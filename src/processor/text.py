import json
import logging
from datetime import datetime
import aiohttp
from pytz import timezone

from .base import Processor
from ..action import Summary, SummaryAction


logger = logging.getLogger("text_processor")

TIMEZONE = timezone("Canada/Eastern")
TEXT_PROCESSOR_MODEL = "gpt-4-turbo"
TEXT_PROCESSOR_MAX_TOKENS = 500
TEXT_PROCESSOR_TEMPERATURE = 0.0
TEXT_PROCESSOR_API_KEY = "jarjarbinks"
TEXT_PROCESSOR_LLM_URL = "https://api.openai.com/v1/chat/completions"

class TextProcessor(Processor):
    name = "text"
    
    def __init__(self):
        super().__init__(TextProcessor.name)
        
    def _create_payload(self, prompt: str):
        """Create the payload for the LLM request."""
        return {
            "model": TEXT_PROCESSOR_MODEL,
            "messages": [{"role": "system", "content": prompt}],
            "max_tokens": TEXT_PROCESSOR_MAX_TOKENS,
            "temperature": TEXT_PROCESSOR_TEMPERATURE,
        }
        
    def _create_prompt(self, summaries: list[Summary]) -> str:
        # TODO: Use Summary static variables to get prompt context for flexibility
        # (i.e. what parameters should be obtained)
        """Create the prompt for the LLM request."""
        
        prompt = f"""Extract event details from the following text and output strictly in the specified JSON format:

            Text: ''

            Output format:
            [
                {{
                    "title": "<str, Club name: Title of the event maximum of 20 words>",
                    "description": "<str, description of the event maximum of 200 words>",
                    "location": "<str, room of the event in the format buildingroom_number e.g. MN2010>",
                    "date": "<str, date of the event in the format 'YYYY-MM-DD'>",
                    "time": "<str, time of the event in the format 'hh:mm - hh:mm'>"
                }},
                // if there is more than one event
                {{
                    "title": "<str, Club name: Title of the event maximum of 20 words>",
                    "description": "<str, description of the event maximum of 200 words>",
                    "location": "<str, room of the event in the format buildingroom_number e.g. MN2010>",
                    "date": "<str,  date of the event in the format 'YYYY-MM-DD'>",
                    "time": "<str, time of the event in the format 'hh:mm - hh:mm'>"
                }},
                // and so on....
            ]

            There are {len(summaries)} events in the text. Recognize the events and output them in the specified format.
            
            For anything in relative time, today's date is {datetime.now(TIMEZONE).strftime("%d %b")}"""

        return prompt


    def matches_content(self, action: SummaryAction) -> bool:
        """Check if the processor can handle the content type."""
        return super().matches_content(action) and isinstance(action.content[self.name], str)
    
    async def resolve(self, content: str, summaries: list[Summary]) -> bool:
        """Process the text."""
        # TODO: Check for TOKEN_LIMIT + prompt length

        headers = {"Authorization": f"Bearer {TEXT_PROCESSOR_API_KEY}", "Content-Type": "application/json"}

        payload = self._create_payload(self._create_prompt(summaries))

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(TEXT_PROCESSOR_LLM_URL, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    response.raise_for_status()
                    response_json = await response.json()
                    completion = response_json["choices"][0]["message"]["content"].strip()
                    data = json.loads(completion.strip())
                    print("Response from LLM:", data)
                    
        except aiohttp.ClientError as e:
            logger.exception("Error fetching data from LLM", exc_info=e)
            return False
        except KeyError as e:
            logger.exception("Error in API response", exc_info=e)
            return False
        except json.JSONDecodeError as e:
            logger.exception("Error parsing JSON response", exc_info=e)
            return False
        
        
        # Note that multiple summaries can dervied from one summary action
        expected_summaries = len(summaries)
        for i in range(expected_summaries):
            summaries[i].title = f"Title {i}"
            summaries[i].description = f"Description {i}"
            summaries[i].location = f"Location {i}"
            summaries[i].start_date = f"Start Date {i}"
        
