import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Model configuration
MODEL_NAME = "gpt-4o"
TEMPERATURE = 0.1  # Low temperature for consistent extraction
MAX_TOKENS = 1000

# SEC.gov request configuration
SEC_HEADERS = {
    'User-Agent': 'Telecom Data Extractor (contact@yourcompany.com)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}
