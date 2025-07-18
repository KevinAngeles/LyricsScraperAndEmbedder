from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TrackInfo:
    """Container for track information."""
    title: str
    artist: str
    track_number: Optional[int] = None
    url: Optional[str] = None
    lyrics: Optional[str] = None

class LyricsProvider(ABC):
    """Base class for all lyrics providers."""
    
    @classmethod
    @abstractmethod
    def can_handle(cls, url: str) -> bool:
        """Check if this provider can handle the given URL."""
        pass
    
    @abstractmethod
    def get_lyrics(self, track_url: str) -> Optional[str]:
        """Extract lyrics from a track URL."""
        pass
    
    @abstractmethod
    def get_track_info_without_lyrics_list_from_album(self, album_url: str) -> List[TrackInfo]:
        """Get every track information without lyrics from an album URL."""
        pass
    
    @abstractmethod
    def get_track_info(self, track_url: str, track_number: int) -> Optional[TrackInfo]:
        """Get track information with lyrics from a track URL."""
        pass
