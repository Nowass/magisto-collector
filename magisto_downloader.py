import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import platform
import os.path

# === CONFIGURATION ===
# Credentials (leave empty for manual login)
MAGISTO_EMAIL = ""  # you can leave empty for manual login
MAGISTO_PASSWORD = ""  # you can leave empty for manual login
DOWNLOAD_DIR = "/home/nowass/Videos/Magisto"  # adjust to your needs

# Browser settings - "chrome" or "brave"
# WARNING: Brave may have issues with ChromeDriver version - we recommend Chrome
BROWSER_TYPE = "chrome"  # change to "brave" if you have compatible version

WAIT_AFTER_DOWNLOAD = 10  # seconds to wait after clicking "Download"
LOGIN_TIMEOUT = 20  # timeout for finding elements during login
DOWNLOAD_TIMEOUT = 15  # timeout for finding download button

# === Logging setup ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('magisto_downloader.log'),
        logging.StreamHandler()
    ]
)

# === Browser setup ===
def get_brave_binary_path():
    """Find path to Brave browser on different OS"""
    system = platform.system()
    
    if system == "Linux":
        brave_paths = [
            "/usr/bin/brave-browser",
            "/usr/bin/brave",
            "/snap/brave/current/usr/bin/brave",
            "/var/lib/flatpak/app/com.brave.Browser/current/active/files/brave",
            "/usr/local/bin/brave-browser",
            "/opt/brave.com/brave/brave-browser"
        ]
    elif system == "Darwin":  # macOS
        brave_paths = [
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
        ]
    elif system == "Windows":
        brave_paths = [
            "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            os.path.expanduser("~\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe")
        ]
    else:
        return None
    
    for path in brave_paths:
        if os.path.exists(path):
            return path
    
    return None

def setup_browser_driver():
    """Setup browser (Chrome or Brave) with optimized options"""
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.notifications": 2  # block notifications
    })
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Create download folder
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    if BROWSER_TYPE.lower() == "brave":
        # Setup for Brave browser
        brave_path = get_brave_binary_path()
        if brave_path:
            options.binary_location = brave_path
            logging.info(f"Trying to use Brave browser: {brave_path}")
            logging.warning("WARNING: Brave may have issues with ChromeDriver version!")
            logging.info("If errors occur, change BROWSER_TYPE to 'chrome'")
        else:
            logging.error("Brave browser not found! Switching to Chrome...")
            logging.info("Install Brave or change BROWSER_TYPE to 'chrome'")
    else:
        logging.info("Using Chrome browser")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logging.info("Browser successfully started!")
        return driver
    except Exception as e:
        logging.error(f"Error starting browser: {e}")
        if BROWSER_TYPE.lower() == "brave":
            logging.error("Problem with Brave browser - probably incompatible ChromeDriver version")
            logging.info("SOLUTION: Change BROWSER_TYPE to 'chrome' in configuration")
            logging.info("Or install older Brave version or newer ChromeDriver version")
        raise

try:
    driver = setup_browser_driver()
    wait = WebDriverWait(driver, LOGIN_TIMEOUT)
except Exception as e:
    logging.error("Cannot start browser. Exiting script.")
    exit(1)

# === Helper functions ===
def check_if_logged_in():
    """Check if user is logged in"""
    try:
        # Check various login indicators
        login_indicators = [
            # Positive indicators (when logged in)
            "//a[contains(@href, '/video/mine')]",
            "//a[contains(@href, '/my-movies')]",
            "//button[contains(text(), 'Profile')]",
            "//div[contains(@class, 'user-menu')]",
            "[data-test-id*='user']",
            ".user-avatar",
            "//a[contains(text(), 'My Videos')]",
            "//a[contains(text(), 'Dashboard')]"
        ]
        
        for indicator in login_indicators:
            try:
                if indicator.startswith("//"):
                    element = driver.find_element(By.XPATH, indicator)
                else:
                    element = driver.find_element(By.CSS_SELECTOR, indicator)
                if element:
                    logging.info(f"   → Found login indicator: {indicator}")
                    return True
            except:
                continue
        
        # Check URL - if redirected to dashboard or similar
        current_url = driver.current_url
        logged_in_patterns = ['/dashboard', '/video/', '/my-movies', '/profile']
        
        for pattern in logged_in_patterns:
            if pattern in current_url:
                logging.info(f"   → URL indicates login: {current_url}")
                return True
        
        return False
        
    except Exception as e:
        logging.warning(f"Error checking login status: {e}")
        return False

# === STEP 1: Login (Manual Login Support) ===
def login_to_magisto():
    """Login to Magisto with manual login support"""
    logging.info("[1/5] Opening Magisto login page...")
    
    try:
        # Use direct login URL for manual login
        driver.get("https://www.magisto.com/connect?q_offer_info=eyJpZCI6IjE0MDA1NDcwMjY5NzE3ODc1MzkiLCJleHBpcmF0aW9uIjoxNzUzNjgyMTc3ODQ4fQ%3D%3D")
        
        logging.info("🔐 MANUAL LOGIN:")
        logging.info("   → Opened login page")
        logging.info("   → Please log in manually in the browser")
        logging.info("   → Press ENTER in terminal after login to continue...")
        
        # Wait for manual confirmation
        input("Press ENTER after completing login...")
        
        # Check if user is logged in
        logged_in = check_if_logged_in()
        
        if logged_in:
            logging.info("✅ Login successful!")
            return True
        else:
            logging.error("❌ Login seems to have failed")
            
            # Try automatic login as fallback
            logging.info("🔄 Trying automatic login...")
            return attempt_automatic_login()
            
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return False

def attempt_automatic_login():
    """Attempt automatic login as fallback"""
    
    # Check if credentials are provided
    if not MAGISTO_EMAIL or not MAGISTO_PASSWORD:
        logging.warning("❌ Credentials not set - automatic login not possible")
        logging.info("💡 Set MAGISTO_EMAIL and MAGISTO_PASSWORD in configuration for automatic login")
        return False
    
    try:
        logging.info("Looking for login form...")
        
        # Search for login button or form
        login_selectors = [
            "//a[contains(text(),'Log in')]",
            "//a[contains(text(),'Sign in')]",
            "//button[contains(text(),'Log in')]",
            "//button[contains(text(),'Sign in')]",
            ".login-btn",
            "[data-test-id='login-button']",
            "input[name='email']"  # Direct search for email field
        ]
        
        login_element = None
        for selector in login_selectors:
            try:
                if selector.startswith("//"):
                    login_element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                else:
                    login_element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                break
            except TimeoutException:
                continue
        
        if not login_element:
            logging.warning("Login form not found")
            return False
        
        # If we find email field directly, we're already on login page
        if login_element.get_attribute("name") == "email":
            email_input = login_element
        else:
            # Click login button
            login_element.click()
            time.sleep(3)
            # Find email field
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
        
        password_input = driver.find_element(By.NAME, "password")
        
        email_input.clear()
        email_input.send_keys(MAGISTO_EMAIL)
        password_input.clear()
        password_input.send_keys(MAGISTO_PASSWORD)
        password_input.send_keys(Keys.RETURN)
        
        # Wait for login
        time.sleep(8)
        return check_if_logged_in()
        
    except Exception as e:
        logging.error(f"Automatic login failed: {e}")
        return False

# Start login process
logging.info("🚀 Starting login process...")

# First check if already logged in
if check_if_logged_in():
    logging.info("✅ Already logged in! Skipping login process.")
else:
    if not login_to_magisto():
        logging.error("❌ Login failed, exiting script")
        driver.quit()
        exit(1)

# === STEP 2: Load videos (infinite scrolling) ===
def load_all_videos():
    """Load all videos using infinite scrolling"""
    logging.info("[2/5] Loading videos...")
    
    current_url = driver.current_url
    logging.info(f"Current URL after login: {current_url}")
    
    # First check if we're already on videos page
    if '/video/' in current_url or '/my-movies' in current_url or 'mine' in current_url:
        logging.info("✅ Already on videos page! Skipping navigation.")
        # Try to find videos on current page
        if check_for_videos_on_page():
            logging.info("✅ Videos found on current page")
        else:
            logging.info("⚠️ No videos on current page, trying other URLs...")
            return try_alternative_video_urls()
    else:
        # If not on videos page, try to navigate
        logging.info("📍 Navigating to videos page...")
        return try_alternative_video_urls()
    
    # Infinite scrolling on current page
    return perform_infinite_scroll_and_collect()

def check_for_videos_on_page():
    """Check if there are videos on current page"""
    try:
        video_selectors = [
            "a[data-test-id='movie-card']",
            "a[data-testid*='movie']",
            "a[data-testid*='video']",
            ".video-card",
            ".movie-card",
            "a[href*='/video/']",
            "a[href*='/movie/']",
            "[data-test*='video']",
            "[data-test*='movie']"
        ]
        
        for selector in video_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logging.info(f"   → Found {len(elements)} videos using selector: {selector}")
                    return True
            except:
                continue
        
        return False
    except Exception as e:
        logging.warning(f"Error checking for videos: {e}")
        return False

def try_alternative_video_urls():
    """Try different URLs for videos page"""
    video_urls_to_try = [
        # Don't try current URL again if already there
        None,  # placeholder for current URL
        "https://www.magisto.com/video/mine",
        "https://www.magisto.com/my-movies",
        "https://www.magisto.com/videos",
        "https://www.magisto.com/dashboard",
        "https://www.magisto.com/library",
        "https://www.magisto.com/home"
    ]
    
    current_url = driver.current_url
    
    # If already on one of target URLs, start scrolling directly
    for target_url in video_urls_to_try[1:]:  # Skip None placeholder
        if target_url and target_url in current_url:
            logging.info(f"✅ Already on target URL: {current_url}")
            return perform_infinite_scroll_and_collect()
    
    # Try navigating to different URLs
    for idx, url in enumerate(video_urls_to_try[1:], 1):  # Skip None placeholder
        try:
            logging.info(f"🔄 Trying URL {idx}: {url}")
            driver.get(url)
            time.sleep(5)
            
            # Check if page loaded successfully
            if "error" in driver.title.lower() or "not found" in driver.page_source.lower():
                logging.warning(f"   ❌ URL {url} returned error")
                continue
            
            # Check if there are videos on page
            if check_for_videos_on_page():
                logging.info(f"✅ Successfully loaded on URL: {url}")
                return perform_infinite_scroll_and_collect()
            else:
                logging.info(f"   ⚠️ No videos on URL {url}")
                
        except Exception as e:
            logging.warning(f"   ❌ URL {url} failed: {e}")
            continue
    
    logging.error("❌ Failed to load any videos page")
    return []

def perform_infinite_scroll_and_collect():
    """Perform infinite scrolling and collect all videos"""
    logging.info("🔄 Starting infinite scrolling...")
    
    # Infinite scrolling
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_tries = 0
    MAX_SCROLL_TRIES = 15
    
    while scroll_tries < MAX_SCROLL_TRIES:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            scroll_tries += 1
            logging.info(f"   📜 Scroll attempt {scroll_tries}/{MAX_SCROLL_TRIES}")
        else:
            scroll_tries = 0
            last_height = new_height
            logging.info("   📜 Loading more videos...")
    
    logging.info("[3/5] ✅ Scrolling completed, collecting video links...")
    
    # Find all video links using various selectors
    video_selectors = [
        "a[data-test-id='movie-card']",
        "a[data-testid*='movie']", 
        "a[data-testid*='video']",
        ".video-card a",
        ".movie-card a",
        "a[href*='/video/'][href!='/video/mine']",  # Exclude the main page
        "a[href*='/movie/'][href!='/my-movies']",   # Exclude the main page
        "[data-test*='video'] a",
        "[data-test*='movie'] a",
        # More specific selectors for Magisto
        "div[class*='video'] a",
        "div[class*='movie'] a",
        "article a[href*='/video/']",
        ".thumbnail a",
        ".video-thumbnail a"
    ]
    
    all_video_links = []
    for selector in video_selectors:
        try:
            links = driver.find_elements(By.CSS_SELECTOR, selector)
            if links:
                logging.info(f"   → Selector '{selector}': {len(links)} links")
            all_video_links.extend(links)
        except Exception as e:
            logging.debug(f"   ⚠️ Selector '{selector}' failed: {e}")
            continue
    
    # Remove duplicates and get URLs
    video_urls = []
    seen_urls = set()
    
    for link in all_video_links:
        try:
            href = link.get_attribute("href")
            if href and href not in seen_urls:
                # Check if URL contains video identifier and is NOT main page
                if (any(pattern in href for pattern in ['/video/', '/movie/', '/watch/', '/view/']) and
                    not any(excluded in href for excluded in ['/video/mine', '/my-movies', '/videos', '/dashboard'])):
                    
                    # Extra check - URL should have some ID at the end
                    if len(href.split('/')[-1]) > 3:  # Minimum ID length
                        video_urls.append(href)
                        seen_urls.add(href)
        except:
            continue
    
    logging.info(f"🎬 Found {len(video_urls)} unique videos")
    
    # Show some example URLs for debugging
    if video_urls:
        logging.info("📋 Examples of found video URLs:")
        for i, url in enumerate(video_urls[:5]):  # Show first 5
            logging.info(f"   {i+1}. {url}")
        if len(video_urls) > 5:
            logging.info(f"   ... and {len(video_urls) - 5} more videos")
    else:
        # Debug info if no videos found
        logging.warning("⚠️ No videos found! Debug info:")
        
        # Try to find all links on page
        all_links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
        logging.info(f"   Total links found on page: {len(all_links)}")
        
        # Show first 10 links for debugging
        for i, link in enumerate(all_links[:10]):
            try:
                href = link.get_attribute("href")
                text = link.text.strip()[:50]  # First 50 characters of text
                logging.info(f"   {i+1}. {href} (text: '{text}')")
            except:
                continue
    
    return video_urls

video_urls = load_all_videos()

if not video_urls:
    logging.error("❌ No videos found.")
    logging.info("🔍 DEBUG INFO:")
    logging.info(f"   Current URL: {driver.current_url}")
    logging.info(f"   Page title: {driver.title}")
    
    # Output some page elements for debugging
    try:
        # Try to find all links on page
        all_links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
        logging.info(f"   Total links found on page: {len(all_links)}")
        
        # Find links with 'video' in URL
        video_links = [link for link in all_links if '/video/' in link.get_attribute("href")]
        logging.info(f"   Of those {len(video_links)} contain '/video/' in URL")
        
        # Show first 10 video links
        logging.info("   Examples of found '/video/' links:")
        for i, link in enumerate(video_links[:10]):
            try:
                href = link.get_attribute("href")
                text = link.text.strip()[:30] if link.text.strip() else "No text"
                logging.info(f"     {i+1}. {href} ('{text}')")
            except:
                continue
        
        # Try to find any images that could be thumbnails
        images = driver.find_elements(By.CSS_SELECTOR, "img")
        logging.info(f"   Found {len(images)} images on page")
        
        # Save screenshot for debugging
        try:
            screenshot_path = "debug_page_screenshot.png"
            driver.save_screenshot(screenshot_path)
            logging.info(f"   📸 Screenshot saved: {screenshot_path}")
        except:
            pass
        
    except Exception as e:
        logging.warning(f"   Error during debugging: {e}")
    
    logging.info("💡 SUGGESTIONS:")
    logging.info("   1. Check manually if you can see videos in browser")
    logging.info("   2. Maybe Magisto changed page structure")
    logging.info("   3. Try waiting longer for page to load")
    
    driver.quit()
    exit(1)

# Extra validation of found URLs
logging.info("🔍 Checking quality of found URLs...")
valid_video_urls = []
invalid_urls = []

for url in video_urls:
    # Check if URL looks like individual video
    if (url.count('/') >= 4 and  # Minimum URL structure
        not any(excluded in url for excluded in ['/mine', '/my-movies', '/videos', '/dashboard']) and
        len(url.split('/')[-1]) >= 5):  # Video ID has at least 5 characters
        valid_video_urls.append(url)
    else:
        invalid_urls.append(url)

if invalid_urls:
    logging.warning(f"⚠️ Filtered out {len(invalid_urls)} invalid URLs:")
    for invalid_url in invalid_urls[:5]:  # Show only first 5
        logging.warning(f"   - {invalid_url}")

video_urls = valid_video_urls
logging.info(f"✅ Final count of valid video URLs: {len(video_urls)}")

if not video_urls:
    logging.error("❌ No valid video URLs remaining after validation!")
    driver.quit()
    exit(1)

# === STEP 3: Download each video ===
def get_video_id_from_url(video_url):
    """Extract video ID from URL for identifying downloaded files"""
    try:
        # e.g. https://www.magisto.com/video/P14WY1NQHDE9VQNhCzE -> P14WY1NQHDE9VQNhCzE
        return video_url.split('/')[-1]
    except:
        return None

def get_video_name_from_widget(driver):
    """Get video name directly from video widget (where download button is)"""
    try:
        # Possible selectors for video name in video widget
        video_name_selectors = [
            "h1",  # Often main heading
            "h2", 
            "h3",
            ".video-title",
            ".title", 
            ".video-name",
            ".media-title",
            "[data-test-id='video-title']",
            "[data-testid='video-title']",
            # Search for text near download button
            "//span[contains(text(),'Download')]/../..//h1",
            "//span[contains(text(),'Download')]/../..//h2", 
            "//span[contains(text(),'Download')]/../..//h3",
            "//span[contains(text(),'Download')]/../preceding-sibling::*//*[string-length(text()) > 3]",
            "//span[contains(text(),'Download')]/../following-sibling::*//*[string-length(text()) > 3]"
        ]
        
        for selector in video_name_selectors:
            try:
                if selector.startswith("//"):
                    title_element = driver.find_element(By.XPATH, selector)
                else:
                    title_element = driver.find_element(By.CSS_SELECTOR, selector)
                
                title = title_element.text.strip()
                
                # Filter unwanted text
                if (title and len(title) > 2 and 
                    "Magisto" not in title and 
                    "Download" not in title and
                    "Page not Found" not in title and
                    not title.isdigit() and  # Is not just a number
                    ":" not in title):  # Is not a time code
                    
                    logging.info(f"   📝 Found video name: '{title}'")
                    return title
            except:
                continue
                
        logging.warning("   ⚠️ Could not find video name in widget")
        return None
        
    except Exception as e:
        logging.error(f"   ❌ Error getting video name: {e}")
        return None

def is_video_already_downloaded_by_name(driver, video_url, download_dir):
    """Check if video is already downloaded - enhanced version using widget name"""
    import glob
    
    video_id = get_video_id_from_url(video_url)
    if not video_id:
        return False, None
    
    # Method 1: Search by video ID in filename
    search_patterns = [
        f"*{video_id}*.mp4",
        f"*{video_id}*.mov", 
        f"*{video_id}*.avi",
        f"*{video_id}*.mkv",
        f"*{video_id}*.webm"
    ]
    
    for pattern in search_patterns:
        matching_files = glob.glob(os.path.join(download_dir, pattern))
        if matching_files:
            return True, matching_files[0]
    
    # Method 2: Search by URL -> file mapping
    mapping_file = os.path.join(download_dir, "download_mapping.txt")
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if '|' in line:
                        saved_url, saved_file = line.strip().split('|', 1)
                        if saved_url == video_url:
                            full_path = os.path.join(download_dir, saved_file)
                            if os.path.exists(full_path):
                                return True, full_path
        except:
            pass
    
    # Method 3: NEW - Check by widget name
    logging.info(f"   🔍 Getting video name from widget...")
    
    # Page is already loaded, just get the name
    video_name = get_video_name_from_widget(driver)
    
    # NEW: If video has generic name ("Untitled"), always download
    if (video_name and 
        (video_name.lower() in ['untitled', 'bez názvu', 'no title', 'no name', 'untitled video', 'new video', 'video', 'my video'] or
         len(video_name.strip()) <= 2)):  # Very short names (1-2 chars) considered generic
        logging.info(f"   ⚠️ Video has generic name '{video_name}' - will be downloaded again for better naming")
        logging.info(f"   💡 Generic names like 'Untitled', 'My video' are never skipped")
        return False, None
    
    if video_name:
        logging.info(f"   🔍 Searching for files with name '{video_name}' (length: {len(video_name)} chars)...")
        
        # Search for files starting with video name with various extensions
        video_extensions = ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'webm']
        
        for ext in video_extensions:
            # Method 3a: Exact match for short names
            exact_patterns = [
                f"{video_name}.{ext}",
                f"{video_name}_HD.{ext}",
                f"{video_name}_FULL_HD.{ext}",
                f"{video_name}_HQ.{ext}",
                f"{video_name}_FULL.{ext}"
            ]
            
            for pattern_name in exact_patterns:
                full_path = os.path.join(download_dir, pattern_name)
                if os.path.exists(full_path):
                    logging.info(f"   ✅ Found by exact match: '{pattern_name}'")
                    return True, full_path
            
            # Method 3b: Wildcard for long names (in case Magisto didn't truncate)
            pattern = os.path.join(download_dir, f"{video_name}*.{ext}")
            matching_files = glob.glob(pattern)
            
            if matching_files:
                filename = os.path.basename(matching_files[0])
                logging.info(f"   ✅ Found by wildcard match: '{filename}'")
                return True, matching_files[0]
        
        # Method 3c: NEW - Check truncated names (up to 20 chars + quality)
        # Magisto truncates long names to ~20 chars and adds _FULL_HD, _HD, etc.
        if len(video_name) > 20:
            truncated_name = video_name[:20]  # First 20 characters
            logging.info(f"   🔍 Name is long ({len(video_name)} chars), trying truncated version: '{truncated_name}'")
            
            for ext in video_extensions:
                # Search for files starting with truncated name
                pattern = os.path.join(download_dir, f"{truncated_name}*.{ext}")
                matching_files = glob.glob(pattern)
                
                for match in matching_files:
                    filename = os.path.basename(match)
                    # Verify file actually starts with video name (not just coincidence)
                    if filename.lower().startswith(truncated_name.lower()):
                        logging.info(f"   ✅ Found by truncated name (20 chars): '{filename}'")
                        return True, match
        
        # Method 3d: Flexible search by name beginning (for various truncation lengths)
        # Try different truncation lengths (15-25 chars)
        for truncate_length in range(15, min(26, len(video_name) + 1)):
            if truncate_length >= len(video_name):
                continue  # Already tried exact match
                
            truncated = video_name[:truncate_length]
            
            for ext in video_extensions:
                pattern = os.path.join(download_dir, f"{truncated}*.{ext}")
                matching_files = glob.glob(pattern)
                
                for match in matching_files:
                    filename = os.path.basename(match)
                    # Verify it's the same video (name beginning matches)
                    base_name = os.path.splitext(filename)[0]  # Without extension
                    # Remove quality suffixes
                    clean_base = base_name.replace('_FULL_HD', '').replace('_HD', '').replace('_HQ', '').replace('_FULL', '')
                    
                    if clean_base.lower().startswith(truncated.lower()) and len(clean_base) <= len(video_name):
                        logging.info(f"   ✅ Found by flexible search (truncated to {truncate_length} chars): '{filename}'")
                        return True, match
        
        logging.info(f"   ❌ No file found for name '{video_name}' (even truncated)")
    else:
        logging.warning("   ⚠️ Could not get video name from widget")
    
    return False, None

def save_download_mapping(video_url, downloaded_file, download_dir):
    """Save URL -> filename mapping for future skip detection"""
    try:
        mapping_file = os.path.join(download_dir, "download_mapping.txt")
        file_name = os.path.basename(downloaded_file)
        
        # Check if mapping already exists
        existing_mappings = set()
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    existing_mappings = set(line.strip() for line in f)
            except:
                pass
        
        new_mapping = f"{video_url}|{file_name}"
        if new_mapping not in existing_mappings:
            with open(mapping_file, 'a', encoding='utf-8') as f:
                f.write(f"{new_mapping}\n")
    except Exception as e:
        logging.warning(f"Could not save mapping: {e}")

def download_video(video_url, video_index, total_videos):
    """Download one video with error handling and enhanced skip detection by name"""
    import glob
    import os
    
    download_dir = DOWNLOAD_DIR  # Use correct configured path!
    
    try:
        # Load video page
        driver.get(video_url)
        time.sleep(3)  # Wait for page to load
        
        # NEW APPROACH: First check skip detection with loaded page
        already_downloaded, existing_file = is_video_already_downloaded_by_name(driver, video_url, download_dir)
        
        if already_downloaded:
            logging.info(f"[4/5] ({video_index}/{total_videos}) ⏭️  SKIPPING - already downloaded: {os.path.basename(existing_file)}")
            return True  # Count as success
        
        logging.info(f"[4/5] ({video_index}/{total_videos}) Visiting {video_url}")
        
        # Page is already loaded, just wait for widget
        time.sleep(5)  # Additional wait for video widget to load
        
        # FIXED selectors for download button
        download_selectors = [
            "//span[contains(text(),'Download')]",  # ✅ Main selector - SPAN element
            "//button[contains(text(),'Download')]",
            "//button[contains(text(),'download')]",
            "//a[contains(text(),'Download')]",
            "//a[contains(text(),'download')]",
            "//button[contains(@class,'download')]",
            "//a[contains(@class,'download')]",
            "//span[contains(@class,'download')]",  # Added for span elements
            "[data-test-id*='download']",
            "[data-testid*='download']",
            ".download-btn",
            ".download-button"
        ]
        
        download_btn = None
        download_wait = WebDriverWait(driver, DOWNLOAD_TIMEOUT)
        
        for selector in download_selectors:
            try:
                if selector.startswith("//"):
                    download_btn = download_wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    download_btn = download_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                break
            except TimeoutException:
                continue
        
        if download_btn:
            # Save list of files before clicking
            initial_files = set(glob.glob(os.path.join(download_dir, "*")))
            
            download_btn.click()
            logging.info("     → Clicked Download button...")
            
            # Wait a moment and check if popup appeared
            time.sleep(3)
            
            # FIXED selectors for confirmation popup for older videos
            confirmation_selectors = [
                "//button[contains(text(),'Download')]",  # Second download button in popup
                "//span[contains(text(),'Download')]",   # Second download span in popup
                "//button[contains(text(),'Confirm')]",
                "//button[contains(text(),'OK')]",
                "//button[contains(text(),'Yes')]",
                "//div[@class='modal']//button[contains(text(),'Download')]",
                "//div[@class='popup']//button[contains(text(),'Download')]",
                "//div[@class='dialog']//button[contains(text(),'Download')]"
            ]
            
            popup_found = False
            for selector in confirmation_selectors:
                try:
                    # All are XPath selectors
                    confirmation_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    # Verify it's not the same button as before
                    if confirmation_btn != download_btn:
                        confirmation_btn.click()
                        logging.info("     → Confirmed in popup dialog...")
                        popup_found = True
                        break
                except TimeoutException:
                    continue
            
            if not popup_found:
                logging.info("     → No popup detected")
            
            # Wait for download to start
            time.sleep(WAIT_AFTER_DOWNLOAD)
            
            # Check if new file appeared
            final_files = set(glob.glob(os.path.join(download_dir, "*")))
            new_files = final_files - initial_files
            
            if new_files:
                new_file_path = list(new_files)[0]
                new_file_name = os.path.basename(new_file_path)
                logging.info(f"     ✅ New file downloaded: {new_file_name}")
                
                # Save mapping for future skip detection
                save_download_mapping(video_url, new_file_path, download_dir)
            else:
                logging.info("     ⏳ Download may still be in progress...")
            
            return True
        else:
            logging.warning("     ❌ Error: 'Download' button not found.")
            return False
            
    except Exception as e:
        logging.error(f"     ❌ Error processing video {video_url}: {e}")
        return False

# Main download loop
successful_downloads = 0
failed_downloads = 0
skipped_downloads = 0

logging.info(f"🚀 Starting download of {len(video_urls)} videos...")
logging.info("   (Already downloaded videos will be automatically skipped)")

for idx, url in enumerate(video_urls, 1):
    # Check if video is already downloaded (for statistics before calling download_video)
    download_dir = DOWNLOAD_DIR  # Use correct configured path!
    
    # Briefly load page for check
    already_downloaded = False
    try:
        driver.get(url)
        time.sleep(2)
        already_downloaded, _ = is_video_already_downloaded_by_name(driver, url, download_dir)
    except:
        already_downloaded = False
    
    if download_video(url, idx, len(video_urls)):
        if already_downloaded:
            skipped_downloads += 1
        else:
            successful_downloads += 1
    else:
        failed_downloads += 1

logging.info("=" * 60)
logging.info(f"[5/5] ✅ COMPLETED! Overall statistics:")
logging.info(f"   📥 Newly downloaded: {successful_downloads}")
logging.info(f"   ⏭️  Skipped (already downloaded): {skipped_downloads}")
logging.info(f"   ❌ Errors: {failed_downloads}")
logging.info(f"   📊 Total processed: {successful_downloads + skipped_downloads + failed_downloads}")

# Show information about downloaded files
download_dir = DOWNLOAD_DIR  # Use correct configured path!
if os.path.exists(download_dir):
    import glob
    all_videos = []
    for ext in ['*.mp4', '*.mov', '*.avi', '*.mkv', '*.webm']:
        all_videos.extend(glob.glob(os.path.join(download_dir, ext)))
    
    logging.info(f"📁 Total videos in downloads folder: {len(all_videos)}")
    
    # Show folder size
    try:
        total_size = sum(os.path.getsize(f) for f in all_videos if os.path.isfile(f))
        size_gb = total_size / (1024**3)
        logging.info(f"💾 Total size: {size_gb:.2f} GB")
    except:
        pass

logging.info("=" * 60)
driver.quit()
