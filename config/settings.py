import os
from pytz import timezone

API_KEY = os.getenv("API_KEY")

TIMEZONE = timezone("Canada/Eastern")

SOURCE_URL = "https://example.com/source"

ALLOWED_ORIGINS = ["http://localhost:2233"]

# Processor settings
TEXT_PROCESSOR_API_KEY = os.getenv("TEXT_PROCESSOR_API_KEY")
TEXT_PROCESSOR_MODEL = "gpt-4-turbo"
TEXT_PROCESSOR_MAX_TOKENS = 4096
TEXT_PROCESSOR_TEMPERATURE = 0.3
TEXT_PROCESSOR_LLM_URL = "https://api.openai.com/v1/chat/completions"
