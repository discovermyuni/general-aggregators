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
    OPTIONAL_ATTRIBUTES = ['end_date']
    
    def __init__(
        self,
        title: str = "",
        description: str = "",
        source: SummarySource = None,
        location: str = "",
        start_date: str = "",
        end_date: str = ""
    ):
        self.title = title
        self.description = description
        self.location = location
        self.start_date = start_date
        self.end_date = end_date

        self.source = source
        self.modifiers = {}
        
    def as_dict(self):
        d = {}
        for attr in Summary.REQUIRED_ATTRIBUTES + Summary.OPTIONAL_ATTRIBUTES:
            value = getattr(self, attr, "")
            d[attr] = value
        return d
    
    def get_missing_attributes(self):
        return [item for item in Summary.REQUIRED_ATTRIBUTES if getattr(self, item) in (None, "")]
    
    def is_complete(self):
        return not self.get_missing_attributes()

    def is_blank(self):
        return self.get_missing_attributes() == Summary.REQUIRED_ATTRIBUTES
    
    def __str__(self):
        return f"Summary(title={self.title}, description={self.description})"

