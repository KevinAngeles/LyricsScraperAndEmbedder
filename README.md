# Lyrics Scraper for Genius and Musixmatch

A Python-based tool to automatically download lyrics from Genius.com or Musixmatch and embed them into your audio files. Available as both a web application and a command-line interface (CLI). This project supports fetching accurate lyrics for entire albums at once from multiple sources.

## Author
- [Kevin Angeles](https://www.kevinangeles.com)

## Features

### Shared Features (Both Web and CLI)
* **Multiple Sources**: Supports both Genius and Musixmatch as lyrics sources
* **Audio File Support**: Works with MP3 and M4A audio formats
* **Lyrics Embedding**: Automatically embeds lyrics into your audio files' metadata
* **Batch Processing**: Process multiple files or entire albums at once

### Web Version (`web_lyrics_embedder.py`)
* **User Friendly Interface**: Simple web interface for easy interaction
* **Visual Feedback**: Real time progress tracking with a graphical interface
* **No Command Line Required**: Perfect for users who prefer a point and click experience
* **Drag & Drop**: Intuitive file upload with drag and drop support
* **Automatic File Management**: Uploaded MP3/M4A files are automatically saved to the media folder where lyrics will be embedded

### CLI Version (`cli_lyrics_embedder.py`)
* **Automation Friendly**: Easily integrate into scripts and automated workflows
* **Lightweight**: Lower resource usage without the web interface overhead
* **Remote Server Ready**: Ideal for headless servers and remote operations
* **Detailed Logging**: Comprehensive console output for debugging and monitoring
* **Direct File Processing**: Processes MP3/M4A files directly from the media folder, embedding lyrics into the original files

## Disclaimer

This tool is for personal use only. Please respect copyright laws and Genius.com's terms of service. The developers are not responsible for any misuse of this software.
