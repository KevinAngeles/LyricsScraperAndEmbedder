#!/usr/bin/env python3
"""
Web-based Lyrics Embedder

A simple web interface for embedding lyrics in audio files.
"""

import os
from flask import Flask, render_template

app = Flask(__name__, template_folder='templates', static_folder='static')

# Create uploads directory in the same folder as the script
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Ensure static directories exist
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Run the Flask app
    print("Starting Lyrics Embedder server...")
    print(f"Temporary upload folder: {app.config['UPLOAD_FOLDER']}")
    app.run(debug=True, host='0.0.0.0', port=5000)
