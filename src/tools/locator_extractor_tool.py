import os
import re
import urllib3
import requests
from html.parser import HTMLParser
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool

# Suppress insecure HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SimpleDOMParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = []
        self.buttons = []
        self.links = []
        self.headings = []
        self.current_tag = None
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        self.current_tag = tag
        self.current_text = []

        if tag == "input":
            info = {
                "name": attr_dict.get("name"),
                "id": attr_dict.get("id"),
                "placeholder": attr_dict.get("placeholder"),
                "type": attr_dict.get("type", "text"),
                "aria_label": attr_dict.get("aria-label")
            }
            if any(info.values()):
                self.inputs.append(info)

        elif tag == "button":
            self.buttons.append({
                "type": attr_dict.get("type", "button"),
                "id": attr_dict.get("id"),
                "class": attr_dict.get("class"),
                "title": attr_dict.get("title")
            })

        elif tag == "a" and "href" in attr_dict:
            self.links.append({
                "href": attr_dict.get("href"),
                "title": attr_dict.get("title")
            })

    def handle_data(self, data):
        if self.current_tag in ["button", "h1", "h2", "h3", "h4", "h5", "h6", "p", "a"]:
            cleaned = data.strip()
            if cleaned:
                self.current_text.append(cleaned)

    def handle_endtag(self, tag):
        text = " ".join(self.current_text).strip()
        if tag == "button" and self.buttons:
            self.buttons[-1]["text"] = text
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"] and text:
            self.headings.append({"level": tag, "text": text})
        self.current_tag = None
        self.current_text = []


def extract_locators_from_kb(query: str = "OrangeHRM") -> str:
    """Fetches verified locators from the knowledge base directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    kb_path = os.path.join(base_dir, "src", "knowledge_base", "orangehrm-login-dashboard-playwright-locators.txt")
    if os.path.exists(kb_path):
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading KB locators: {e}"
    return "No verified locators found in KB."


def extract_locators_from_live_url(url: str) -> str:
    """Attempts to inspect a live application URL to extract latest DOM locators."""
    if not url.startswith("http://") and not url.startswith("https://"):
        return ""

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=8)
        if response.status_code == 200:
            parser = SimpleDOMParser()
            parser.feed(response.text)

            locators_found = []
            if parser.inputs:
                locators_found.append("Inputs found:")
                for inp in parser.inputs[:10]:
                    locators_found.append(f"  - {inp}")
            if parser.buttons:
                locators_found.append("Buttons found:")
                for btn in parser.buttons[:10]:
                    locators_found.append(f"  - {btn}")
            if parser.headings:
                locators_found.append("Headings found:")
                for h in parser.headings[:10]:
                    locators_found.append(f"  - {h}")

            return "\n".join(locators_found) if locators_found else "No interactive elements found in initial HTML."
    except Exception as e:
        return f"Live DOM extraction skipped ({e})"
    return ""


@tool("get_application_locators")
def get_application_locators_tool(query_or_url: str) -> str:
    """Retrieves verified and latest locators for the target application from the Knowledge Base and Live Application DOM.

    Args:
        query_or_url: URL or application domain name (e.g., 'https://opensource-demo.orangehrmlive.com/web/index.php/auth/login' or 'OrangeHRM').
    """
    kb_locators = extract_locators_from_kb(query_or_url)
    
    url_match = re.search(r"https?://[^\s]+", query_or_url)
    live_locators = ""
    if url_match:
        live_locators = extract_locators_from_live_url(url_match.group(0))

    result = f"=== VERIFIED KNOWLEDGE BASE LOCATORS ===\n{kb_locators}\n"
    if live_locators:
        result += f"\n=== LIVE DOM EXTRACTED LOCATORS ===\n{live_locators}\n"
    return result
