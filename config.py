import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
MODEL = os.getenv("MODEL", "claude-sonnet-4-6")
MAX_TEXT_CHARS = int(os.getenv("MAX_TEXT_CHARS", "40000"))
