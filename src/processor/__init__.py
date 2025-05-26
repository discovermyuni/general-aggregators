from .base import Processor
from .text import TextProcessor

__all__ = ["Processor", "TextProcessor"]
ALL_PROCESSORS = [TextProcessor]