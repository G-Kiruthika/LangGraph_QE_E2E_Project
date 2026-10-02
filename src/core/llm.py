import os
import httpx
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")

custom_http_client = httpx.Client(
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    verify=False  # Disable SSL verification (not recommended for production)
)

os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

llm = ChatGroq(model="openai/gpt-oss-120b", groq_api_key=groq_api_key, http_client=custom_http_client) 