from .action import SummaryAction, Summary, SummarySource

# example settings url
TARGET_URL = "http://localhost:8000/api/fetch_source"

def get_target_url(source_key: str) -> str:
    return f"{TARGET_URL}?s={source_key}"


async def _obtain_source(source_key: str) -> SummarySource:
    # simulate fetching source data from main thing
    return SummarySource(key=source_key, title="Sample Title", background="Sample Background")


async def standardize_content(action: SummaryAction):
    source = _obtain_source(action.source_key)
    
    # add TextProcessor AND THEN OR 
    # ImageProcessor
    summary = Summary(
        title=action.content,
        description="Sample Description",
        source=source,
        location="Sample Location",
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    
    # add TagsPostModifier
    summary._extra["tags"] = ["tag1", "tag2"]
    
    return summary


async def send_content(summary: Summary, target_url: str):
    pass
