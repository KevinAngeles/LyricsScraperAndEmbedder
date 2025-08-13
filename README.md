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

## Prerequisites

- Python 3.6 or higher
- Required Python packages (install via `pip install -r requirements.txt`):
  - requests
  - beautifulsoup4
  - mutagen
  - lxml
  - Flask (for web version)
  - Werkzeug (required by Flask)

## Installation

1. Clone this repository or download the scripts to your local machine
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Directory Structure

```
LyricsScraperAndEmbedder/
├── media/                    # Directory for MP3/M4A files (created on first run)
├── providers/                # Lyrics provider implementations
├── static/                   # Web application static files (CSS, JS)
├── templates/                # Web application HTML templates
├── cli_lyrics_embedder.py    # Command-line interface version
├── lyrics_embedder.py        # Core lyrics embedding functionality
├── utilities.py              # Shared utility functions
├── web_lyrics_embedder.py    # Web application version
└── requirements.txt          # Python dependencies
```

## Usage

### Web Version
1. **Start the web server**:
   ```bash
   python web_lyrics_embedder.py
   ```
2. **Open your browser** to `http://localhost:5000`
3. **Enter the Genius album URL** and click "Process"
4. **Monitor progress** directly in your browser

### CLI Version
1. **Prepare Your Audio Files**:
   - Place your MP3 or M4A files in the `media` folder
   - Ensure audio files have track numbers in their metadata that match the track numbers on Genius for proper matching.
   - Files with missing track numbers or track numbers different from the Genius track listing won't be processed.

2. **Run the CLI Tool**:
   ```bash
   python cli_lyrics_embedder.py [genius_album_url]
   ```
   
   Example:
   ```bash
   python cli_lyrics_embedder.py "https://genius.com/albums/Various-artists/Fast-five-original-motion-picture-soundtrack"
   ```

3. **Follow Prompts**:
   - If no URL is provided, you'll be prompted to enter one
   - The script will guide you through the process

4. **iTunes Sync (Optional)**:
   - Open the properties of each audio file in iTunes
   - Save and close the properties of each audio file in iTunes for the lyrics to be allowed to be synchronized to Apple devices
   - If you skip this step, the lyrics will be embedded but may not sync to Apple devices

## How It Works

### Both Versions:
1. **Lyrics Download**:
   - The application can use either Genius or Musixmatch as the lyrics source
   - For Genius: Scrapes the provided album URL to get track listings and lyrics
   - For Musixmatch: Searches and matches tracks using the Musixmatch API

2. **Lyrics Embedding**:
   - The application processes each audio file in the `media` folder
   - It matches the audio files with the downloaded lyrics using track numbers from the files' metadata
   - Lyrics are embedded into the audio files' metadata (ID3 tags for MP3, iTunes tags for M4A)

### Web Version Specifics:
- Uses Flask to serve a simple web interface
- Provides real-time progress updates via web sockets
- Displays a clean, responsive interface for managing the process

### CLI Version Specifics:
- Designed for automation and scripting
- Shows progress bars in the terminal
- Ideal for batch processing and integration with other tools

## Notes

- **Supported Audio Formats**: MP3 (.mp3) and M4A (.m4a)
- **Important**: For best results, ensure your audio files have proper metadata (track numbers, titles) that match the source platform
- **Source-Specific Notes**:
  - **Genius**: Requires album URLs from genius.com for batch processing
  - **Musixmatch**: Works with individual tracks or albums using search functionality
- **Troubleshooting**:
  - If lyrics aren't being found, verify your audio files have correct metadata (track numbers, titles)
  - Check if the track/album names in your files match those on the source platform
  - Ensure you have write permissions for the audio files
  - Some M4A files might have restricted write permissions. Check file properties if embedding fails

## Disclaimer

This tool is for personal use only. Please respect copyright laws and Genius.com's terms of service. The developers are not responsible for any misuse of this software.
