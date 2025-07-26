#!/usr/bin/env python3
"""Test script for centralized thoughts logging."""

import time
import sys
import os

# Add the parent directory to the path so we can import from utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cognito_thoughts import CognitoThoughts

def test_centralized_logging():
    """Test that multiple agents log to the same centralized file."""
    
    # Create multiple agent loggers
    extractor = CognitoThoughts("ExtractorAgent")
    analyst1 = CognitoThoughts("AnalystAgent[Skeptic]")
    analyst2 = CognitoThoughts("AnalystAgent[Proponent]")
    orchestrator = CognitoThoughts("Orchestrator")
    
    print(f"Logging to centralized file: {CognitoThoughts.get_thoughts_file()}")
    print("-" * 50)
    
    # Simulate agent thoughts
    orchestrator.step("Research Pipeline", "Starting paper analysis")
    time.sleep(0.1)
    
    extractor.step("PDF Extraction", "Processing paper.pdf")
    extractor.analyze("Found 10 pages with 5 figures")
    time.sleep(0.1)
    
    analyst1.think("This methodology seems questionable")
    analyst1.decide("Challenge assumptions", "Statistical significance is weak")
    time.sleep(0.1)
    
    analyst2.think("Promising results for real-world applications")
    analyst2.insight("Could revolutionize the field if scaled properly")
    time.sleep(0.1)
    
    extractor.success("Extraction complete: 5000 words")
    analyst1.question("Are the control variables properly isolated?")
    analyst2.success("Identified 3 key innovations")
    
    orchestrator.progress(2, 5, "Papers analyzed")
    orchestrator.error("API rate limit hit", "Will retry in 5 seconds")
    
    print("-" * 50)
    print("Test complete! Check the centralized log file.")
    print(f"File: {CognitoThoughts.get_thoughts_file()}")

if __name__ == "__main__":
    test_centralized_logging()
