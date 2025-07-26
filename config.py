# TODO - implement proper configurations here. 

import os
from dotenv import load_dotenv

load_dotenv()

# Default values for the application
DEFAULT_NUM_PAPERS = int(os.getenv("DEFAULT_NUM_PAPERS", "1"))
DEFAULT_NUM_VMS = int(os.getenv("DEFAULT_NUM_VMS", "1"))

# ArXiv API settings (if needed, though arxiv library handles most)
ARXIV_API_URL = "http://export.arxiv.org/api/query?"

# Paths
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
TEMP_DIR = os.getenv("TEMP_DIR", "temp")
PDF_DIR = os.getenv("PDF_DIR", "pdfs")
LOG_DIR = os.getenv("LOG_DIR", "logs")

# Orgo and LLM API keys
ORGO_API_KEY = os.getenv("ORGO_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # For Agent S2 if needed

# Available Claude models
CLAUDE_MODELS = { # TODO - extract proper models here.
    "claude-3-5-sonnet-latest": "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-latest": "claude-3-5-haiku-20241022",
    "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku": "claude-3-5-haiku-20241022",
    "claude-3-opus": "claude-3-opus-20240229",
    "claude-3-sonnet": "claude-3-sonnet-20240229",
    "claude-3-haiku": "claude-3-haiku-20240307"
}

# LLM settings for summarization
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "claude-3-5-haiku-20241022")

# If user specified a model alias, convert it to the full model name
if LLM_MODEL_NAME in CLAUDE_MODELS:
    LLM_MODEL_NAME = CLAUDE_MODELS[LLM_MODEL_NAME]

# LLM temperature setting
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))

# Retry settings
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "2.0"))
RETRY_BACKOFF_FACTOR = float(os.getenv("RETRY_BACKOFF_FACTOR", "2.0"))
