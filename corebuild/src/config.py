import os
from dotenv import load_dotenv

load_dotenv()

# Supports the original deployment variable plus the standard OpenAI variable.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_KEY")
CORE_BUILD_SECRET = os.getenv("CORE_BUILD_SECRET") or "corebuild-local-preview-secret"
