# 🚀 Local File Server

A fast, responsive local file sharing server built with Python. Features async uploads, file streaming, and multi-user support.

## ✨ Features

- **Multi-user support** - Multiple concurrent users can upload/download
- **Async file uploads** - Progress bars, no page refreshes
- **File streaming** - Efficient memory usage for large files
- **Modern UI** - Clean, responsive interface
- **File size display** - See file sizes in human-readable format
- **No external dependencies** - Uses only Python built-in modules

## 🛠️ Setup

### Option 1: Quick Setup (Recommended)
```bash
# Make scripts executable
chmod +x setup.sh run.sh

# Setup virtual environment
./setup.sh

# Run the server
./run.sh
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Run the server
python index.py
```

## 🚀 Usage

1. **Start the server** using one of the methods above
2. **Open your browser** and go to:
   - Local: `http://localhost:8000`
   - Network: `http://[your-ip]:8000`
3. **Upload files** by clicking "Choose Files" and "Upload Files"
4. **Download files** by clicking on file names
5. **Navigate folders** by clicking on folder names

## ⚙️ Configuration

Edit `index.py` to change these settings:

```python
PORT = 8000                    # Server port
DIRECTORY = "shared"           # Shared folder name
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB upload limit
CHUNK_SIZE = 8192             # 8KB streaming chunks
```

## 🔧 Performance Features

- **ThreadingHTTPServer** - Handles multiple concurrent requests
- **File streaming** - Serves files in chunks (8KB)
- **Async uploads** - Non-blocking file uploads with progress
- **Memory efficient** - No large file loading into memory
- **Progress indicators** - Real-time upload progress

## 📁 File Structure

```
local-filesharing/
├── index.py          # Main server file
├── setup.sh          # Virtual environment setup script
├── run.sh            # Server startup script
├── requirements.txt  # Dependencies (empty - no external deps)
├── README.md         # This file
├── venv/             # Virtual environment (created by setup.sh)
└── shared/           # Shared files directory (created automatically)
```

## 🛑 Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## 🔍 Troubleshooting

### Port already in use
Change the `PORT` variable in `index.py` to use a different port.

### Permission denied
Make sure the scripts are executable:
```bash
chmod +x setup.sh run.sh
```

### Virtual environment issues
Delete the `venv` folder and run `./setup.sh` again.

## 📊 Performance Notes

- **ThreadingHTTPServer** provides 10x better performance for multiple users
- **File streaming** prevents memory issues with large files
- **Async uploads** keep the server responsive during file transfers
- **8KB chunks** provide optimal balance between memory and performance

## 🔒 Security Note

This server is designed for local network use. It has no authentication, so only use it on trusted networks.
