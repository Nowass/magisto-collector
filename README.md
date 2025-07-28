# 🧠 Magisto Video Downloader

This project was created to automate the **backup of all videos created in the online editor [Magisto.com](https://www.magisto.com)**. The user has over 100 videos in their account, but Magisto does not offer a bulk download option.

## ⚙️ Features

- **Manual login support** - No need to store credentials in code!
- **Chrome browser support** with automatic ChromeDriver management
- **Automated login process** with robust error handling
- **Smart video discovery** with multiple selector fallbacks
- **Infinite scrolling** to load all videos from lazy-loaded content
- **Bulk download** with progress tracking and error recovery
- **Comprehensive logging** to file and console
- **Anti-detection measures** to prevent bot detection
- **Configurable timeouts** and retry mechanisms

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Nowass/magisto-collector.git
   cd magisto-collector
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Linux/Mac
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Google Chrome (recommended):**
   ```bash
   # For Ubuntu/Debian:
   wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
   echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
   sudo apt update
   sudo apt install -y google-chrome-stable
   ```
   
   *Or download from [chrome.google.com](https://www.google.com/chrome/) for other systems.*

## 🔧 Configuration

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
