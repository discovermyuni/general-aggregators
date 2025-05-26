from src.action import Summary
from src.action import SummaryAction


class Processor:
    def __init__(self, name: str):
        self.name = name

    def get_titles(self, content: any, previous_titles: list[str] | None = None) -> list[str]:
        raise NotImplementedError

    def has_relevant_content(self, action: SummaryAction) -> bool:
        """Check if the processor can handle the content type."""
        return self.name in action.content

    def get_relevant_content(self, action: SummaryAction) -> bool:
        return action.content[self.name]

    async def resolve(self, content: any, summaries: list[Summary]) -> bool:
        raise NotImplementedError
