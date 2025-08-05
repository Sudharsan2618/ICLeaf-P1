# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

# Google Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash"

# GitHub API Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# YouTube API Configuration
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Search Configuration
MAX_SEARCH_RESULTS = 5
MAX_CONTEXT_LENGTH = 4000 