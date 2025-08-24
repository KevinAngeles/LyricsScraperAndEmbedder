#!/usr/bin/env python3
"""
Web-based Lyrics Embedder

A simple web interface for embedding lyrics in audio files.
"""

import os
from flask import Flask, request, jsonify, Response, render_template
import json
import time
from providers.factory import ProviderFactory
from utilities import get_track_number, ensure_media_directory
from lyrics_embedder import add_lyrics_to_audio
from queue import Queue

# Simple message queue for SSE
class MessageAnnouncer:
    def __init__(self):
        self.listeners = []

    def listen(self):
        q = Queue()
        self.listeners.append(q)
        return q

    def announce(self, msg):
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except:
                del self.listeners[i]

announcer = MessageAnnouncer()

def format_sse(data, event=None):
    msg = []
    if event is not None:
        msg.append(f'event: {event}\n')
    msg.append(f'data: {json.dumps(data)}\n\n')
    return ''.join(msg)

app = Flask(__name__, template_folder='templates', static_folder='static')

# Create uploads directory in the same folder as the script
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    def generate():
        print("\n=== New SSE Connection Established ===")
        queue = announcer.listen()
        try:
            while True:
                msg = queue.get()
                print(f"Sending SSE message: {msg[:100]}...")  # Print first 100 chars of message
                yield msg
        except GeneratorExit:
            print("SSE Client disconnected")
        except Exception as e:
            print(f"Error in SSE stream: {e}")
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers.add('Cache-Control', 'no-cache')
    response.headers.add('Connection', 'keep-alive')
    return response

@app.route('/process', methods=['POST'], strict_slashes=False)
def process_files():
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        # List the uploaded files
        files = request.files.getlist('files')
        if not files or len(files) == 0:
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        url = request.form.get('url')
        if not url:
            return jsonify({'success': False, 'error': 'No URL provided'}), 400
        
        # Get the provider for the URL
        provider = ProviderFactory.get_provider_for_url(url)
        if not provider:
            return jsonify({'success': False, 'error': 'Unsupported URL. Please use a Genius or Musixmatch URL.'}), 400
        
        print("\n=== Processing Request ===")
        print(f"URL: {url}")
        print(f"Provider: {type(provider).__name__}")
        print(f"Files: {[f.filename for f in files]}")
        
        tracks_uploaded_dictionary = {}
        files_without_track_numbers = []
        
        success_count = 0
            
        print("\n=== Processing Uploaded Files ===")
        for i, file in enumerate(files, 1):
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            print(f"Saving file to: {upload_path}")
            file.save(upload_path)
            
            # Verify file was saved
            if not os.path.exists(upload_path):
                error_msg = f"ERROR: {file.filename} was not saved successfully"
                print(error_msg)
                files_without_track_numbers.append({
                    'filename': file.filename,
                    'error': error_msg
                })
                continue
            
            # Extract track number from metadata
            track_number = get_track_number(upload_path)
            if track_number is None:
                error_msg = f"No track number found in metadata"
                print(f"{file.filename}: {error_msg}")
                files_without_track_numbers.append({
                    'filename': file.filename,
                    'error': error_msg
                })
                # Remove the file since it doesn't have a track number
                os.remove(upload_path)
            else:
                file_size = os.path.getsize(upload_path)
                print(f"{file.filename}: Track {track_number}, Size: {file_size} bytes")
                tracks_uploaded_dictionary[track_number] = {
                    'path': upload_path,
                    'filename': file.filename,
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
        
        # Prepare response data with unified tracks list
        response_data = {
            'success': True,
            'tracks': unified_tracks,
            'upload_dir': app.config['UPLOAD_FOLDER']
        }
        
        # Send the track information to the client
        print("\n=== Sending Track Information via SSE ===")
        sse_message = format_sse(response_data, 'track_analysis')
        print(f"Message: {sse_message}")
        announcer.announce(sse_message)
        print("Track information sent to client")
        
        # If no tracks with track numbers were found, return early
        if not tracks_uploaded_dictionary:
            return jsonify({
                'success': False,
                'error': 'No tracks with valid track numbers were found in the uploaded files',
                'details': response_data
            }), 400
        
        # Fetch the list of urls for tracks lyrics from the album
        print("\n=== Fetching Album Tracks ===")
        unprocessed_track_info_list = provider.get_track_info_without_lyrics_list_from_album(url)
        if not unprocessed_track_info_list:
            return jsonify({'success': False, 'error': 'No tracks found for this album URL'}), 404
        
        # Create a list of track info that match the track numbers
        matched_unprocessed_track_info_list = []
        for unprocessed_track_info in unprocessed_track_info_list:
            track_number = unprocessed_track_info.track_number
            if track_number in tracks_uploaded_dictionary:
                matched_unprocessed_track_info_list.append(unprocessed_track_info)
        
        # Print every unprocessed track_info from matched_unprocessed_track_info_list
        for unprocessed_track_info in matched_unprocessed_track_info_list:
            print(unprocessed_track_info)
        
        # Check if lyrics exist for each track and prepare track info with status
        track_info_dicts = []
        for track in matched_unprocessed_track_info_list:
            # Try to get lyrics to verify they exist
            status = 'found' if track.url and track.url.strip() else 'error'
            message = 'lyrics found...' if status == 'found' else 'lyrics not found'
            
            track_info_dicts.append({
                'title': track.title,
                'artist': track.artist,
                'track_number': track.track_number,
                'url': track.url,
                'message': message,
                'status': status  # These tracks already passed initial validation
            })
        
        # Send the list of album lyrics that matches the uploaded tracks to client
        print("\n=== Sending Album Lyrics via SSE ===")
        sse_message = format_sse({'tracks': track_info_dicts}, 'tracks')
        print(f"Message: {sse_message}")
        announcer.announce(sse_message)
        print("Album lyrics sent to client")

        # Process each track and send updates
        processed_count = 0
        at_least_one_lyric_successfully_processed = False
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
                if track_info:
                    at_least_one_lyric_successfully_processed = True
                    # Send processed update with track info
                    update_msg = format_sse({
                        'title': track_info.title,
                        'artist': track_info.artist,
                        'track_number': track_number,
                        'url': track_info.url,
                        'status': 'processing',
                        'message': 'Processing...',
                        'track_id': track_id,
                        'progress': progress_number
                    }, 'track_update')
                    announcer.announce(update_msg)
                    continue
                
                # If we get here, either track_info is None
                error_msg = f'No lyric found for track {track_number}'
                update_msg = format_sse({
                    'title': f'Track {track_number}',
                    'artist': '',
                    'track_number': track_number,
                    'url': '',
                    'status': 'error',
                    'track_id': track_id,
                    'message': error_msg,
                    'progress': progress_number
                }, 'track_update')
                announcer.announce(update_msg)
            
            except Exception as e:
                error_msg = f'Error processing track {track_number}: {str(e)}'
                track_info_dict = {
                    'track_id': track_id,
                    'status': 'error',
                    'message': error_msg,
                    'url': '',
                    'title': f'Track {track_number}',
                    'artist': '',
                    'track_number': track_number,
                    'progress': progress_number
                }
                update_msg = format_sse(track_info_dict, 'track_update')
                announcer.announce(update_msg)
        
        if not at_least_one_lyric_successfully_processed:
            return jsonify({'success': False, 'error': 'No tracks were successfully processed'}), 404

        for embedding_index, matched_unprocessed_track_info in enumerate(matched_unprocessed_track_info_list):
            embedding_progress = ((embedding_index+1)/len(matched_unprocessed_track_info_list))*100
            try:
                matched_processed_track_info = provider.get_track_info(matched_unprocessed_track_info.url, matched_unprocessed_track_info.track_number)
                lyrics = matched_processed_track_info.lyrics
                if not lyrics:
                    print(f"No lyrics found for track {matched_processed_track_info.track_number}")
                    continue
                # Get the saved file path from tracks_uploaded_dictionary
                file_info = tracks_uploaded_dictionary.get(matched_processed_track_info.track_number)
                if not file_info:
                    print(f"File not found for track {matched_processed_track_info.track_number}")
                    update_msg = format_sse({
                        'track_id': track_id,
                        'status': 'error',
                        'track_number': matched_processed_track_info.track_number,
                        'message': 'Failed to process track {matched_processed_track_info.track_number}',
                        'url': matched_processed_track_info.url,
                        'track_title': matched_processed_track_info.title,
                        'artist': matched_processed_track_info.artist,
                        'progress': embedding_progress
                    }, 'track_update')
                    announcer.announce(update_msg)
                    continue
                print(f"\n=== Processing file: {file_info['path']} ===")
                print(f"Original size: {os.path.getsize(file_info['path'])} bytes")
                success = add_lyrics_to_audio(file_info['path'], lyrics)
                if success:
                    success_count += 1
                    print(f"Successfully embedded lyrics in {file_info['filename']}")
                    update_msg = format_sse({
                        'track_id': track_id,
                        'track_number': matched_processed_track_info.track_number,
                        'status': 'success',
                        'message': f'Lyrics successfully embedded',
                        'url': matched_processed_track_info.url,
                        'track_title': matched_processed_track_info.title,
                        'artist': matched_processed_track_info.artist,
                        'progress': embedding_progress
                    }, 'track_update')
                    announcer.announce(update_msg)
                else:
                    print(f"Failed to embed lyrics in {file_info['filename']}")
                    update_msg = format_sse({
                        'track_id': track_id,
                        'status': 'error',
                        'track_number': matched_processed_track_info.track_number,
                        'message': f'Failed to process {file_info["filename"]}',
                        'url': matched_processed_track_info.url,
                        'track_title': matched_processed_track_info.title,
                        'artist': matched_processed_track_info.artist,
                        'progress': embedding_progress
                    }, 'track_update')
                    announcer.announce(update_msg)
            except FileNotFoundError:
                print(f"File not found: {file_info['path']}")
        # Small delay to ensure all messages are sent
        time.sleep(0.5)
        print("-" * 50)
        if success_count > 0:
            return jsonify({'success': True, 'processed_count': processed_count, 'total_tracks': len(tracks_uploaded_dictionary), 'message': 'Lyrics embedded successfully', 'success_count': success_count}), 200
        return jsonify({'success': False, 'processed_count': processed_count, 'total_tracks': len(tracks_uploaded_dictionary), 'message': 'Failed to embed lyrics', 'success_count': success_count}), 200
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        try:
            # Try to send the error via SSE before returning
            if 'track_id' in locals():
                update_msg = format_sse({
                    'track_id': track_id,
                    'status': 'error',
                    'message': f'Server error: {error_msg}'
                }, 'track_update')
                announcer.announce(update_msg)
                time.sleep(0.5)  # Give time for message to be sent
        except Exception as sse_error:
            print(f"Error sending SSE error message: {sse_error}")
        return jsonify({'success': False, 'error': f'Error processing request: {error_msg}'}), 500

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Ensure static directories exist
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Ensure media directory exists
    ensure_media_directory()
    
    # Run the Flask app
    print("Starting Lyrics Embedder server...")
    print(f"Temporary upload folder: {app.config['UPLOAD_FOLDER']}")
    app.run(debug=True, host='0.0.0.0', port=5000)
