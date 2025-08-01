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
    
    let droppedFiles = [];
    
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
});
