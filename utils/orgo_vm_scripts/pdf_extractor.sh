#!/bin/bash

# This script is a placeholder for execution within an Orgo VM.
# It assumes pdftotext is installed and available.

PDF_PATH=$1

if [ -z "$PDF_PATH" ]; then
    echo "Usage: $0 <path_to_pdf>"
    exit 1
fi

if [ ! -f "$PDF_PATH" ]; then
    echo "Error: PDF file not found at $PDF_PATH"
    exit 1
fi

pdftotext "$PDF_PATH" -
