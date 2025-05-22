from ..action import SummaryAction, Summary

class Processor:
    def __init__(self, name: str):
        self.name = name

    def process(self, action: SummaryAction) -> Summary:
        raise NotImplementedError