import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPEN_AI_KEY")
CORE_BUILD_SECRET=os.getenv("CORE_BUILD_SECRET")