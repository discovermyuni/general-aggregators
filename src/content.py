from typing import Optional
from .action import SummaryAction, Summary, SummarySource

from .processor.text import TextProcessor
# from .processor.image import ImageProcessor

# example settings file url
TARGET_URL = "http://localhost:8000/api/fetch_source"
ALL_PROCESSORS = [TextProcessor]

def get_target_url(source_key: str) -> str:
    return f"{TARGET_URL}?s={source_key}"


async def _obtain_source(source_key: str) -> SummarySource:
    # simulate fetching source data from main thing
    return SummarySource(key=source_key, title="Sample Title", background="Sample Background")


async def count_events(action: SummaryAction, source: SummarySource, target_url: str) -> int:
    # simulate the counting (needs to be done via LLM, possibly a lighter variant)
    return 1


async def standardize_content(action: SummaryAction) -> Optional[Summary]:
    source = await _obtain_source(action.source_key)
    summary = Summary(source=source)
    
    # Count the number of events (to simplify the token-intensive processing)
    count = await count_events(action, source, get_target_url(source.key))
    if count <= 0:
        print("No possible events found in action.")
        return None
    print(f"Expecting {count} summaries from action.")
    
    # Add all relevant processors for the various content types
    # (i.e. text, image, etc.)
    processors = []
    for p in ALL_PROCESSORS:
        if p.name in action.content:
            processors.append(p())

    # Initialize blank summaries (to carry over and re-assign less)
    summaries = [Summary(source=source) for _ in range(count)]
    
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


async def send_content(summary: Summary, target_url: str):
    pass
