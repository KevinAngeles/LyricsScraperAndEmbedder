import re
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from urllib.parse import urljoin
from .base_provider import LyricsProvider, TrackInfo
from lxml import etree

class GeniusProvider(LyricsProvider):
    """Lyrics provider for Genius.com."""
    
    DOMAINS = ['genius.com']
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if this provider can handle the given URL."""
        return any(domain in url.lower() for domain in cls.DOMAINS)
    
    def get_lyrics(self, track_url: str) -> Optional[str]:
        """Extract lyrics from a Genius track URL."""
        try:
            if not track_url:
                print("get_lyrics: Track URL is empty")
                return None
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            print(f"\nFetching lyrics from: {track_url}")
            response = requests.get(track_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the lyrics root div
            lyrics_root = soup.find('div', id='lyrics-root')
            if not lyrics_root:
                print("Could not find lyrics root element")
                return ""
            # Find all divs with data-lyrics-container="true"
            lyrics_containers = lyrics_root.find_all('div', attrs={'data-lyrics-container': 'true'})
            if not lyrics_containers:
                print("No lyrics containers found")
                return ""
            lyrics = []
            for container in lyrics_containers:
                if not container or not container.children:
                    continue
                for element in container.children:
                    # Skip div elements
                    if not element:
                        continue
                    if element.name == 'div':
                        continue
                    # Add newline for <br> tags
                    elif element.name == 'br':
                        lyrics.append('\n')
                    # Handle anchor tags that contain spans
                    elif element.name == 'a':
                        span = element.find('span')
                        if not span or not span.children:
                            continue
                        for child in span.children:
                            if not child:
                                continue
                            elif child.name == 'br':
                                lyrics.append('\n')
                            elif child.name == 'i':
                                lyrics.append(child.get_text())
                            elif child.string and child.string.strip():
                                lyrics.append(child.string)
                    # Handle text nodes
                    elif element.string and element.string.strip():
                        lyrics.append(element.string)
                    # Handle elements with text content (like <i> tags)
                    elif element.strings:
                        # Only add if there's actual text content
                        text = ''.join(element.strings).strip()
                        if text:
                            lyrics.append(text)
                # Add double newline after each container (verse/chorus)
                lyrics.append('\n\n')
            # Join all parts and clean up whitespace
            lyrics_text = ''.join(lyrics).strip()
            # Normalize newlines to have max 2 consecutive newlines
            lyrics_text = re.sub(r'\n{3,}', '\n\n', lyrics_text)
            return lyrics_text
            
        except Exception as e:
            print(f"Error fetching lyrics: {e}")
            return ""
    
    def get_track_info_without_lyrics_list_from_album(self, album_url: str) -> List[TrackInfo]:
        """Get all tracks from a Genius album URL."""
        try:
            print(f"Fetching album tracks from: {album_url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            # print(f"Fetching album page: {album_url}")
            response = requests.get(album_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            # Convert BeautifulSoup to string and parse with lxml
            html_str = str(soup)
            
            parser = etree.HTMLParser()
            tree = etree.fromstring(html_str, parser)
            album_nodes = tree.xpath('//h1[contains(@class, "header_with_cover_art-primary_info-title")]')
            album_name = album_nodes[0].text if (isinstance(album_nodes, list) and len(album_nodes) > 0 and hasattr(album_nodes[0], 'text')) else ''
            print(album_name)
            # Find the artist name
            artist_nodes = tree.xpath('//h2/a[contains(@class, "header_with_cover_art-primary_info-primary_artist")]')
            artist_name = artist_nodes[0].text if (isinstance(artist_nodes, list) and len(artist_nodes) > 0 and hasattr(artist_nodes[0], 'text')) else ''
            
            chart_rows = tree.xpath('//div[contains(@class, "chart_row")]')
            track_info_list_without_lyrics = []
            for chart_row in chart_rows:
                track_lyrics_number_node = chart_row.xpath('./div[contains(@class, "chart_row-number_container")][1]/span[1]/span[1]')
                # if node is an empty list, skip it
                if not isinstance(track_lyrics_number_node, list) or not len(track_lyrics_number_node) > 0 or not hasattr(track_lyrics_number_node[0], 'text') or not isinstance(track_lyrics_number_node[0].text, str):
                    continue
                track_lyrics_number = int(track_lyrics_number_node[0].text)
                track_lyrics_url_node = chart_row.xpath('./div[contains(@class, "chart_row-content")][1]/a[1]/@href')
                if not isinstance(track_lyrics_url_node, list) or not len(track_lyrics_url_node) > 0 or not isinstance(track_lyrics_url_node[0], str) or not track_lyrics_url_node[0].strip():
                    continue
                track_lyrics_url = track_lyrics_url_node[0].strip()
                track_lyrics_missing_text_node = chart_row.xpath('./div[contains(@class, "chart_row-metadata_element")][1]/text()')
                # currently, in genius albums, if lyrics are missing for a track, it will have (Missing Lyrics) in a row with class chart_row-metadata_element
                if isinstance(track_lyrics_missing_text_node, list) and len(track_lyrics_missing_text_node) > 0 and isinstance(track_lyrics_missing_text_node[0], str) and track_lyrics_missing_text_node[0].strip().lower() in ["(missing lyrics)", "(unreleased)"]:
                    continue
                track_lyrics_title_node = chart_row.xpath('./div[contains(@class, "chart_row-content")][1]/a[1]/h3[1]/text()')
                if not isinstance(track_lyrics_title_node, list) or not len(track_lyrics_title_node) > 0 or not isinstance(track_lyrics_title_node[0], str) or not track_lyrics_title_node[0].strip():
                    continue
                track_lyrics_title = track_lyrics_title_node[0].strip()
                track_info = TrackInfo(
                    title=track_lyrics_title,
                    artist=artist_name,
                    track_number=track_lyrics_number,
                    url=track_lyrics_url
                )
                track_info_list_without_lyrics.append(track_info)
            # Print the complete list
            print("\nList of track URLs:")
            print(track_info_list_without_lyrics)
            return track_info_list_without_lyrics
            
        except Exception as e:
            print(f"Error fetching album tracks: {e}")
            return []
    
    def get_track_info(self, track_url: str, track_number: int) -> Optional[TrackInfo]:
        """Get track information from a Genius track URL."""
        try:
            response = requests.get(track_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tracks = []
            
            # Parse the HTML with lxml for XPath support
            parser = etree.HTMLParser()
            tree = etree.fromstring(response.content, parser)
            
            # using xpath //h1[1]/div[1]/div[1]/div[1]/span[1]
            xpath = "//h1[1]/div[1]/div[1]/div[1]/span[1]"
            # Extract title
            title_elem = tree.xpath(xpath)
            if not title_elem or not hasattr(title_elem[0], 'text') or not title_elem[0].text.strip():
                title = ""
            else:
                title = title_elem[0].text.strip()

            # Extract artist
            # //*[@id="application"]/main/div[1]/div[3]/div/div[1]/div[1]/div[1]/span/span/a
            artist_elem = tree.xpath('//*[@id="application"]/main/div[1]/div[3]/div/div[1]/div[1]/div[1]/span/span/a')
            if not artist_elem or not hasattr(artist_elem[0], 'text') or not artist_elem[0].text.strip():
                artist = ""
            else:
                artist = artist_elem[0].text.strip()
            
            # Get lyrics
            lyrics = self.get_lyrics(track_url)

            return TrackInfo(
                title=title,
                artist=artist,
                url=track_url,
                track_number=track_number,
                lyrics=lyrics
            )
            
        except Exception as e:
            print(f"Error fetching track info: {e}")
            return None
