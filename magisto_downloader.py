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

# === KONFIGURACE ===
DOWNLOAD_DIR = "/home/nowass/Videos/Magisto"  # uprav podle sebe

# Nastavení prohlížeče - "chrome" nebo "brave"
# POZOR: Brave může mít problémy s verzí ChromeDriveru - doporučujeme Chrome
BROWSER_TYPE = "chrome"  # změň na "brave" pokud máš kompatibilní verzi

WAIT_AFTER_DOWNLOAD = 10  # vteřiny pro počkání po kliknutí na "Download"
LOGIN_TIMEOUT = 20  # timeout pro nalezení elementů při přihlášení
DOWNLOAD_TIMEOUT = 15  # timeout pro nalezení download tlačítka

# === Nastavení logování ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('magisto_downloader.log'),
        logging.StreamHandler()
    ]
)

# === Nastavení prohlížeče ===
def get_brave_binary_path():
    """Najde cestu k Brave browseru na různých OS"""
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
    """Nastavení prohlížeče (Chrome nebo Brave) s optimalizovanými možnostmi"""
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.notifications": 2  # blokovat notifikace
    })
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Vytvoření downloadovací složky
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    if BROWSER_TYPE.lower() == "brave":
        # Nastavení pro Brave browser
        brave_path = get_brave_binary_path()
        if brave_path:
            options.binary_location = brave_path
            logging.info(f"Pokouším se použít Brave browser: {brave_path}")
            logging.warning("POZOR: Brave může mít problémy s verzí ChromeDriveru!")
            logging.info("Pokud se vyskytnou chyby, změň BROWSER_TYPE na 'chrome'")
        else:
            logging.error("Brave browser nebyl nalezen! Přepínám na Chrome...")
            logging.info("Nainstaluj Brave nebo změň BROWSER_TYPE na 'chrome'")
    else:
        logging.info("Používám Chrome browser")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logging.info("Prohlížeč úspěšně spuštěn!")
        return driver
    except Exception as e:
        logging.error(f"Chyba při spuštění prohlížeče: {e}")
        if BROWSER_TYPE.lower() == "brave":
            logging.error("Problém s Brave browserem - pravděpodobně nekompatibilní verze ChromeDriveru")
            logging.info("ŘEŠENÍ: Změň BROWSER_TYPE na 'chrome' v konfiguraci")
            logging.info("Nebo nainstaluj starší verzi Brave nebo novější verzi ChromeDriveru")
        raise

try:
    driver = setup_browser_driver()
    wait = WebDriverWait(driver, LOGIN_TIMEOUT)
except Exception as e:
    logging.error("Nelze spustit prohlížeč. Ukončuji script.")
    exit(1)

# === Pomocné funkce ===
def check_if_logged_in():
    """Kontrola, zda je uživatel přihlášen"""
    try:
        # Kontrola různých indikátorů přihlášení
        login_indicators = [
            # Pozitivní indikátory (když je přihlášen)
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
                    logging.info(f"   → Nalezen indikátor přihlášení: {indicator}")
                    return True
            except:
                continue
        
        # Kontrola URL - pokud jsme přesměrováni na dashboard nebo podobně
        current_url = driver.current_url
        logged_in_patterns = ['/dashboard', '/video/', '/my-movies', '/profile']
        
        for pattern in logged_in_patterns:
            if pattern in current_url:
                logging.info(f"   → URL indikuje přihlášení: {current_url}")
                return True
        
        return False
        
    except Exception as e:
        logging.warning(f"Chyba při kontrole přihlášení: {e}")
        return False

# === KROK 1: Přihlášení (Manual Login Support) ===
def login_to_magisto():
    """Přihlášení na Magisto s podporou manuálního přihlášení"""
    logging.info("[1/5] Otevírám Magisto login stránku...")
    
    try:
        # Použití přímé login URL pro manuální přihlášení
        driver.get("https://www.magisto.com/connect?q_offer_info=eyJpZCI6IjE0MDA1NDcwMjY5NzE3ODc1MzkiLCJleHBpcmF0aW9uIjoxNzUzNjgyMTc3ODQ4fQ%3D%3D")
        
        logging.info("🔐 MANUÁLNÍ PŘIHLÁŠENÍ:")
        logging.info("   → Otevřel jsem login stránku")
        logging.info("   → Prosím, přihlas se ručně v prohlížeči")
        logging.info("   → Po přihlášení stiskni ENTER v terminálu pro pokračování...")
        
        # Čekání na manuální potvrzení
        input("Stiskni ENTER po dokončení přihlášení...")
        
        # Kontrola, zda je uživatel přihlášen
        logged_in = check_if_logged_in()
        
        if logged_in:
            logging.info("✅ Přihlášení úspěšné!")
            return True
        else:
            logging.error("❌ Zdá se, že přihlášení se nezdařilo")
            
            # Pokusit se o automatické přihlášení jako fallback
            logging.info("🔄 Pokouším se o automatické přihlášení...")
            return attempt_automatic_login()
            
    except Exception as e:
        logging.error(f"Chyba při přihlašování: {e}")
        return False

def attempt_automatic_login():
    """Pokus o automatické přihlášení jako fallback"""
    try:
        logging.info("Hledám login formulář...")
        
        # Hledání login tlačítka nebo formuláře
        login_selectors = [
            "//a[contains(text(),'Log in')]",
            "//a[contains(text(),'Sign in')]",
            "//button[contains(text(),'Log in')]",
            "//button[contains(text(),'Sign in')]",
            ".login-btn",
            "[data-test-id='login-button']",
            "input[name='email']"  # Přímé hledání email pole
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
            logging.warning("Login formulář nebyl nalezen")
            return False
        
        # Pokud najdeme přímo email pole, jsme už na login stránce
        if login_element.get_attribute("name") == "email":
            email_input = login_element
        else:
            # Kliknout na login tlačítko
            login_element.click()
            time.sleep(3)
            # Najít email pole
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
        
        password_input = driver.find_element(By.NAME, "password")
        
        email_input.clear()
        email_input.send_keys(MAGISTO_EMAIL)
        password_input.clear()
        password_input.send_keys(MAGISTO_PASSWORD)
        password_input.send_keys(Keys.RETURN)
        
        # Počkání na přihlášení
        time.sleep(8)
        return check_if_logged_in()
        
    except Exception as e:
        logging.error(f"Automatické přihlášení selhalo: {e}")
        return False

# Spuštění přihlášení
logging.info("🚀 Začínám proces přihlášení...")

# Nejdříve zkontrolovat, jestli už nejsme přihlášeni
if check_if_logged_in():
    logging.info("✅ Už jste přihlášeni! Přeskakuji login proces.")
else:
    if not login_to_magisto():
        logging.error("❌ Přihlášení selhalo, ukončuji script")
        driver.quit()
        exit(1)

# === KROK 2: Načíst videa (nekonečné scrollování) ===
def load_all_videos():
    """Načtení všech videí pomocí nekonečného scrollování"""
    logging.info("[2/5] Načítám videa...")
    
    current_url = driver.current_url
    logging.info(f"Aktuální URL po přihlášení: {current_url}")
    
    # Nejdříve zkontrolovat, zda už nejsme na stránce s videi
    if '/video/' in current_url or '/my-movies' in current_url or 'mine' in current_url:
        logging.info("✅ Už jsme na stránce s videi! Přeskakuji navigaci.")
        # Zkusit najít videa na aktuální stránce
        if check_for_videos_on_page():
            logging.info("✅ Videa nalezena na aktuální stránce")
        else:
            logging.info("⚠️ Na aktuální stránce nejsou videa, zkouším jiné URL...")
            return try_alternative_video_urls()
    else:
        # Pokud nejsme na stránce s videi, zkusit navigovat
        logging.info("📍 Navigace na stránku s videi...")
        return try_alternative_video_urls()
    
    # Nekonečné scrollování na aktuální stránce
    return perform_infinite_scroll_and_collect()

def check_for_videos_on_page():
    """Zkontroluje, zda jsou na aktuální stránce videa"""
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
                    logging.info(f"   → Nalezeno {len(elements)} videí pomocí selektoru: {selector}")
                    return True
            except:
                continue
        
        return False
    except Exception as e:
        logging.warning(f"Chyba při kontrole videí: {e}")
        return False

def try_alternative_video_urls():
    """Zkusí různé URL pro stránku s videi"""
    video_urls_to_try = [
        # Nezkoušet znovu aktuální URL pokud už tam jsme
        None,  # placeholder pro aktuální URL
        "https://www.magisto.com/video/mine",
        "https://www.magisto.com/my-movies",
        "https://www.magisto.com/videos",
        "https://www.magisto.com/dashboard",
        "https://www.magisto.com/library",
        "https://www.magisto.com/home"
    ]
    
    current_url = driver.current_url
    
    # Pokud už jsme na některé z target URL, začít přímo scrollováním
    for target_url in video_urls_to_try[1:]:  # Skip None placeholder
        if target_url and target_url in current_url:
            logging.info(f"✅ Už jsme na target URL: {current_url}")
            return perform_infinite_scroll_and_collect()
    
    # Zkusit navigovat na různé URL
    for idx, url in enumerate(video_urls_to_try[1:], 1):  # Skip None placeholder
        try:
            logging.info(f"🔄 Zkouším URL {idx}: {url}")
            driver.get(url)
            time.sleep(5)
            
            # Kontrola, zda se stránka načetla úspěšně
            if "error" in driver.title.lower() or "not found" in driver.page_source.lower():
                logging.warning(f"   ❌ URL {url} vrátil chybu")
                continue
            
            # Kontrola, zda jsou videa na stránce
            if check_for_videos_on_page():
                logging.info(f"✅ Úspěšně načteno na URL: {url}")
                return perform_infinite_scroll_and_collect()
            else:
                logging.info(f"   ⚠️ Na URL {url} nejsou videa")
                
        except Exception as e:
            logging.warning(f"   ❌ URL {url} selhalo: {e}")
            continue
    
    logging.error("❌ Nepodařilo se načíst žádnou stránku s videi")
    return []

def perform_infinite_scroll_and_collect():
    """Provede nekonečné scrollování a sebere všechna videa"""
    logging.info("🔄 Spouštím nekonečné scrollování...")
    
    # Nekonečné scrollování
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_tries = 0
    MAX_SCROLL_TRIES = 15
    
    while scroll_tries < MAX_SCROLL_TRIES:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            scroll_tries += 1
            logging.info(f"   📜 Scroll pokus {scroll_tries}/{MAX_SCROLL_TRIES}")
        else:
            scroll_tries = 0
            last_height = new_height
            logging.info("   📜 Načítám další videa...")
    
    logging.info("[3/5] ✅ Scrollování dokončeno, sbírám odkazy na videa...")
    
    # Nalezení všech video odkazů pomocí různých selectorů
    video_selectors = [
        "a[data-test-id='movie-card']",
        "a[data-testid*='movie']",
        "a[data-testid*='video']",
        ".video-card a",
        ".movie-card a", 
        "a[href*='/video/']",
        "a[href*='/movie/']",
        "[data-test*='video'] a",
        "[data-test*='movie'] a"
    ]
    
    all_video_links = []
    for selector in video_selectors:
        try:
            links = driver.find_elements(By.CSS_SELECTOR, selector)
            if links:
                logging.info(f"   → Selector '{selector}': {len(links)} odkazů")
            all_video_links.extend(links)
        except Exception as e:
            logging.debug(f"   ⚠️ Selector '{selector}' selhal: {e}")
            continue
    
    # Odstranění duplikátů a získání URL
    video_urls = []
    seen_urls = set()
    
    for link in all_video_links:
        try:
            href = link.get_attribute("href")
            if href and href not in seen_urls:
                # Kontrola, zda URL obsahuje video identifikátor
                if any(pattern in href for pattern in ['/video/', '/movie/', '/watch/', '/view/']):
                    video_urls.append(href)
                    seen_urls.add(href)
        except:
            continue
    
    logging.info(f"🎬 Nalezeno celkem {len(video_urls)} unikátních videí")
    
    # Zobrazit několik příkladů URL pro debugging
    if video_urls:
        logging.info("📋 Příklady nalezených video URL:")
        for i, url in enumerate(video_urls[:3]):  # Zobrazit prvních 5
            logging.info(f"   {i+1}. {url}")
        if len(video_urls) > 3:
            logging.info(f"   ... a dalších {len(video_urls) - 3} videí")
    
    return video_urls

video_urls = load_all_videos()

if not video_urls:
    logging.error("❌ Nebyla nalezena žádná videa.")
    logging.info("🔍 DEBUG INFO:")
    logging.info(f"   Aktuální URL: {driver.current_url}")
    logging.info(f"   Titulek stránky: {driver.title}")
    
    # Výpis několika elementů na stránce pro debugging
    try:
        all_elements = driver.find_elements(By.CSS_SELECTOR, "a, button, div[class*='video'], div[class*='movie']")
        logging.info(f"   Celkem nalezeno {len(all_elements)} interaktivních elementů")
        
        # Zkusit najít jakékoliv odkazy s 'video' nebo 'movie' v textu
        video_text_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'video') or contains(text(), 'movie') or contains(text(), 'Video') or contains(text(), 'Movie')]")
        if video_text_links:
            logging.info(f"   Nalezeno {len(video_text_links)} odkazů s 'video/movie' v textu")
        
        # Zkusit najít jakékoliv obrázky, které by mohly být thumbnaily
        images = driver.find_elements(By.CSS_SELECTOR, "img")
        logging.info(f"   Nalezeno {len(images)} obrázků na stránce")
        
        # Uložit screenshot pro debugging
        try:
            screenshot_path = "debug_page_screenshot.png"
            driver.save_screenshot(screenshot_path)
            logging.info(f"   📸 Screenshot uložen: {screenshot_path}")
        except:
            pass
        
    except Exception as e:
        logging.warning(f"   Chyba při debugging: {e}")
    
    logging.info("💡 NÁVRHY:")
    logging.info("   1. Zkontroluj ručně, zda vidíš videa v prohlížeči")
    logging.info("   2. Zkus jiný browser nebo vyčistit cache")
    logging.info("   3. Magisto možná změnil strukturu stránky")
    
    driver.quit()
    exit(1)

# === KROK 3: Stáhni každé video ===
def download_video(video_url, video_index, total_videos):
    """Stáhnutí jednoho videa s error handlingem"""
    logging.info(f"[4/5] ({video_index}/{total_videos}) Navštěvuji {video_url}")
    
    try:
        driver.get(video_url)
        time.sleep(5)
        
        # Možné selektory pro download tlačítko
        download_selectors = [
            "//button[contains(text(),'Download')]",
            "//button[contains(text(),'download')]",
            "//a[contains(text(),'Download')]",
            "//a[contains(text(),'download')]",
            "//button[contains(@class,'download')]",
            "//a[contains(@class,'download')]",
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
            download_btn.click()
            logging.info("     → Stahování zahájeno...")
            time.sleep(WAIT_AFTER_DOWNLOAD)
            return True
        else:
            logging.warning("     ❌ Chyba: tlačítko 'Download' nenalezeno.")
            return False
            
    except Exception as e:
        logging.error(f"     ❌ Chyba při zpracování videa {video_url}: {e}")
        return False

# Hlavní loop pro stahování
successful_downloads = 0
failed_downloads = 0

for idx, url in enumerate(video_urls, 1):
    if download_video(url, idx, len(video_urls)):
        successful_downloads += 1
    else:
        failed_downloads += 1

logging.info(f"[5/5] ✅ Hotovo! Úspěšně staženo: {successful_downloads}, Selhalo: {failed_downloads}")
driver.quit()
