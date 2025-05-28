import json
import logging
from datetime import datetime

import aiohttp

from src.action import Summary
from src.action import SummaryAction
from src.settings_store import get_setting
from src.settings_store import get_setting_or_default

from .base import Processor

logger = logging.getLogger("aggregator")
logging.basicConfig(level=logging.INFO)

TIMEZONE = get_setting("TIMEZONE")
TEXT_PROCESSOR_MODEL = get_setting_or_default("TEXT_PROCESSOR_MODEL", "gpt-4o-mini")
TEXT_PROCESSOR_MAX_TOKENS = get_setting_or_default("TEXT_PROCESSOR_MAX_TOKENS", 4096)
TEXT_PROCESSOR_TEMPERATURE = get_setting_or_default("TEXT_PROCESSOR_TEMPERATURE", 0.0)
TEXT_PROCESSOR_LLM_URL = get_setting_or_default("TEXT_PROCESSOR_LLM_URL", "https://api.openai.com/v1/chat/completions")
TEXT_PROCESSOR_API_KEY = get_setting("TEXT_PROCESSOR_API_KEY")


class TextProcessor(Processor):
    name = "text"

    def __init__(self):
        super().__init__(TextProcessor.name)

    def _create_payload(self, prompt: str):
        """Create the payload for the LLM request."""
        return {
            "messages": [{"role": "system", "content": prompt}],
            "model": TEXT_PROCESSOR_MODEL,
            "max_tokens": TEXT_PROCESSOR_MAX_TOKENS,
            "temperature": TEXT_PROCESSOR_TEMPERATURE,
        }


    async def _query_llm_for_json(self, payload: dict) -> str | None:
        """Query the LLM with the given payload."""
        headers = {"Authorization": f"Bearer {TEXT_PROCESSOR_API_KEY}", "Content-Type": "application/json"}
        try:
            async with aiohttp.ClientSession() as session, session.post(
                TEXT_PROCESSOR_LLM_URL, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                response.raise_for_status()
                response_json = await response.json()
                completion = response_json["choices"][0]["message"]["content"].strip()
                return json.loads(completion.strip())

        except aiohttp.ClientError as e:
            logger.exception("Error fetching data from LLM", exc_info=e)
        except KeyError as e:
            logger.exception("Error in API response", exc_info=e)
        except json.JSONDecodeError as e:
            logger.exception("Error parsing JSON response", exc_info=e)
        return None


    async def get_titles(
        self, content: str, previous_titles: list[str] | None = None,
    ) -> list[str]:
        if previous_titles is None:
            previous_titles = []
        recognition_text = (
            "Some events have already been recognized, so do not count them again. "
            "Here are the previously recognized events by title: "
            f"{chr(10).join(['- ' + t for t in previous_titles])}."
            "\nRemember to only count the new events in the text below."
        )

        prompt = (
            "Count the number of events in the text below. ONLY return the number of recognized "
            "events as a number (i.e. 0, 1, 6).\n"
            "Do not add any other text or explanation.\n"
            f"{recognition_text if previous_titles else ''}\n\n"
            "Text to count events in:\n"
            f"{content}\n"
        )
        logger.info("COUNT PROMPT: %s", prompt)
        payload = self._create_payload(prompt)
        return await self._query_llm_for_json(payload)


    def _create_prompt(self, content: str, summaries: list[Summary]) -> str:
        """Create the prompt for the LLM request."""

        return (
            f"Extract event details into JSON objects from text at the bottom and fill in the missing fields "
            f"for each event. Return it in a JSON array."
            "You have been given the titles of the events in the text, fill in the "
            "details for each event based on the text below.\n\n"
            "All dates should be in the format YYYY-MM-DD hh:mm (24-hour format like 2025-02-28 13:00). "
            'If relative time is given (e.g., "tomorrow", "next week"),\n'
            f"convert it to an absolute date based on today's date, which is "
            f"{datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M')}. "
            "Keep descriptions concise but cover all important details.\n\n"
            'Locations can be given as rooms, buildings or addresses, but should be standardized to a single '
            'location string (e.g., "Room MN2710", "ABC", "Campus", "5838 George Dr").\n\n'
            'Remove any requests to "message me", "reply to this email" or "click here" in the text.\n\n'
            "Each event is listed here, fill in the missing fields to the best of your ability if they are blank. "
            "You may add detail to non-blank fields, but nothing else.\n"
            'If you use double quotes in the text, escape them with a backslash (e.g., \\"text\\"). '
            "If you use newlines, use \\\\n, JSON-style.\n\n"
            "ONLY return the JSON object with the event details. Do not add any other text or explanation.\n\n"
            f"The keys are: {', '.join(Summary.REQUIRED_ATTRIBUTES)}, "
            f"{', '.join([s + ' (optional)' for s in Summary.OPTIONAL_ATTRIBUTES])}.\n"
            f"{json.dumps([summary.as_dict() for summary in summaries], indent=2)}\n\n"
            f"Text to parse:\n{content}\n"
        )


    def matches_content(self, action: SummaryAction) -> bool:
        """Check if the processor can handle the content type."""
        return super().matches_content(action) and isinstance(action.content[self.name], str)


    async def resolve(self, content: str, summaries: list[Summary]) -> bool:
        """Process the text."""
        # TODO: Check for TOKEN_LIMIT + prompt length
        # TODO: make use of source background info
        prompt = self._create_prompt(content, summaries)
        logger.info("PROMPT: %s", prompt)
        payload = self._create_payload(prompt)
        data = await self._query_llm_for_json(payload)

        for i, obj in enumerate(data):
            if i >= len(summaries):
                logger.error(
                    "Invalid number of objects in response than summaries (expected %i): %s",
                    len(summaries),
                    obj,
                )
                break

            summary = summaries[i]

            summary.title = obj.get("title")
            summary.description = obj.get("description")
            summary.location = obj.get("location")
            summary.start_date = obj.get("start_date")
            if obj.get("end_date") not in (None, ""):
                summary.end_date = obj.get("end_date")

        return True
