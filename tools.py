from pathlib import Path
from random import random
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from ddgs import DDGS
from pypdf import PdfReader
import os

@tool
def internet_search(query, max_results=3):
    """
    Perform an internet search using DuckDuckGo and return the top results.
    Args:   
        query (str): The search query.
        max_results (int): The maximum number of results to return.
    Returns:
        list: A list of search results.
    """
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(query, max_results=max_results)]
        
    return results


@tool
def fetch_website_content(url: str) -> str:
    """
    Visits a specific URL link and extracts all the main text content from the webpage.
    Args:
        url (str): The exact URL of the website to read.
    Returns:
        str: The plain text content of the website.
    """
    try:
        # Send a request with a standard browser User-Agent header to avoid blocks
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")
        
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator="\n")
        
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase for line in lines for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)
        
        return clean_text[:5000] 
        
    except Exception as e:
        return f"Error fetching content from {url}: {str(e)}"
    

@tool
def hash_str(text: str) -> str:
    """
    Generates a simple hash for the given text.
    Args:
        text (str): The input text to hash.
    Returns:
        int: The hashed text.
    """
    return hash(text)


FULL_PATH = Path(__file__).resolve().parent / "virtualFileSystem"

@tool
def extract_exact_pages(pdf_path, start_page, end_page):
    """
    Extracts text from a PDF file for the specified range of pages.
    """
    # Force the path to strip any leading slashes/backslashes so it chains properly
    clean_pdf_path = str(pdf_path).lstrip("\\/")
    target_pdf = (FULL_PATH / clean_pdf_path).resolve()
    
    # Safety Check: Prevent the AI from escaping the virtual file system
    if not str(target_pdf).startswith(str(FULL_PATH)):
        return "Error: Security violation. Access restricted to the virtual workspace."

    if not target_pdf.exists():
        return f"Error: The file could not be found at path: {pdf_path}"
        
    reader = PdfReader(target_pdf)
    extracted_text = ""
    
    # Handle bounds safety so the agent doesn't crash the script on bad guesses
    total_pages = len(reader.pages)
    safe_start = max(1, min(start_page, total_pages))
    safe_end = max(safe_start, min(end_page, total_pages))
    
    for page_num in range(safe_start - 1, safe_end):
        extracted_text += f"--- PAGE {page_num + 1} ---\n"
        extracted_text += reader.pages[page_num].extract_text()
        
    return extracted_text
