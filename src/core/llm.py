import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# Support both GEMINI_API_KEY and GOOGLE_API_KEY
gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Optional proxy bypass for enterprise networks
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

llm = ChatGoogleGenerativeAI(
    model=model_name,
    google_api_key=gemini_api_key,
    temperature=0
)
 