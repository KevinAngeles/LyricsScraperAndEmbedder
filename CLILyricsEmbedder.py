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

import os
import time
import sys
from typing import List
from pathlib import Path
from Utilities import ensure_media_directory, get_provider_from_url, get_track_number
from LyricsEmbedder import add_lyrics_to_audio

def embed_files(media_files: List[Path], provider, url: str):
    if not url or len(media_files) == 0:
        print("No files provided")
        return False
    if not media_files or len(media_files) == 0:
        print("No files provided")
        return False

    # Get the provider for the URL
    try:
        print("\n=== Processing Request ===")
        print(f"Provider: {type(provider).__name__}")
        print(f"Files: {[f.name for f in media_files]}")
        
        tracks_uploaded_dictionary = {}
        files_without_track_numbers = []
        
        embed_count = 0
        success_count = 0
            
        print("\n=== Processing Uploaded Files ===")
        for i, file in enumerate(media_files, 1):
            # Extract track number from metadata
            track_number = get_track_number(str(file))
            if track_number is None:
                error_msg = f"No track number found in metadata"
                print(f"{file.name}: {error_msg}")
                files_without_track_numbers.append({
                    'filename': file.name,
                    'error': error_msg
                })
                continue
            file_size = file.stat().st_size
            print(f"{file.name}: Track {track_number}, Size: {file_size} bytes")
            tracks_uploaded_dictionary[track_number] = {
                'path': file,
                'filename': file.name,
                'size': file_size
            }
        
        # Sort tracks by track number
        sorted_tracks = dict(sorted(tracks_uploaded_dictionary.items()))
        
        # Prepare unified tracks list with status information
        unified_tracks = []
        
        # Add valid tracks with 'processing' status
        for num, info in sorted_tracks.items():
            unified_tracks.append({
                'track_number': num,
                'filename': info['filename'],
                'size': info['size'],
                'status': 'uploaded',
                'message': 'File uploaded'
            })
        
        # Add invalid tracks with error status
        for track in files_without_track_numbers:
            unified_tracks.append({
                'track_number': None,
                'filename': track['filename'],
                'size': 0,
                'status': 'error',
                'message': 'File does not have a track number in its metadata'
            })
        
        # Sort unified tracks by track number (valid tracks first, then invalid)
        unified_tracks.sort(key=lambda x: (x['track_number'] is None, x['track_number']))
        
        # If no tracks with track numbers were found, return early
        if not tracks_uploaded_dictionary:
            print('No tracks with valid track numbers were found in the uploaded files')
            return False
        
        # Fetch the list of urls for tracks lyrics from the album
        print("\n=== Fetching Album Tracks ===")
        unprocessed_track_info_list = provider.get_track_info_without_lyrics_list_from_album(url)
        if not unprocessed_track_info_list:
            print('No tracks found for this album URL')
            return False
        
        # Create a list of track info that match the track numbers
        matched_unprocessed_track_info_list = []
        for unprocessed_track_info in unprocessed_track_info_list:
            track_number = unprocessed_track_info.track_number
            if track_number in tracks_uploaded_dictionary:
                matched_unprocessed_track_info_list.append(unprocessed_track_info)
        
        # Print every unprocessed track_info from matched_unprocessed_track_info_list
        for unprocessed_track_info in matched_unprocessed_track_info_list:
            print(unprocessed_track_info)
         
        # Process each track and send updates
        processed_count = 0
        at_least_one_lyric_successfully_processed = False
        matched_processed_track_info_dict = {}
        for i, matched_unprocessed_track_info in enumerate(matched_unprocessed_track_info_list):
            processed_count += 1
            track_id = matched_unprocessed_track_info.url.split('/')[-1]
            track_number = matched_unprocessed_track_info.track_number
            progress_number = (processed_count/len(matched_unprocessed_track_info_list))*100
            # Simulate processing time
            time.sleep(0.5)

            # Process the track
            try:
                # First get track info to display
                track_info = provider.get_track_info(matched_unprocessed_track_info.url, track_number)
                if track_info and track_info.lyrics and track_info.lyrics.strip() != '':
                    at_least_one_lyric_successfully_processed = True
                    # Success: processed update with track info
                    # Update the track info in the list with the one that has lyrics
                    matched_processed_track_info_dict[track_number] = track_info
                    print(f"Lyric downloaded for track {track_number}")
                    continue
                
                # If we get here, either track_info is None or process_track failed
                error_msg = f'No lyric found for track {track_number}'
                print(error_msg)
           
            except Exception as e:
                error_msg = f'Error processing track {track_number}: {str(e)}'
                print(error_msg)
        
        if not at_least_one_lyric_successfully_processed:
            print('No tracks were successfully processed')
            return False
        print('At least one lyric was successfully downloaded')

        for track_number, processed_track_info in matched_processed_track_info_dict.items():
            # Get the saved file path from tracks_uploaded_dictionary
            file_info = tracks_uploaded_dictionary.get(track_number)
            if file_info:
                print(f"\n=== Processing file: {file_info['path']} ===")
            file_path = str(file_info['path'])
            print(f"Original size: {os.path.getsize(file_path)} bytes")
            print(f"Lyrics type: {type(processed_track_info.lyrics)}")
            print(f"Lyrics preview: {str(processed_track_info.lyrics)[:30]}..." if processed_track_info.lyrics else "No lyrics content")
            success = add_lyrics_to_audio(file_path, processed_track_info.lyrics)
            
            if success:
                success_count += 1
                print(f"Successfully embedded lyrics in {file_info['filename']}")
            else:
                print(f"Failed to embed lyrics in {file_info['filename']}")
        
        if success_count > 0:
            print(
                f"Successfully embedded lyrics in {success_count} files",
                {
                    'success': True,
                    'processed_count': processed_count,
                    'total_tracks': len(tracks_uploaded_dictionary),
                    'message': 'Lyrics embedded successfully',
                    'success_count': success_count
                }
            )
            return True
        print("No files were successfully embedded")
        return False
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        return False

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
    
    # Check if there are any files in the media directory
    media_files = list(Path(media_dir).glob('*'))
    if not any(f.suffix.lower() in ['.mp3', '.m4a'] for f in media_files):
        print(f"Warning: No audio files found in {media_dir}")
        print("Please add your audio files to the 'media' directory and run the script again.")
        return
    success = embed_files(media_files, provider, url)
    if not success:
        print("Failed to embed lyrics to audio files")
        return
    
    print("\n" + "="*50)
    print("WORKFLOW COMPLETE!")
    print("="*50)

if __name__ == "__main__":
    main()
