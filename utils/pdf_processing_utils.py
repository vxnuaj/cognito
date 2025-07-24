import requests
from pypdf import PdfReader
import os

def download_pdf(url: str, destination_path: str):
    """
    Downloads a PDF from a given URL to a specified destination path.
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an exception for bad status codes
    with open(destination_path, 'wb') as pdf_file:
        for chunk in response.iter_content(chunk_size=8192):
            pdf_file.write(chunk)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a PDF file using pypdf.
    """
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    return text
