import os
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, parse_qs, urlparse
import json
import time
from lxml import etree
from .base_provider import LyricsProvider, TrackInfo
import traceback

class MusixmatchProvider(LyricsProvider):
    """Lyrics provider for Musixmatch.com."""
    
    DOMAINS = ['musixmatch.com']
    BASE_URL = 'https://www.musixmatch.com'
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.musixmatch.com/'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if this provider can handle the given URL."""
        return any(domain in url.lower() for domain in cls.DOMAINS)

    def _save_debug_html(self, soup: BeautifulSoup, filename: str = 'debug.txt') -> None:
        """Save HTML from a specific XPath to a debug file."""
        try:
            # Convert BeautifulSoup to string and parse with lxml
            html_str = str(soup)
            
            parser = etree.HTMLParser()
            tree = etree.fromstring(html_str, parser)
            # Define the XPath
            # XPath to check for exact text match
            # XPath is the div that directly contains the text case insensitive show performers
            xpath = '//*[@id="__next"]/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div/div/div[2]/div[1]/div[1]/div/div[1]'
            # verify if the div contains the text show performers using xpath xp
            element = tree.xpath(xpath)
            if element:
                text = element[0].text
            has_show_performance = element[0].text and element[0].text.lower() == 'show performers'
            if has_show_performance:
                xpath = '//*[@id="__next"]/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div/div/div[2]/div[1]'
            else:
                xpath = '//*[@id="__next"]/div/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[2]/div[1]/div[1]'

            # Find the element using XPath
            element = tree.xpath(xpath)
            if not element:
                print(f"No element found with XPath: {xpath}")
                return
            # dbg = etree.tostring(element[0], pretty_print=True, encoding='unicode')
            
            # Get all paragraph divs (direct children of the container)
            list_of_html_paragraphs = element[0].xpath('./div')
            
            # Process each paragraph to get its text lines
            lyric_lines = []
            for paragraph in list_of_html_paragraphs:
                # Get all text lines in this paragraph
                lines = paragraph.xpath('.//div[not(*)]/text()')
                # Add non-empty lines to the current paragraph
                paragraph_text = '\n'.join(line.strip() for line in lines if line.strip())
                if paragraph_text:  # Only add non-empty paragraphs
                    lyric_lines.append(paragraph_text)

            # For each paragraph extract the text and add it to the lyrics
            lyrics = ""
            for paragraph in list_of_html_paragraphs:
                # Only get divs with no child elements at all
                text_divs = paragraph.xpath('.//div[not(descendant::div)][normalize-space()]')
                print(f"Found {len(text_divs)} text divs in paragraph")
                for div in text_divs:
                    if div.text and div.text.strip():
                        lyrics += div.text.strip() + "\n"
                if text_divs:  # Only add newline if we found text
                    lyrics += "\n"
            
            # Join paragraphs with double newlines for spacing
            lyrics = re.sub(r'^Show performers\s', '', lyrics)
            lyrics = re.sub(r'Add to favorites\s*Share\s*', '', lyrics)
            lyrics = lyrics.strip()
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(lyrics)
            
            print(f"Debug HTML saved to {os.path.abspath(filename)}")
            
        except Exception as e:
            print(f"Error saving debug HTML: {e}")
            traceback.print_exc()
    
    def get_lyrics(self, track_url: str) -> Optional[str]:
        """Extract lyrics from a Musixmatch track URL."""
        try:
            print(f"\nFetching lyrics from Musixmatch: {track_url}")
            
            # Set headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.musixmatch.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = self.session.get(track_url, headers=headers)
            response.raise_for_status()
            
            # Check if we got a valid HTML response
            if not response.text.strip():
                print("Received empty response from server")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            # Parse the HTML with lxml for XPath support
                     
            # Convert BeautifulSoup to string and parse with lxml
            html_str = str(soup)
            parser = etree.HTMLParser()
            tree = etree.fromstring(html_str, parser)
            # Search inside the xpath
            xpath = '//*[@id="__next"]/div/div/div/div[1]/div'
            element = tree.xpath(xpath)
            if not element:
                return None
            element_str = ""
            # convert element to string and search if it contains the text "verse" or "chorus" ir "outro"
            for node in element:
                element_str += etree.tostring(node, pretty_print=True, encoding='unicode').lower()
            xpath = '//*[@id="__next"]/div/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[2]/div[1]/div[1]'
            if 'verse' in element_str or 'chorus' in element_str or 'outro' in element_str:
                print("=========Found verse, chorus or outro")
                xpath = '//*[@id="__next"]/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div/div/div[2]/div[1]'
            
            # Find the element using XPath
            element = tree.xpath(xpath)
            if not element:
                print(f"No element found with XPath: {xpath}")
                return None
            
            # Get all paragraph divs (direct children of the container)
            list_of_html_paragraphs = element[0].xpath('./div')

            # For each paragraph extract the text and add it to the lyrics
            lyrics = ""
            for paragraph in list_of_html_paragraphs:
                add_newline = False
                for node in paragraph:
                    # if node is a div that directly contains an h3, skip it
                    if node.tag == 'div' and node.xpath('.//h3'):
                        node = node.xpath('.//*[self::div or self::h3][not(descendant::div)][normalize-space()]')
                        heading_line = []
                        for div in node:
                            if div.text and div.text.strip():
                                heading_line.append(div.text.strip())
                                add_newline = True
                        lyrics += "["
                        lyrics += " - ".join(heading_line)
                        lyrics += "]\n"
                        continue
                    node = node.xpath('.//div[not(descendant::div)][normalize-space()]')
                    for div in node:
                        if div.text and div.text.strip():
                            lyrics += div.text.strip() + "\n"
                            add_newline = True
                
                if add_newline:  # Only add newline if we found text
                    lyrics += "\n"
            
            # Join paragraphs with double newlines for spacing
            lyrics = re.sub(r'^Show performers\s', '', lyrics)
            lyrics = re.sub(r'Add to favorites\s*Share\s*', '', lyrics)
            lyrics = lyrics.strip()
            return lyrics
            
        except Exception as e:
            print(f"Unexpected error while fetching lyrics: {e}")
            traceback.print_exc()
            return None
    
    def get_track_info_without_lyrics_list_from_album(self, album_url: str) -> List[TrackInfo]:
        """Get all tracks from a Musixmatch album URL."""
        try:
            print(f"Fetching album tracks from: {album_url}")
            response = self.session.get(album_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tracks = []
            
            # Parse the HTML with lxml for XPath support
            parser = etree.HTMLParser()
            tree = etree.fromstring(response.content, parser)
            
            # Find the main container using XPath
            container = tree.xpath('//*[@id="__next"]/div/div/div/div[1]/div/div/div/div[2]/div/div/div[2]/div[2]/div')
            
            if not container:
                print("Could not find the tracks container using XPath")
                return []
                
            # Find all direct child div elements that contain track information
            track_divs = container[0].xpath('./div')
            
            if not track_divs:
                print("No track divs found in the container")
                return []
            
            for idx, track_div in enumerate(track_divs, 1):
                try:
                    # Find the <a> tag with href attribute
                    link = track_div.xpath('.//a[@href]')
                    if not link:
                        print(f"No link found for track {idx}")
                        continue
                        
                    # Get the relative URL from href
                    href = link[0].get('href')
                    if not href:
                        print(f"No href found for track {idx}")
                        continue
                    
                    # Construct full URL
                    track_url = urljoin(self.BASE_URL, href)
                    
                    # Extract title and artist from the track URL
                    # The URL format is /lyrics/ARTIST/TITLE
                    parts = href.split('/')
                    if len(parts) >= 4:  # ['', 'lyrics', artist, title, ...]
                        artist = parts[2].replace('-', ' ').title()
                        title = parts[3].replace('-', ' ').title()
                    else:
                        # Fallback to track number if we can't parse from URL
                        artist = "Unknown Artist"
                        title = f"Track {idx}"
                    
                    tracks.append(TrackInfo(
                        title=title,
                        artist=artist,
                        track_number=idx,
                        url=track_url
                    ))
                    
                except Exception as e:
                    print(f"Error processing track {idx}: {e}")
            
            return tracks
            
        except Exception as e:
            print(f"Error fetching album tracks: {e}")
            return []
    
    def get_track_info(self, track_url: str, track_number: int) -> Optional[TrackInfo]:
        """Get track information from a Musixmatch track URL."""
        try:
            response = self.session.get(track_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove self.base_url from track_url
            href = track_url.replace(self.BASE_URL, '')
            
            # The URL format is /lyrics/ARTIST/TITLE
            # Extract title and artist from the track URL
            parts = href.split('/')
            artist = ""
            title = ""
            if len(parts) >= 4:  # ['', 'lyrics', artist, title, ...]
                artist = parts[2].replace('-', ' ').title()
                title = parts[3].replace('-', ' ').title()
            
            # Get lyrics
            lyrics = self._get_lyrics_from_page(soup)
            
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
