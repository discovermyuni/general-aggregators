from typing import Optional

class SummaryAction:
    def __init__(self, content: dict[str, any], source_key: str):
        self.content = content
        self.source_key = source_key

    def __str__(self):
        return f"SummaryAction(source_key={self.source_key})"


class SummarySource:
    def __init__(self, key: str, title: str, background: str):
        self.key = key
        self.title = title
        self.background = background

    def __str__(self):
        return f"SummarySource(source={self.source})"


class Summary:
    REQUIRED_ATTRIBUTES = ['title', 'description', 'location', 'start_date']
    
    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[SummarySource] = None,
        location: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        self.title = title
        self.description = description
        self.location = location
        self.start_date = start_date
        self.end_date = end_date

        self.source = source
        self.modifiers = {}
        
    def get_missing_attributes(self):
        return [item for item in Summary.REQUIRED_ATTRIBUTES if getattr(self, item) is None]
    
    def is_complete(self):
        return not self.get_missing_attributes()

    def is_blank(self):
        return self.get_missing_attributes() == Summary.REQUIRED_ATTRIBUTES
    
    def __str__(self):
        return f"Summary(title={self.title}, description={self.description})"

