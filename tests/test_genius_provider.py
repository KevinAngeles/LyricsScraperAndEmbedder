import pytest
from pathlib import Path
import sys

# Add the parent directory to path to import the module
sys.path.append(str(Path(__file__).parent.parent))
from providers.genius_provider import GeniusProvider

def test_get_track_info_without_lyrics_list_from_album():
    """Test getting track info from a Genius album URL."""
    # Initialize the provider
    provider = GeniusProvider()
    
    # Test with a known album URL
    album_url = "https://genius.com/albums/Backstreet-boys/All-i-have-to-give-ill-never-break-your-heart-remixes"
    
    # Call the method
    tracks = provider.get_track_info_without_lyrics_list_from_album(album_url)
    
    # Basic assertions
    assert isinstance(tracks, list), "Should return a list of TrackInfo objects"
    assert len(tracks) > 0, "Should return at least one track"
    
    # Debug output
    print(f"\nFound {len(tracks)} tracks:")
    for track in tracks:
        print(f"{track.track_number}. {track.title} - {track.artist}")
    assert len(tracks) == 11, "Should return 11 lyrics for this album (there were " + str(len(tracks)) + " found)"

    # Check track info structure
    for idx in range(0, len(tracks)):
        assert hasattr(tracks[idx], 'title'), "Track should have a title"
        assert hasattr(tracks[idx], 'artist'), "Track should have an artist"
        assert tracks[idx].title, "Track title should not be empty"
        assert tracks[idx].artist, "Artist should not be empty"
    
    print("\n Last track info:", tracks[-1].lyrics)