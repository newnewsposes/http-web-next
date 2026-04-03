/**
 * Chunked file upload with progress tracking
 */

class ChunkedUploader {
    constructor(file, options = {}) {
        this.file = file;
        this.chunkSize = options.chunkSize || 1024 * 1024; // 1MB default
        this.isPublic = options.isPublic !== undefined ? options.isPublic : true;
        this.isBrowsable = options.isBrowsable !== undefined ? options.isBrowsable : false;
        this.uploadId = null;
        this.totalChunks = Math.ceil(file.size / this.chunkSize);
        this.uploadedChunks = 0;
        this.aborted = false;
        
        // Callbacks
        this.onProgress = options.onProgress || (() => {});
        this.onComplete = options.onComplete || (() => {});
        this.onError = options.onError || (() => {});
    }
    
    async start() {
        try {
            // Validate file first
            const validationResult = await this.validateFile();
            if (!validationResult.valid) {
                this.onError(validationResult.error);
                return;
            }
            
            // Initialize upload
            await this.initUpload();
            
            // Upload chunks
            for (let i = 0; i < this.totalChunks; i++) {
                if (this.aborted) {
                    await this.cancel();
                    return;
                }
                
                await this.uploadChunk(i);
                this.uploadedChunks++;
                
                const progress = (this.uploadedChunks / this.totalChunks) * 100;
                this.onProgress(progress, this.uploadedChunks, this.totalChunks);
            }
            
            // Complete upload
            await this.completeUpload();
        } catch (error) {
            this.onError(error.message);
        }
    }
    
    async validateFile() {
        const response = await fetch('/api/files/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                fileSize: this.file.size,
                fileName: this.file.name,
                mimeType: this.file.type
            })
        });
        
        return await response.json();
    }
    
    async initUpload() {
        const response = await fetch('/api/upload/init', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: this.file.name,
                fileSize: this.file.size,
                mimeType: this.file.type
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to initialize upload');
        }
        
        const data = await response.json();
        this.uploadId = data.uploadId;
        this.chunkSize = data.chunkSize;
        this.totalChunks = Math.ceil(this.file.size / this.chunkSize);
    }
    
    async uploadChunk(chunkIndex) {
        const start = chunkIndex * this.chunkSize;
        const end = Math.min(start + this.chunkSize, this.file.size);
        const chunk = this.file.slice(start, end);
        
        const formData = new FormData();
        formData.append('uploadId', this.uploadId);
        formData.append('chunkIndex', chunkIndex);
        formData.append('chunk', chunk);
        
        const response = await fetch('/api/upload/chunk', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `Failed to upload chunk ${chunkIndex}`);
        }
    }
    
    async completeUpload() {
        const response = await fetch('/api/upload/complete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                uploadId: this.uploadId,
                totalChunks: this.totalChunks,
                filename: this.file.name,
                mimeType: this.file.type,
                isPublic: this.isPublic,
                isBrowsable: this.isBrowsable
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to complete upload');
        }
        
        const data = await response.json();
        this.onComplete(data);
    }
    
    async cancel() {
        if (this.uploadId) {
            await fetch(`/api/upload/cancel/${this.uploadId}`, {
                method: 'DELETE'
            });
        }
    }
    
    abort() {
        this.aborted = true;
    }
}

// Share link copy function
function copyShareLink(url, el) {
    // Try navigator.clipboard first (secure contexts)
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(() => {
            showToast('Link copied to clipboard!', 'success');
            if (el) {
                const original = el.innerHTML;
                el.innerHTML = 'Copied!';
                setTimeout(() => { el.innerHTML = original; }, 2000);
            }
        }).catch((err) => {
            // Fallback to legacy method
            try {
                const textarea = document.createElement('textarea');
                textarea.value = url;
                textarea.style.position = 'fixed';
                textarea.style.left = '-9999px';
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                showToast('Link copied to clipboard!', 'success');
                if (el) {
                    const original = el.innerHTML;
                    el.innerHTML = 'Copied!';
                    setTimeout(() => { el.innerHTML = original; }, 2000);
                }
            } catch (e) {
                showToast('Failed to copy link', 'error');
            }
        });
    } else {
        // Legacy copy fallback
        try {
            const textarea = document.createElement('textarea');
            textarea.value = url;
            textarea.style.position = 'fixed';
            textarea.style.left = '-9999px';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            showToast('Link copied to clipboard!', 'success');
            if (el) {
                const original = el.innerHTML;
                el.innerHTML = 'Copied!';
                setTimeout(() => { el.innerHTML = original; }, 2000);
            }
        } catch (e) {
            showToast('Failed to copy link', 'error');
        }
    }
}

// Toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// Format file size
function formatFileSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

// Expose an initializer so this can be re-run after PJAX navigation
export function initUploads() {
    const fileInput = document.getElementById('file-input');
    const dropZone = document.querySelector('.drop-zone');

    function attachHandlers() {
        if (dropZone) {
            // Drag & drop handlers
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('drag-over');
            });

            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('drag-over');
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('drag-over');

                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleFileUpload(files[0]);
                }
            });
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    handleFileUpload(file);
                }
            });
        }
    }

    // Initialize handlers immediately
    attachHandlers();
}

// Modified handleFileUpload to use PJAX refresh instead of full reload
function handleFileUpload(file) {
    // Create progress UI
    const progressContainer = document.createElement('div');
    progressContainer.className = 'upload-progress';
    progressContainer.innerHTML = `
        <div class="upload-info">
            <span class="upload-filename">${file.name}</span>
            <span class="upload-size">${formatFileSize(file.size)}</span>
        </div>
        <div class="progress-bar-container">
            <div class="progress-bar" style="width: 0%"></div>
        </div>
        <div class="upload-status">
            <span class="upload-percent">0%</span>
            <button class="btn-cancel" onclick="cancelUpload()">Cancel</button>
        </div>
    `;

    const uploadSection = document.querySelector('.upload-section');
    uploadSection.appendChild(progressContainer);

    // Get privacy and browsable settings
    const isPublicCheckbox = document.querySelector('input[name="is_public"]');
    const isPublic = isPublicCheckbox ? isPublicCheckbox.checked : true;
    
    const isBrowsableCheckbox = document.querySelector('input[name="is_browsable"]');
    const isBrowsable = isBrowsableCheckbox ? isBrowsableCheckbox.checked : false;

    // Start chunked upload
    const uploader = new ChunkedUploader(file, {
        isPublic: isPublic,
        isBrowsable: isBrowsable,
        onProgress: (percent, uploaded, total) => {
            const progressBar = progressContainer.querySelector('.progress-bar');
            const percentText = progressContainer.querySelector('.upload-percent');

            progressBar.style.width = `${percent}%`;
            percentText.textContent = `${Math.round(percent)}% (${uploaded}/${total} chunks)`;
        },
        onComplete: (data) => {
            showToast(`File uploaded successfully: ${data.filename}`, 'success');
            setTimeout(() => {
                if (window.pjaxNavigate) {
                    // Refresh current page content via PJAX
                    window.pjaxNavigate(window.location.pathname, false);
                } else {
                    window.location.reload();
                }
            }, 900);
        },
        onError: (error) => {
            showToast(`Upload failed: ${error}`, 'error');
            progressContainer.remove();
        }
    });

    // Store uploader for cancel
    window.currentUploader = uploader;

    uploader.start();
}

function cancelUpload() {
    if (window.currentUploader) {
        window.currentUploader.abort();
        showToast('Upload cancelled', 'info');
    }
}

// Auto-init for non-module environments
if (typeof window !== 'undefined') {
    window.initUploads = () => {
        try { initUploads(); } catch (e) { /* ignore */ }
    };
}