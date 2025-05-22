from typing import Optional

class SummaryAction:
    def __init__(self, content_type: int, content: str, source_key: str):
        self.content_type = content_type
        self.content = content
        self.source_key = source_key

    def __str__(self):
        return f"SummaryAction(action={self.action})"


class SummarySource:
    def __init__(self, key: str, title: str, background: str):
        self.key = key
        self.title = title
        self.background = background

    def __str__(self):
        return f"SummarySource(source={self.source})"


class Summary:
    def __init__(self, title: str, description: str, source: SummarySource, location: str = "N/A", start_date: str = "N/A", end_date: Optional[str] = None):
        self.title = title
        self.description = description
        self.location = location
        self.start_date = start_date
        self.end_date = end_date
        
        self._source = source
        self._extra = {}

    def __str__(self):
        return f"Summary(title={self.title}, description={self.description})"

