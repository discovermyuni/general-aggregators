from .base import Processor
from ..action import Summary, SummaryAction


class TextProcessor(Processor):
    name = "text"
    
    def __init__(self):
        super().__init__(TextProcessor.name)

    def matches_content(self, action: SummaryAction) -> bool:
        """Check if the processor can handle the content type."""
        return super().matches_content(action) and isinstance(action.content[self.name], str)
    
    async def resolve(self, content: str, summaries: list[Summary]):
        """Process the text."""
        # Check for TOKEN_LIMIT
        # Confirm `text` is a string
        
        # Send request to LLM
        
        # Use Summary static variables to get prompt context for flexibility
        # (i.e. what parameters should be obtained)
        
        # Recieve information and attempt to parse as JSON
        # Add as many keys as possible
        
        # Note that multiple summaries can dervied from one summary action
        expected_summaries = len(summaries)
        for i in range(expected_summaries):
            summaries[i].title = f"Title {i}"
            summaries[i].description = f"Description {i}"
            summaries[i].location = f"Location {i}"
            summaries[i].start_date = f"Start Date {i}"
        
