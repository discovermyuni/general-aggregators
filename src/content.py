import logging
from http import HTTPStatus

import aiohttp

from .action import Summary
from .action import SummaryAction
from .action import SummarySource
from .processor import ALL_PROCESSORS
from .processor import Processor
from .settings_store import get_setting

logger = logging.getLogger("aggregator")

SOURCE_URL = get_setting("SOURCE_URL")


async def _obtain_source(source_key: str) -> SummarySource | None:
    try:
        async with aiohttp.ClientSession() as session, session.get(SOURCE_URL) as resp:
            resp.raise_for_status()
            data = await resp.json()
            key = data.get("key")
            title = data.get("title")
            background = data.get("background")
            org_background = data.get("org_background") if "org_background" in data else None
            return SummarySource(key=key, title=title, background=background, org_background=org_background)
    except aiohttp.ClientError:
        logger.exception("Failed to fetch source data")
        return None
    except aiohttp.ContentTypeError:
        logger.exception("Failed to parse JSON from source")
        return None


async def get_event_titles(action: SummaryAction, processors: list[Processor]) -> list[str]:
    current_titles = []

    for processor in processors:
        if not processor.has_relevant_content(action.content):
            continue

        relevant_content = processor.get_relevant_content(action.content)
        titles = await processor.get_titles(relevant_content, current_titles)

        if not titles:
            continue

        current_titles.extend(titles)

    return titles


async def standardize_content(action: SummaryAction) -> list[Summary]:
    source = await _obtain_source(action.source_key)
    summary = Summary(source=source)

    # Add all relevant processors for the various content types
    # (i.e. text, image, etc.)
    processors = [p() for p in ALL_PROCESSORS if p.name in action.content]

    # Count the number of events and their titles (to avoid duplicant summaries between processors)
    titles = await get_event_titles(action, processors)
    count = len(titles)
    if count <= 0:
        logger.info("No possible events found in action.")
        return None
    logger.info("Expecting %d summaries from action.", count)

    # Initialize mostly blank summaries
    summaries = [Summary(title=title, source=source) for title in titles]

    # Keep trying until all the summaries are complete or all processors are exhausted
    for processor in processors:
        if not processor.has_relevant_content(action):
            continue

        matching_content = processor.get_relevant_content(action)
        await processor.resolve(matching_content, summaries)

        if all(s.is_complete() for s in summaries):
            logger.info("All summaries are complete early.")
            break
    else:
        # Take the the ones that are complete (if any)
        complete_summaries = []
        for i, summary in enumerate(summaries):
            if summary.is_complete():
                complete_summaries.append(summary)
            else:
                missing_attributes = summary.get_missing_attributes()
                logger.warning(
                    "Missing attributes in summary %d: %s",
                    i,
                    ", ".join(missing_attributes),
                )

        summaries = complete_summaries

    if not summaries:
        logger.info("No complete summaries found.")
        return None

    logger.info(
        "Found %d complete summaries (of expected %d) from %s action.",
        len(summaries),
        count,
        action.source_key,
    )
    return summaries


async def send_content(action: SummaryAction, summaries: list[Summary], publish_api_key: str, target_url: str):
    async with aiohttp.ClientSession() as session:
        payload = {
            "source_key": action.source_key,
            "summaries": [s.get_as_dict() for s in summaries],
        }

        headers = {
            "Content-Type": "application/json",
            "Header": f"Api-Key {publish_api_key}",
        }

        async with session.post(target_url, json=payload, headers=headers) as resp:
            if resp.status != HTTPStatus.OK:
                logger.error("Failed to send content: %d %s", resp.status, await resp.text())
            else:
                logger.info("Content sent successfully.")
