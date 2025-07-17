from mutagen.mp3 import MP3 as MP3Tags
from mutagen.mp4 import MP4 as MP4Tags
from pathlib import Path

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

def ensure_lyrics_dir() -> Path:
    """Ensure the lyrics directory exists and return its path."""
    lyrics_dir = Path("lyrics")
    lyrics_dir.mkdir(exist_ok=True)
    return lyrics_dir