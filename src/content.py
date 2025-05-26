from .action import SummaryAction, Summary, SummarySource

from .processor import Processor
from .processor.text import TextProcessor
import aiohttp
from .settings_store import get_setting


SOURCE_URL = get_setting("SOURCE_URL")

ALL_PROCESSORS = [TextProcessor]


async def _obtain_source(source_key: str) -> SummarySource:
    # TODO: implement this AND organization contextual data (like this is a university, etc.)
    return SummarySource(key=source_key, title="Sample Title", background="Sample Background")


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
    processors = []
    for p in ALL_PROCESSORS:
        if p.name in action.content:
            processors.append(p())

    # Count the number of events and their titles (to avoid duplicant summaries between processors)
    titles = await get_event_titles(action, processors)
    count = len(titles)
    if count <= 0:
        print("No possible events found in action.")
        return None
    print(f"Expecting {count} summaries from action.")
    

    # Initialize mostly blank summaries
    summaries = [Summary(title=title, source=source) for title in titles]
    
    # Keep trying until all the summaries are complete or all processors are exhausted
    for processor in processors:
        if not processor.has_relevant_content(action):
            continue
        
        matching_content = processor.get_relevant_content(action)
        await processor.resolve(matching_content, summaries)
    
        if all([s.is_complete() for s in summaries]):
            print("All summaries are complete early.")
            break
    else:
        # Take the the ones that are complete (if any)
        complete_summaries = []
        for i, summary in enumerate(summaries):
            if summary.is_complete():
                complete_summaries.append(summary)
            else:
                missing_attributes = summary.get_missing_attributes()
                print(f"Missing attributes in summary {i}: {', '.join(missing_attributes)}")
        
        summaries = complete_summaries
    
    if not summaries:
        print("No complete summaries found.")
        return None
    
    print(f"Found {len(summaries)} complete summaries (of expected {count}) from {action.source_key} action.")
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
            if resp.status != 200:
                print(f"Failed to send content: {resp.status} {await resp.text()}")
            else:
                print("Content sent successfully.")
