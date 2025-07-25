from mutagen.mp3 import MP3 as MP3Tags
from mutagen.mp4 import MP4 as MP4Tags
from pathlib import Path
import os
from providers.factory import ProviderFactory
from providers.base_provider import LyricsProvider
from typing import Optional

def get_track_number(file_path):
    """Extract track number from audio file metadata.
    
    Args:
        file_path (str): Path to the audio file
        
    Returns:
        int or None: Track number if found, None otherwise
    """
    try:
        if file_path.lower().endswith('.mp3'):
            audio = MP3Tags(file_path)
            if 'TRCK' in audio.tags:
                # TRCK can be a string like '1/12' or just '1'
                track = str(audio.tags['TRCK'][0]).split('/')[0]
                if track.isdigit():
                    return int(track)
        elif file_path.lower().endswith('.m4a'):
            audio = MP4Tags(file_path)
            if 'trkn' in audio.tags:
                # MP4 track number is stored as [(track_number, total_tracks)]
                track_data = audio.tags['trkn'][0]
                if track_data and track_data[0] > 0:
                    return track_data[0]
        return None
    except Exception as e:
        print(f"Error reading track number from {file_path}: {e}")
        return None

def ensure_media_directory() -> Path:
    """Ensure media directory exists and return its path."""
    current_dir = os.getcwd()
    media_dir = os.path.join(current_dir, 'media')
    # Create directories if they don't exist
    os.makedirs(media_dir, exist_ok=True)
    return media_dir

def get_provider_from_url(url: str) -> Optional[LyricsProvider]:
    """Get the appropriate provider for the given URL."""
    provider = ProviderFactory.get_provider_for_url(url)
    if not provider:
        print(f"\nError: No supported provider found for URL: {url}")
        print("Supported domains:")
        for name, provider_class in ProviderFactory._providers.items():
            if hasattr(provider_class, 'DOMAINS'):
                print(f"- {name}: {', '.join(provider_class.DOMAINS)}")
        return None
    return provider
