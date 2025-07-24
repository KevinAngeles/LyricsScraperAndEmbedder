#!/usr/bin/env python3
from mutagen.id3 import ID3, USLT
from mutagen.mp4 import MP4

def add_lyrics_to_audio(audio_path, lyrics_text, language='eng'):
    """Add lyrics to an audio file"""
    try:
        if audio_path.lower().endswith('.mp3'):
            # For MP3 files
            audio = ID3(audio_path)
            # Remove existing lyrics if any
            for tag in list(audio.keys()):
                if tag.startswith('USLT'):
                    del audio[tag]
            # Add new lyrics
            audio.add(USLT(encoding=3, lang=language, desc='', text=lyrics_text))
            audio.save()
            return True
            
        elif audio_path.lower().endswith('.m4a'):
            # For M4A files
            audio = MP4(audio_path)
            # Add lyrics as a new metadata field
            audio['\xa9lyr'] = lyrics_text
            audio.save()
            return True
            
    except Exception as e:
        print(f"Error adding lyrics to {audio_path}: {e}")
    return False
