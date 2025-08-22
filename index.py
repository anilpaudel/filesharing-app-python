import http.server
import socketserver
import os
import urllib
import io
import socket
import threading
import time
from urllib.parse import parse_qs, urlparse

PORT = 8303
DIRECTORY = "shared"
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB limit
CHUNK_SIZE = 8192  # 8KB chunks

def get_local_ip():
    """Detect local LAN IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"
    return ip

class FileServerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
        self.upload_progress = {}

    def end_headers(self):
        """Add performance headers"""
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def send_file_streaming(self, filepath):
        """Stream file in chunks instead of loading entirely into memory"""
        try:
            file_size = os.path.getsize(filepath)
            self.send_response(200)
            self.send_header('Content-Length', str(file_size))
            self.send_header('Accept-Ranges', 'bytes')
            
            # Get file extension for content type
            ext = os.path.splitext(filepath)[1].lower()
            if ext in ['.txt', '.py', '.js', '.css', '.html', '.json']:
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
            elif ext in ['.jpg', '.jpeg']:
                self.send_header('Content-Type', 'image/jpeg')
            elif ext == '.png':
                self.send_header('Content-Type', 'image/png')
            elif ext == '.gif':
                self.send_header('Content-Type', 'image/gif')
            elif ext == '.pdf':
                self.send_header('Content-Type', 'application/pdf')
            else:
                self.send_header('Content-Type', 'application/octet-stream')
            
            self.end_headers()
            
            # Stream file in chunks
            with open(filepath, 'rb') as f:
                bytes_sent = 0
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                        bytes_sent += len(chunk)
                        self.wfile.flush()  # Ensure data is sent immediately
                    except (BrokenPipeError, ConnectionResetError):
                        # Client disconnected, stop sending
                        break
                    
        except Exception as e:
            if not self.wfile.closed:
                self.send_error(500, f"Error serving file: {str(e)}")

    def do_GET(self):
        """Handle GET requests with streaming for files"""
        parsed_path = urlparse(self.path)
        path = urllib.parse.unquote(parsed_path.path)
        
        # Handle root path
        if path == '/':
            return self.list_directory(DIRECTORY)
        
        # Handle file requests
        filepath = os.path.join(DIRECTORY, path.lstrip('/'))
        if os.path.isfile(filepath):
            return self.send_file_streaming(filepath)
        elif os.path.isdir(filepath):
            return self.list_directory(filepath)
        else:
            self.send_error(404, "File not found")

    def list_directory(self, path):
        """Generate a modern, organized file browser UI with file management features"""
        try:
            file_list = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None

        # Sort files: directories first, then files, both alphabetically
        dirs = []
        files = []
        for name in file_list:
            fullname = os.path.join(path, name)
            if os.path.isdir(fullname):
                dirs.append(name)
            else:
                files.append(name)
        
        dirs.sort(key=lambda a: a.lower())
        files.sort(key=lambda a: a.lower())
        sorted_list = dirs + files

        html = []
        html.append("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>📂 Local File Server</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    overflow: hidden;
                }
                
                .header {
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }
                
                .header h1 {
                    font-size: 2.5em;
                    margin-bottom: 10px;
                    font-weight: 300;
                }
                
                .header p {
                    opacity: 0.9;
                    font-size: 1.1em;
                }
                
                .content {
                    padding: 30px;
                }
                
                .section {
                    background: #f8f9fa;
                    border-radius: 15px;
                    padding: 25px;
                    margin-bottom: 25px;
                    border: 1px solid #e9ecef;
                }
                
                .section h2 {
                    color: #495057;
                    margin-bottom: 20px;
                    font-size: 1.5em;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .file-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 15px;
                }
                
                .file-card {
                    background: white;
                    border-radius: 12px;
                    padding: 20px;
                    border: 2px solid #e9ecef;
                    transition: all 0.3s ease;
                    position: relative;
                }
                
                .file-card:hover {
                    border-color: #4facfe;
                    transform: translateY(-2px);
                    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                }
                
                .file-icon {
                    font-size: 2em;
                    margin-bottom: 10px;
                    display: block;
                }
                
                .file-name {
                    font-weight: 600;
                    color: #495057;
                    margin-bottom: 8px;
                    word-break: break-word;
                }
                
                .file-size {
                    color: #6c757d;
                    font-size: 0.9em;
                    margin-bottom: 15px;
                }
                
                .file-actions {
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                }
                
                .btn {
                    padding: 8px 16px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 0.9em;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                    gap: 5px;
                }
                
                .btn-primary {
                    background: #4facfe;
                    color: white;
                }
                
                .btn-primary:hover {
                    background: #3a8bfd;
                    transform: translateY(-1px);
                }
                
                .btn-danger {
                    background: #dc3545;
                    color: white;
                }
                
                .btn-danger:hover {
                    background: #c82333;
                    transform: translateY(-1px);
                }
                
                .btn-warning {
                    background: #ffc107;
                    color: #212529;
                }
                
                .btn-warning:hover {
                    background: #e0a800;
                    transform: translateY(-1px);
                }
                
                .btn-small {
                    padding: 6px 12px;
                    font-size: 0.8em;
                }
                
                .upload-area {
                    border: 3px dashed #dee2e6;
                    border-radius: 15px;
                    padding: 40px;
                    text-align: center;
                    transition: all 0.3s ease;
                    background: white;
                }
                
                .upload-area:hover {
                    border-color: #4facfe;
                    background: #f8f9ff;
                }
                
                .upload-area.dragover {
                    border-color: #4facfe;
                    background: #e3f2fd;
                }
                
                .file-input {
                    display: none;
                }
                
                .upload-btn {
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 10px;
                    font-size: 1.1em;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    margin-top: 15px;
                }
                
                .upload-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 25px rgba(79, 172, 254, 0.3);
                }
                
                .upload-btn:disabled {
                    background: #6c757d;
                    cursor: not-allowed;
                    transform: none;
                    box-shadow: none;
                }
                
                .progress-container {
                    margin-top: 20px;
                    display: none;
                }
                
                .progress-bar {
                    width: 100%;
                    height: 8px;
                    background: #e9ecef;
                    border-radius: 4px;
                    overflow: hidden;
                    margin-bottom: 10px;
                }
                
                .progress-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #4facfe, #00f2fe);
                    width: 0%;
                    transition: width 0.3s ease;
                }
                
                .status {
                    padding: 15px;
                    border-radius: 10px;
                    margin-top: 15px;
                    font-weight: 500;
                }
                
                .status.success {
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }
                
                .status.error {
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }
                
                .status.info {
                    background: #d1ecf1;
                    color: #0c5460;
                    border: 1px solid #bee5eb;
                }
                
                .empty-state {
                    text-align: center;
                    padding: 60px 20px;
                    color: #6c757d;
                }
                
                .empty-state .icon {
                    font-size: 4em;
                    margin-bottom: 20px;
                    opacity: 0.5;
                }
                
                .modal {
                    display: none;
                    position: fixed;
                    z-index: 1000;
                    left: 0;
                    top: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0,0,0,0.5);
                }
                
                .modal-content {
                    background-color: white;
                    margin: 15% auto;
                    padding: 30px;
                    border-radius: 15px;
                    width: 90%;
                    max-width: 500px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.2);
                }
                
                .modal h3 {
                    margin-bottom: 20px;
                    color: #495057;
                }
                
                .modal input {
                    width: 100%;
                    padding: 12px;
                    border: 2px solid #e9ecef;
                    border-radius: 8px;
                    font-size: 1em;
                    margin-bottom: 20px;
                }
                
                .modal input:focus {
                    outline: none;
                    border-color: #4facfe;
                }
                
                .modal-buttons {
                    display: flex;
                    gap: 10px;
                    justify-content: flex-end;
                }
                
                @media (max-width: 768px) {
                    .file-grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .header h1 {
                        font-size: 2em;
                    }
                    
                    .content {
                        padding: 20px;
                    }
                }
            </style>
        </head>
        <body>
        """)
        
        html.append(f"""
        <div class="container">
            <div class="header">
                <h1>📂 Local File Server</h1>
                <p>Share and manage your files easily</p>
            </div>
            
            <div class="content">
                <div class="section">
                    <h2>📁 Files & Folders</h2>
        """)

        if not sorted_list:
            html.append("""
                    <div class="empty-state">
                        <div class="icon">📁</div>
                        <h3>No files available</h3>
                        <p>Upload some files to get started!</p>
                    </div>
            """)
        else:
            html.append('<div class="file-grid">')
            
            for name in sorted_list:
                fullname = os.path.join(path, name)
                display_name = name
                is_dir = os.path.isdir(fullname)
                
                # Get file info
                try:
                    if is_dir:
                        size_str = "📁 Directory"
                        icon = "📁"
                        actions = f"""
                            <button class="btn btn-primary btn-small" onclick="openFolder('{urllib.parse.quote(name)}/')">
                                📂 Open
                            </button>
                        """
                    else:
                        size = os.path.getsize(fullname)
                        size_str = f"📄 {self.format_file_size(size)}"
                        icon = self.get_file_icon(name)
                        actions = f"""
                            <a href="{urllib.parse.quote(name)}" class="btn btn-primary btn-small">⬇️ Download</a>
                            <button class="btn btn-warning btn-small" onclick="renameFile('{name}')">✏️ Rename</button>
                            <button class="btn btn-danger btn-small" onclick="deleteFile('{name}')">🗑️ Delete</button>
                        """
                except:
                    size_str = "N/A"
                    icon = "📄"
                    actions = ""
                
                html.append(f"""
                    <div class="file-card">
                        <span class="file-icon">{icon}</span>
                        <div class="file-name">{display_name}</div>
                        <div class="file-size">{size_str}</div>
                        <div class="file-actions">
                            {actions}
                        </div>
                    </div>
                """)
            
            html.append('</div>')

        html.append("""
                </div>
                
                <div class="section">
                    <h2>⬆️ Upload Files</h2>
                    <div class="upload-area" id="uploadArea">
                        <div class="icon">📤</div>
                        <h3>Drag & Drop Files Here</h3>
                        <p>or click to select files</p>
                        <input type="file" id="fileInput" multiple class="file-input" />
                        <button class="upload-btn" onclick="document.getElementById('fileInput').click()">
                            Choose Files
                        </button>
                    </div>
                    <div class="progress-container" id="progressContainer">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progressFill"></div>
                        </div>
                        <div id="progressText">0%</div>
                    </div>
                    <div id="status"></div>
                </div>
            </div>
        </div>
        
        <!-- Rename Modal -->
        <div id="renameModal" class="modal">
            <div class="modal-content">
                <h3>✏️ Rename File</h3>
                <input type="text" id="newFileName" placeholder="Enter new file name">
                <div class="modal-buttons">
                    <button class="btn" onclick="closeModal('renameModal')">Cancel</button>
                    <button class="btn btn-primary" onclick="confirmRename()">Rename</button>
                </div>
            </div>
        </div>
        
        <!-- Delete Confirmation Modal -->
        <div id="deleteModal" class="modal">
            <div class="modal-content">
                <h3>🗑️ Delete File</h3>
                <p>Are you sure you want to delete "<span id="deleteFileName"></span>"?</p>
                <p style="color: #dc3545; font-size: 0.9em;">This action cannot be undone.</p>
                <div class="modal-buttons">
                    <button class="btn" onclick="closeModal('deleteModal')">Cancel</button>
                    <button class="btn btn-danger" onclick="confirmDelete()">Delete</button>
                </div>
            </div>
        </div>
        """)

        # JavaScript for enhanced functionality
        html.append("""
        <script>
        let currentFile = '';
        
        // Upload functionality
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const status = document.getElementById('status');
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                uploadFiles(files);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                uploadFiles(e.target.files);
            }
        });
        
        async function uploadFiles(files) {
            progressContainer.style.display = 'block';
            showStatus('Uploading files...', 'info');
            
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const progress = ((i + 1) / files.length) * 100;
                        progressFill.style.width = progress + '%';
                        progressText.textContent = Math.round(progress) + '%';
                    } else {
                        throw new Error('Upload failed');
                    }
                } catch (error) {
                    showStatus('Upload failed: ' + error.message, 'error');
                    progressContainer.style.display = 'none';
                    return;
                }
            }
            
            showStatus('All files uploaded successfully!', 'success');
            progressContainer.style.display = 'none';
            setTimeout(() => location.reload(), 1500);
        }
        
        // File management functions
        function openFolder(path) {
            window.location.href = path;
        }
        
        function renameFile(filename) {
            currentFile = filename;
            document.getElementById('newFileName').value = filename;
            document.getElementById('renameModal').style.display = 'block';
        }
        
        function deleteFile(filename) {
            currentFile = filename;
            document.getElementById('deleteFileName').textContent = filename;
            document.getElementById('deleteModal').style.display = 'block';
        }
        
        async function confirmRename() {
            const newName = document.getElementById('newFileName').value.trim();
            if (!newName) {
                showStatus('Please enter a file name', 'error');
                return;
            }
            
            try {
                const response = await fetch('/rename', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `old_name=${encodeURIComponent(currentFile)}&new_name=${encodeURIComponent(newName)}`
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    showStatus('File renamed successfully!', 'success');
                    closeModal('renameModal');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showStatus('Rename failed: ' + result.message, 'error');
                }
            } catch (error) {
                showStatus('Rename failed: ' + error.message, 'error');
            }
        }
        
        async function confirmDelete() {
            try {
                const response = await fetch('/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `filename=${encodeURIComponent(currentFile)}`
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    showStatus('File deleted successfully!', 'success');
                    closeModal('deleteModal');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showStatus('Delete failed: ' + result.message, 'error');
                }
            } catch (error) {
                showStatus('Delete failed: ' + error.message, 'error');
            }
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        function showStatus(message, type) {
            status.textContent = message;
            status.className = 'status ' + type;
        }
        
        // Close modals when clicking outside
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
            }
        }
        </script>
        </body>
        </html>
        """)

        encoded = "\n".join(html).encode("utf-8", "surrogateescape")

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        
        try:
            self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            pass
        return None

    def format_file_size(self, size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def get_file_icon(self, filename):
        """Get appropriate icon for file type"""
        ext = os.path.splitext(filename)[1].lower()
        
        # Image files
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']:
            return "🖼️"
        # Video files
        elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']:
            return "🎥"
        # Audio files
        elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma']:
            return "🎵"
        # Document files
        elif ext in ['.pdf']:
            return "📄"
        elif ext in ['.doc', '.docx']:
            return "📝"
        elif ext in ['.xls', '.xlsx']:
            return "📊"
        elif ext in ['.ppt', '.pptx']:
            return "📈"
        # Code files
        elif ext in ['.py', '.js', '.html', '.css', '.php', '.java', '.cpp', '.c', '.h']:
            return "💻"
        # Archive files
        elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            return "📦"
        # Text files
        elif ext in ['.txt', '.md', '.log', '.csv']:
            return "📄"
        # Executable files
        elif ext in ['.exe', '.msi', '.deb', '.rpm', '.dmg']:
            return "⚙️"
        else:
            return "📄"

    def do_POST(self):
        """Handle file uploads with chunked processing"""
        if self.path == '/upload':
            return self.handle_upload()
        elif self.path == '/delete':
            return self.handle_delete()
        elif self.path == '/rename':
            return self.handle_rename()
        
        # Fallback to old multipart handling
        return self.handle_multipart_upload()

    def do_DELETE(self):
        """Handle DELETE requests for file deletion"""
        return self.handle_delete()

    def do_PUT(self):
        """Handle PUT requests for file renaming"""
        return self.handle_rename()

    def handle_upload(self):
        """Handle single file upload with progress tracking"""
        content_length = int(self.headers.get("Content-Length", 0))
        
        if content_length > MAX_UPLOAD_SIZE:
            self.send_response(413, "File too large")
            self.end_headers()
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_response(400, "Invalid upload request")
            self.end_headers()
            return

        try:
            boundary = content_type.split("boundary=")[-1].encode()
            body = self.rfile.read(content_length)
            
            parts = body.split(b"--" + boundary)
            for part in parts:
                if b"Content-Disposition" in part and b"filename=" in part:
                    try:
                        header, file_data = part.split(b"\r\n\r\n", 1)
                    except ValueError:
                        continue
                    
                    file_data = file_data.rsplit(b"\r\n", 1)[0]
                    header_str = header.decode(errors="ignore")
                    
                    filename_marker = 'filename="'
                    filename_start = header_str.find(filename_marker)
                    if filename_start != -1:
                        filename_start += len(filename_marker)
                        filename_end = header_str.find('"', filename_start)
                        filename = header_str[filename_start:filename_end]
                        
                        if filename:
                            filepath = os.path.join(DIRECTORY, os.path.basename(filename))
                            with open(filepath, "wb") as f:
                                f.write(file_data)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "success"}')
            
        except Exception as e:
            self.send_response(500, "Upload failed")
            self.end_headers()
            self.wfile.write(f'{{"status": "error", "message": "{str(e)}"}}'.encode())

    def handle_delete(self):
        """Handle file deletion"""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            body = self.rfile.read(content_length).decode('utf-8')
            data = urllib.parse.parse_qs(body)
            filename = data.get('filename', [''])[0]
        else:
            # Try to get filename from query string
            parsed_url = urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            filename = query_params.get('filename', [''])[0]

        if not filename:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "error", "message": "No filename provided"}')
            return

        try:
            filepath = os.path.join(DIRECTORY, filename)
            if os.path.exists(filepath):
                if os.path.isdir(filepath):
                    os.rmdir(filepath)  # Remove empty directory
                else:
                    os.remove(filepath)  # Remove file
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "success", "message": "File deleted successfully"}')
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "error", "message": "File not found"}')
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(f'{{"status": "error", "message": "{str(e)}"}}'.encode())

    def handle_rename(self):
        """Handle file renaming"""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = urllib.parse.parse_qs(body)
        
        old_name = data.get('old_name', [''])[0]
        new_name = data.get('new_name', [''])[0]

        if not old_name or not new_name:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "error", "message": "Both old_name and new_name required"}')
            return

        try:
            old_path = os.path.join(DIRECTORY, old_name)
            new_path = os.path.join(DIRECTORY, new_name)
            
            if os.path.exists(old_path):
                if os.path.exists(new_path):
                    self.send_response(409)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "error", "message": "File with new name already exists"}')
                    return
                
                os.rename(old_path, new_path)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "success", "message": "File renamed successfully"}')
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "error", "message": "File not found"}')
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(f'{{"status": "error", "message": "{str(e)}"}}'.encode())

    def handle_multipart_upload(self):
        """Legacy multipart upload handling"""
        content_length = int(self.headers.get("Content-Length", 0))
        content_type = self.headers.get("Content-Type", "")

        if "multipart/form-data" not in content_type:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid upload request")
            return

        boundary = content_type.split("boundary=")[-1].encode()
        body = self.rfile.read(content_length)

        parts = body.split(b"--" + boundary)
        for part in parts:
            if b"Content-Disposition" in part and b"filename=" in part:
                try:
                    header, file_data = part.split(b"\r\n\r\n", 1)
                except ValueError:
                    continue
                file_data = file_data.rsplit(b"\r\n", 1)[0]
                header_str = header.decode(errors="ignore")

                filename_marker = 'filename="'
                filename_start = header_str.find(filename_marker)
                if filename_start != -1:
                    filename_start += len(filename_marker)
                    filename_end = header_str.find('"', filename_start)
                    filename = header_str[filename_start:filename_end]
                    if filename:
                        filepath = os.path.join(DIRECTORY, os.path.basename(filename))
                        with open(filepath, "wb") as f:
                            f.write(file_data)

        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

if __name__ == "__main__":
    os.makedirs(DIRECTORY, exist_ok=True)
    ip = get_local_ip()
    
    # Create a simple threaded server since ThreadingHTTPServer isn't available
    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
    
    print("🚀 Serving '{DIRECTORY}' with threading support")
    print(f"📍 Local:   http://localhost:{PORT}")
    print(f"🌍 Network: http://{ip}:{PORT}")
    print(f"📊 Max upload size: {MAX_UPLOAD_SIZE // (1024*1024)}MB")
    print(f"⚡ Chunk size: {CHUNK_SIZE // 1024}KB")
    print("Press Ctrl+C to stop the server")
    
    with ThreadedTCPServer(("", PORT), FileServerHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")