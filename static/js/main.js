document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const dropArea = document.getElementById('drop-area');
    const fileList = document.getElementById('file-list');
    const lyricsUrl = document.getElementById('lyrics-url');
    const embedBtn = document.getElementById('embed-btn');
    const fileInput = document.getElementById('file-input');
    const processingSection = document.getElementById('processing-section');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const trackList = document.getElementById('track-list');
    const validTracksContainer = document.getElementById('valid-tracks');
    const invalidTracksContainer = document.getElementById('invalid-tracks');
    
    let droppedFiles = [];
    let track_info_list = [];
    
    // Helper Functions
    function formatFileSize(bytes) {
        if (bytes === 0 || !bytes) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function showMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `status-message ${type}`;
        messageDiv.textContent = message;
        
        const targetElement = document.querySelector('.input-group');
        if (targetElement && targetElement.parentNode) {
            targetElement.parentNode.insertBefore(messageDiv, targetElement);
        } else {
            // Fallback to appending to body if .input-group is not found
            document.body.prepend(messageDiv);
        }
        
        // Remove message after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
    
    function updateProgress(percent) {
        progressBar.style.width = `${percent}%`;
        progressText.textContent = `${Math.round(percent)}%`;
    }
    
    // File Handling
    function handleFiles(files) {
        const newFiles = Array.from(files).filter(file => 
            file.type.startsWith('audio/') || 
            file.name.toLowerCase().endsWith('.mp3') || 
            file.name.toLowerCase().endsWith('.m4a')
        );
        
        if (newFiles.length === 0) {
            showMessage('Please select audio files (MP3 or M4A)', 'error');
            return;
        }
        
        // Add new files to the list
        newFiles.forEach(file => {
            if (!droppedFiles.some(f => f.name === file.name && f.size === file.size)) {
                droppedFiles.push(file);
            }
        });
        
        updateFileList();
        updateEmbedButton();
    }
    
    function updateFileList() {
        fileList.innerHTML = '';
        
        if (droppedFiles.length === 0) {
            fileList.innerHTML = '<p>No files selected</p>';
            return;
        }
        
        droppedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <div class="file-info" title="${file.name}">
                    ${file.name} (${formatFileSize(file.size)})
                </div>
                <span class="file-status pending">Pending</span>
                <button class="remove-file" onclick="event.stopPropagation(); removeFile(${index})" title="Remove file">×</button>
            `;
            fileList.appendChild(fileItem);
        });
    }
    
    function updateEmbedButton() {
        embedBtn.disabled = droppedFiles.length === 0 || !lyricsUrl.value.trim();
    }
    
    // Make removeFile available globally
    window.removeFile = function(index) {
        droppedFiles.splice(index, 1);
        updateFileList();
        updateEmbedButton();
    };
    
    // Drag and Drop Handlers
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        dropArea.classList.add('highlight');
    }
    
    function unhighlight() {
        dropArea.classList.remove('highlight');
    }
    
    // Event Listeners
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    dropArea.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });
    
    dropArea.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });
    
    lyricsUrl.addEventListener('input', updateEmbedButton);
    
    // Process Files
    embedBtn.addEventListener('click', processFiles);
    
    function processFiles() {
        if (droppedFiles.length === 0 || !lyricsUrl.value.trim()) return;
        
        const formData = new FormData();
        droppedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('url', lyricsUrl.value.trim());
        
        // Clear lyricsUrl abd reset file list (from drag and drop feature)
        lyricsUrl.value = '';
        updateEmbedButton();
        fileList.innerHTML = '<p>Files Uploaded</p>';
        droppedFiles = [];

        // Show processing section
        processingSection.style.display = 'block';
        
        // Reset progress
        updateProgress(0);
        
        // Send files to server
        fetch('/process', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('Successfully processed all tracks!', 'success');
            } else {
                showMessage(`Error: ${data.error}`, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('An error occurred while processing the files', 'error');
        });
    }
    
    // SSE Event Listeners
    const eventSource = new EventSource('/stream');
    
    function updateTrackList(tracks) {
        // Clear previous content
        validTracksContainer.innerHTML = '';
        invalidTracksContainer.innerHTML = '';
        
        if (tracks && tracks.length > 0) {
            let validCount = 0;
            let invalidCount = 0;
            
            // Process all tracks (both valid and invalid)
            tracks.forEach(track => {
                const trackItem = document.createElement('div');
                trackItem.className = 'track-item';
                message = track?.message || '';
                // available status: uploaded, found, processing, success, error
                css_status = "status-found";
                switch (track.status) {
                    case "uploaded":
                        css_status = "status-uploaded";
                        break;
                    case "found":
                        css_status = "status-found";
                        break;
                    case "processing":
                        css_status = "status-processing";
                        break;
                    case "success":
                        css_status = "status-success";
                        break;
                    default:
                        css_status = "status-error";
                        break;
                }
                if (track.status !== 'error') {
                    validCount++;
                    trackItem.innerHTML = `
                        <div class="track-info">
                            <strong>Track ${track.track_number}</strong>: ${track.filename}
                            <small>(${formatFileSize(track.size)})</small>
                        </div>
                        <span class="track-status ${css_status}">${message}</span>
                    `;
                    validTracksContainer.appendChild(trackItem);
                } else {
                    invalidCount++;
                    trackItem.innerHTML = `
                        <div class="track-info">
                            <strong>${track.filename}</strong>
                            <div class="error-message">${message}</div>
                        </div>
                    `;
                    invalidTracksContainer.appendChild(trackItem);
                }
            });
            
            // Update counters
            document.getElementById('valid-tracks-count').textContent = `(${validCount})`;
            document.getElementById('invalid-tracks-count').textContent = `(${invalidCount})`;
            
            // Show appropriate messages if no tracks in a section
            if (validCount === 0) {
                validTracksContainer.innerHTML = '<p class="no-tracks">No valid tracks found</p>';
            }
            if (invalidCount === 0) {
                invalidTracksContainer.innerHTML = '<p class="no-tracks">No issues found</p>';
            }
        } else {
            validTracksContainer.innerHTML = '<p class="no-tracks">No tracks found</p>';
            invalidTracksContainer.innerHTML = '<p class="no-tracks">No issues found</p>';
            document.getElementById('valid-tracks-count').textContent = '(0)';
            document.getElementById('invalid-tracks-count').textContent = '(0)';
        }
    }
    
    eventSource.addEventListener('tracks', function(e) {
        try {
            const data = JSON.parse(e.data);
            console.log('Received tracks event:', data);
            
            processingSection.style.display = 'block';
            trackList.innerHTML = ''; // Clear previous content
            // Match total tracks with track update
            let current_idx = 0
            let updated_idx = 0
            while (current_idx < track_info_list.length && updated_idx < data.tracks.length) {
                if (track_info_list[current_idx].track_number == data.tracks[updated_idx].track_number) {
                    track_info_list[current_idx].status = data.tracks[updated_idx].status;
                    track_info_list[current_idx].message = data.tracks[updated_idx].message;
                    current_idx += 1
                    updated_idx += 1
                } else if (track_info_list[current_idx].track_number > data.tracks[updated_idx].track_number) {
                    updated_idx += 1
                } else {
                    current_idx += 1
                }
            }
            updateTrackList(track_info_list);
        } catch (error) {
            console.error('Error processing tracks event:', error, 'Data:', e.data);
            showMessage('Error processing track list from server', 'error');
        }
    });
    
    eventSource.addEventListener('track_analysis', function(e) {
        try {
            const data = JSON.parse(e.data);
            console.log('Received track_analysis event:', data);
            
            track_info_list = data.tracks;
            updateTrackList(track_info_list);
            
        } catch (error) {
            console.error('Error processing track_analysis event:', error);
            showMessage('Error processing track analysis', 'error');
        }
    });
    
    // Handle album lyrics verification status
    eventSource.addEventListener('album_lyrics', function(e) {
        try {
            const data = JSON.parse(e.data);
            console.log('Received album_lyrics event:', data);
            
            if (!(data.tracks && data.tracks.length > 0)) {
                console.error('Received invalid album_lyrics event:', data);
                return;
            }   
            // Update each track's status based on lyrics verification
            data.tracks.forEach(track => {
                if (!track.is_valid) return; // Skip invalid tracks
                
                // Find the track by its track number in the valid tracks container
                const trackItems = validTracksContainer.querySelectorAll('.track-item');
                trackItems.forEach(trackItem => {
                    const trackTitle = trackItem.querySelector('.track-info strong');
                    if (!(trackTitle)) {
                        return;
                    }
                    // The title is in format: "Track {number}: {filename}"
                    const titleText = trackTitle.textContent;
                    const expectedPrefix = `Track ${track.track_number}: `;
                    
                    if (!(titleText.startsWith(expectedPrefix))) {
                        return;
                    }
                    const statusElement = trackItem.querySelector('.track-status');
                    if (!(statusElement)) {
                        return;
                    }
                    statusElement.textContent = track.status;
                    // Update status class based on lyrics status
                    message = track?.message || '';
                    // available status: uploaded, found, processing, success, error
                    css_status = "status-found";
                    switch (track.status) {
                        case "uploaded":
                            css_status = "status-uploaded";
                            break;
                        case "found":
                            css_status = "status-found";
                            break;
                        case "processing":
                            css_status = "status-processing";
                            break;
                        case "success":
                            css_status = "status-success";
                            break;
                        default:
                            css_status = "status-error";
                            break;
                    }
                    statusElement.className = 'track-status ' + css_status;
                });
            });
        } catch (error) {
            console.error('Error processing album_lyrics event:', error, 'Data:', e.data);
            showMessage('Error processing lyrics verification', 'error');
        }
    });

    eventSource.addEventListener('track_update', function(e) {
        try {
            const data = JSON.parse(e.data);
            console.log('Received track_update event:', data);
            
            processingSection.style.display = 'block';
            trackList.innerHTML = ''; // Clear previous content
            // Match total tracks with track update
            let track_number = data.track_number
            let track_status = data.status
            let left = 0
            let right = track_info_list.length - 1;
            while (left <= right) {
                let mid = Math.floor((left + right) / 2);
                if (track_info_list[mid].track_number === track_number) {
                    track_info_list[mid].status = track_status
                    track_info_list[mid].message = data.message
                    break;
                } else if (track_info_list[mid].track_number < track_number) {
                    left = mid + 1;
                } else {
                    right = mid - 1;
                }
            }
            updateTrackList(track_info_list);
            
            // Update progress if available
            if (data.progress !== undefined) {
                updateProgress(parseFloat(data.progress));
            }
            
        } catch (error) {
            console.error('Error processing track_update event:', error);
        }
    });
    
    eventSource.addEventListener('error', function(e) {
        console.error('SSE Error:', e);
        showMessage('Connection to server lost. Please refresh the page.', 'error');
    });
});
