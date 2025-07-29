# Magisto Video Downloader

An automated Python script to download all your videos from Magisto.com using Selenium WebDriver.

## Features

### ✅ **Smart Skip Detection**
- **Filename-based matching**: Uses video widget names for accurate skip detection
- **Truncation handling**: Handles Magisto's filename truncation (20+ character names)  
- **Multiple detection methods**: ID-based, mapping file, and widget name matching
- **Flexible truncation**: Supports various truncation lengths (15-25 characters)

### ✅ **Generic Name Re-download**
Always re-downloads videos with generic names for better naming:
- `Untitled`, `My video`, `New video`, `Video`
- `No title`, `No name`, `Bez názvu` (Czech)
- Any name ≤ 2 characters

### ✅ **Popup Handling**
- Automatically handles confirmation popups for older videos
- Multiple selector strategies for reliable popup detection

### ✅ **Browser Support**
- **Chrome** (recommended)
- **Brave** (experimental - may have ChromeDriver compatibility issues)

### ✅ **Robust Error Handling**
- Retry mechanisms for network issues
- Detailed logging for debugging
- Skip detection prevents duplicate downloads

## Requirements

- Python 3.7+
- Chrome or Brave browser
- Internet connection

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Nowass/magisto-collector
cd magisto-collector
```

2. **Install dependencies:**
```bash
pip install selenium webdriver-manager
```

## Configuration

Edit the configuration section in `magisto_downloader.py`:

```python
# === CONFIGURATION ===
MAGISTO_EMAIL = ""  # Leave empty for manual login
MAGISTO_PASSWORD = ""  # Leave empty for manual login  
DOWNLOAD_DIR = "/path/to/your/download/folder"  # Adjust to your needs
BROWSER_TYPE = "chrome"  # "chrome" or "brave"

# Timing settings
WAIT_AFTER_DOWNLOAD = 10  # seconds to wait after clicking download
LOGIN_TIMEOUT = 20  # timeout for login elements
DOWNLOAD_TIMEOUT = 15  # timeout for download button
```

## Usage

### Main Script
```bash
python magisto_downloader.py
```

### Test Single Video
```bash
python test_single_download.py
```

## How It Works

### 1. **Login Process**
- Opens Magisto login page
- Supports manual login (recommended)
- Fallback to automatic login if credentials provided

### 2. **Video Discovery**
- Navigates to video library
- Performs infinite scrolling to load all videos
- Collects all video URLs using multiple selectors

### 3. **Smart Download Process**
For each video:
1. **Skip Detection**: Checks if already downloaded using:
   - Video ID matching in filenames
   - URL mapping file lookup
   - Widget name extraction and matching
   - Truncation-aware filename matching

2. **Generic Name Handling**: Always downloads videos with generic names

3. **Download Execution**:
   - Clicks download button
   - Handles confirmation popups
   - Saves download mapping for future runs

### 4. **Skip Detection Logic**

#### Method 1: Video ID Matching
Searches for files containing the video ID in the filename.

#### Method 2: URL Mapping File  
Uses `download_mapping.txt` to track URL → filename relationships.

#### Method 3: Widget Name Matching (Enhanced)
- **3a**: Exact match for short names with quality suffixes (`_FULL_HD`, `_HD`, etc.)
- **3b**: Wildcard matching for full-length names
- **3c**: 20-character truncation detection (Magisto's standard)
- **3d**: Flexible truncation detection (15-25 characters)

#### Generic Name Override
Videos with generic names always bypass skip detection:
```python
generic_names = ['untitled', 'my video', 'new video', 'video', 
                 'no title', 'no name', 'bez názvu']
```

## File Structure

```
magisto-collector/
├── magisto_downloader.py      # Main downloader script
├── test_single_download.py    # Single video test script  
├── README.md                  # This file
├── magisto_downloader.log     # Execution log
└── downloads/                 # Created automatically
    ├── download_mapping.txt   # URL → filename mapping
    └── *.mp4                  # Downloaded videos
```

## Advanced Features

### Filename Truncation Handling
Magisto truncates long video names to ~20 characters and adds quality suffixes. The script handles this by:

1. **Detecting long names** (>20 characters)
2. **Testing truncated versions** at 20 characters
3. **Flexible length testing** (15-25 character ranges)
4. **Quality suffix removal** for accurate matching

Example:
- Original: `"my-very-long-video-name-from-vacation-2025"`
- Magisto saves as: `"my-very-long-video-_FULL_HD.mp4"`
- Script detects match using truncation logic

### Quality Suffix Support
Handles all Magisto quality formats:
- `_FULL_HD.mp4`
- `_HD.mp4` 
- `_HQ.mp4`
- `_FULL.mp4`

### Mapping File Format
The `download_mapping.txt` file format:
```
https://www.magisto.com/video/ABC123|video_name_FULL_HD.mp4
https://www.magisto.com/video/XYZ789|another_video_HD.mp4
```

## Troubleshooting

### Browser Issues
- **Chrome recommended**: More stable than Brave
- **ChromeDriver auto-managed**: Uses webdriver-manager for updates
- **Brave compatibility**: May have version conflicts

### Login Problems
- **Manual login preferred**: More reliable than automatic
- **Session persistence**: Checks if already logged in
- **Multiple login indicators**: Various selectors for detection

### Download Issues
- **Popup handling**: Automatic confirmation for older videos
- **Timeout adjustments**: Modify timeout values if needed
- **Network issues**: Script includes retry mechanisms

### Skip Detection Problems
- **Check download directory**: Ensure `DOWNLOAD_DIR` is correct
- **Mapping file**: Verify `download_mapping.txt` exists and is readable
- **Debug logging**: Check logs for skip detection details

## Logging

The script provides detailed logging:
- **INFO**: General progress and status
- **WARNING**: Non-critical issues
- **ERROR**: Critical problems

Log files: `magisto_downloader.log` and `test_single_download.log`

## Statistics

After completion, the script shows:
- **📥 Newly downloaded**: Count of new videos
- **⏭️ Skipped**: Count of already existing videos  
- **❌ Errors**: Count of failed downloads
- **📊 Total processed**: Overall statistics
- **💾 Total size**: Disk usage of all videos

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for personal use. Please respect Magisto's terms of service.

## Disclaimer

This tool is for downloading your own videos from Magisto. Users are responsible for complying with Magisto's terms of service and applicable laws.

1. **Edit the script configuration** in `magisto_downloader.py`:
   ```python
   MAGISTO_EMAIL = ""  # Optional - leave empty for manual login
   MAGISTO_PASSWORD = ""  # Optional - leave empty for manual login  
   DOWNLOAD_DIR = "/path/to/your/download/directory"
   BROWSER_TYPE = "chrome"  # Use Chrome (recommended)
   ```

   **Note:** You can now leave credentials empty and log in manually in the browser window!

2. **Adjust timeouts if needed:**
   - `WAIT_AFTER_DOWNLOAD`: Time to wait after clicking download
   - `LOGIN_TIMEOUT`: Timeout for login elements
   - `DOWNLOAD_TIMEOUT`: Timeout for download button

## 🎯 Usage

Simply run the script:
```bash
python magisto_downloader.py
```

**Manual Login Process:**
1. The script opens Chrome browser with Magisto login page
2. **Manually log in** to your Magisto account in the browser
3. **Press ENTER** in the terminal when login is complete
4. Script continues with video discovery and download

**Benefits of Manual Login:**
- ✅ **No credentials in code** - much more secure
- ✅ **Supports 2FA** and other security measures  
- ✅ **Always works** even if Magisto changes login process
- ✅ **You stay in control** of the authentication

The script will:
1. Log into your Magisto account
2. Navigate to your videos page
3. Scroll through all videos to load them
4. Visit each video and trigger download
5. Log progress and errors to both console and `magisto_downloader.log`

## 📊 Logging

The script creates detailed logs in `magisto_downloader.log` including:
- Login attempts and results
- Video discovery process
- Download success/failure for each video
- Error messages and debugging information

## 🛡️ Security Notes

- **Credentials are stored locally** in the script variables
- **No external data transmission** except to Magisto.com
- **No API keys required**
- **Anti-detection measures** to appear as regular browser usage

## 🔍 Troubleshooting

### Common Issues:

1. **Login fails**: 
   - Check your credentials
   - Magisto may have changed their login page structure
   - Check the logs for specific error messages

2. **No videos found**:
   - The script tries multiple URL patterns for the videos page
   - Check if you're logged in properly
   - Magisto may have changed their page structure

3. **Download button not found**:
   - The script uses multiple selectors to find download buttons
   - Some videos may not have download buttons available
   - Check the video page manually to see if download is available

4. **Browser issues**:
   - The script uses **Chrome browser** with automatic ChromeDriver management
   - Chrome provides the best compatibility with WebDriver
   - If using Brave: Note that Brave versions may not be compatible with available ChromeDrivers
   - The script automatically downloads the correct ChromeDriver version for Chrome

### Debug Mode:

To see more detailed output, you can modify the logging level:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## 📌 Possible Extensions

- [ ] CSV logging of downloaded videos with metadata
- [ ] Detection of already-downloaded videos to skip duplicates
- [ ] Resume functionality for interrupted sessions
- [ ] Headless browser mode for server environments
- [ ] Docker container for easy deployment
- [ ] GUI interface for non-technical users
- [ ] Video quality selection
- [ ] Batch processing with multiple accounts

## 🤝 Contributing

Feel free to open issues or submit pull requests for improvements!

## 📄 License

This project is for educational and personal backup purposes only. Please respect Magisto's terms of service.
