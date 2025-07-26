#!/usr/bin/env python3
"""
Lyrics Workflow Script

This script automates the complete workflow of:
1. Downloading lyrics from supported providers (Genius, Musixmatch)
2. Adding the downloaded lyrics to corresponding audio files

Usage:
    python3 lyrics_workflow.py [lyrics_url]

If no URL is provided, the user will be prompted to enter one.
"""

import sys
from pathlib import Path
from providers.factory import ProviderFactory
from utilities import ensure_media_directory, get_provider_from_url

def main():
    # Ensure directories exist and get their paths
    media_dir = ensure_media_directory()
    
    print(f"\nMedia directory: {media_dir}\n")
    
    # Get URL from command line or prompt
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("\nEnter lyrics URL (Genius or Musixmatch): ")
    
    # Get the appropriate provider
    provider = get_provider_from_url(url)
    if not provider:
        return
    
    print(f"\nUsing provider: {provider.__class__.__name__}")

if __name__ == "__main__":
    main()
