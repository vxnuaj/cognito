from dataclasses import dataclass
from typing import List

@dataclass
class ExtractedContent:
    raw_text: str
    image_data: List[str]  # List of base64 encoded image strings

@dataclass
class Summary:
    tldr: str
    key_contributions: str
    novelty: str
    limitations_criticisms: str
    explain_like_im_5: str