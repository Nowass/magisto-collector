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
# Credentials (pouze pro automatické přihlášení - lze nechat prázdné pro manuální login)
MAGISTO_EMAIL = ""  # můžeš vymazat pro manuální login
MAGISTO_PASSWORD = ""  # můžeš vymazat pro manuální login
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
    
    # Kontrola, zda jsou zadané credentials
    if not MAGISTO_EMAIL or not MAGISTO_PASSWORD:
        logging.warning("❌ Credentials nejsou nastaveny - automatické přihlášení nelze provést")
        logging.info("💡 Nastav MAGISTO_EMAIL a MAGISTO_PASSWORD v konfiguraci pro automatické přihlášení")
        return False
    
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
                # Kontrola, zda URL obsahuje video identifikátor a NENÍ to main page
                if (any(pattern in href for pattern in ['/video/', '/movie/', '/watch/', '/view/']) and
                    not any(excluded in href for excluded in ['/video/mine', '/my-movies', '/videos', '/dashboard'])):
                    
                    # Extra kontrola - URL by mělo mít nějaký ID na konci
                    if len(href.split('/')[-1]) > 3:  # Minimální délka ID
                        video_urls.append(href)
                        seen_urls.add(href)
        except:
            continue
    
    logging.info(f"🎬 Nalezeno celkem {len(video_urls)} unikátních videí")
    
    # Zobrazit několik příkladů URL pro debugging
    if video_urls:
        logging.info("📋 Příklady nalezených video URL:")
        for i, url in enumerate(video_urls[:5]):  # Zobrazit prvních 5
            logging.info(f"   {i+1}. {url}")
        if len(video_urls) > 5:
            logging.info(f"   ... a dalších {len(video_urls) - 5} videí")
    else:
        # Debug info pokud nejsou nalezena žádná videa
        logging.warning("⚠️ Nebyla nalezena žádná videa! Debug info:")
        
        # Zkusit najít všechny odkazy na stránce
        all_links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
        logging.info(f"   Celkem nalezeno {len(all_links)} odkazů na stránce")
        
        # Zobrazit prvních 10 odkazů pro debugging
        for i, link in enumerate(all_links[:10]):
            try:
                href = link.get_attribute("href")
                text = link.text.strip()[:50]  # První 50 znaků textu
                logging.info(f"   {i+1}. {href} (text: '{text}')")
            except:
                continue
    
    return video_urls

video_urls = load_all_videos()

if not video_urls:
    logging.error("❌ Nebyla nalezena žádná videa.")
    logging.info("🔍 DEBUG INFO:")
    logging.info(f"   Aktuální URL: {driver.current_url}")
    logging.info(f"   Titulek stránky: {driver.title}")
    
    # Výpis několika elementů na stránce pro debugging
    try:
        # Zkusit najít všechny odkazy na stránce
        all_links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
        logging.info(f"   Celkem nalezeno {len(all_links)} odkazů na stránce")
        
        # Najít odkazy s 'video' v URL
        video_links = [link for link in all_links if '/video/' in link.get_attribute("href")]
        logging.info(f"   Z toho {len(video_links)} obsahuje '/video/' v URL")
        
        # Zobrazit prvních 10 video odkazů
        logging.info("   Příklady nalezených '/video/' odkazů:")
        for i, link in enumerate(video_links[:10]):
            try:
                href = link.get_attribute("href")
                text = link.text.strip()[:30] if link.text.strip() else "No text"
                logging.info(f"     {i+1}. {href} ('{text}')")
            except:
                continue
        
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
    logging.info("   2. Možná Magisto změnil strukturu stránek")
    logging.info("   3. Zkus počkat déle na načtení stránky")
    
    driver.quit()
    exit(1)

# Extra validace nalezených URL
logging.info("🔍 Kontroluji kvalitu nalezených URL...")
valid_video_urls = []
invalid_urls = []

for url in video_urls:
    # Kontrola, zda URL vypadá jako jednotlivé video
    if (url.count('/') >= 4 and  # Minimální struktura URL
        not any(excluded in url for excluded in ['/mine', '/my-movies', '/videos', '/dashboard']) and
        len(url.split('/')[-1]) >= 5):  # ID videa má aspoň 5 znaků
        valid_video_urls.append(url)
    else:
        invalid_urls.append(url)

if invalid_urls:
    logging.warning(f"⚠️ Vyřazeno {len(invalid_urls)} neplatných URL:")
    for invalid_url in invalid_urls[:5]:  # Zobrazit jen prvních 5
        logging.warning(f"   - {invalid_url}")

video_urls = valid_video_urls
logging.info(f"✅ Finální počet platných video URL: {len(video_urls)}")

if not video_urls:
    logging.error("❌ Po validaci nezbylo žádné platné video URL!")
    driver.quit()
    exit(1)

# === KROK 3: Stáhni každé video ===
def get_video_id_from_url(video_url):
    """Extrahuje video ID z URL pro identifikaci stažených souborů"""
    try:
        # Např. https://www.magisto.com/video/P14WY1NQHDE9VQNhCzE -> P14WY1NQHDE9VQNhCzE
        return video_url.split('/')[-1]
    except:
        return None

def get_video_name_from_widget(driver):
    """Získá název videa přímo z video widgetu (tam kde je i download tlačítko)"""
    try:
        # Možné selektory pro název videa v rámci video widgetu
        video_name_selectors = [
            "h1",  # Často hlavní nadpis
            "h2", 
            "h3",
            ".video-title",
            ".title", 
            ".video-name",
            ".media-title",
            "[data-test-id='video-title']",
            "[data-testid='video-title']",
            # Hledat text v blízkosti download tlačítka
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
                
                # Filtrovat nežádoucí texty
                if (title and len(title) > 2 and 
                    "Magisto" not in title and 
                    "Download" not in title and
                    "Page not Found" not in title and
                    not title.isdigit() and  # Není jen číslo
                    ":" not in title):  # Není časový kód
                    
                    logging.info(f"   📝 Nalezen název videa: '{title}'")
                    return title
            except:
                continue
                
        logging.warning("   ⚠️ Nepodařilo se najít název videa ve widgetu")
        return None
        
    except Exception as e:
        logging.error(f"   ❌ Chyba při získávání názvu videa: {e}")
        return None

def is_video_already_downloaded_by_name(driver, video_url, download_dir):
    """Kontroluje, zda je video již staženo - vylepšená verze používající název z widgetu"""
    import glob
    
    video_id = get_video_id_from_url(video_url)
    if not video_id:
        return False, None
    
    # Metoda 1: Hledat podle video ID v názvu souboru
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
    
    # Metoda 2: Hledat podle mapování URL -> soubor
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
    
    # Metoda 3: NOVÁ - Kontrola podle názvu z video widgetu
    logging.info(f"   🔍 Získávám název videa z widgetu...")
    
    # Stránka už je načtená, jen získáme název
    video_name = get_video_name_from_widget(driver)
    
    if video_name:
        logging.info(f"   🔍 Hledám soubory pro název '{video_name}'...")
        
        # Hledat soubory začínající názvem videa s různými příponami
        video_extensions = ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'webm']
        
        for ext in video_extensions:
            # Metoda 3a: Přesná shoda pro krátké názvy
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
                    logging.info(f"   ✅ Nalezeno přesnou shodou: '{pattern_name}'")
                    return True, full_path
            
            # Metoda 3b: Wildcard pro dlouhé názvy (pro případ, že by Magisto nezkrátil)
            pattern = os.path.join(download_dir, f"{video_name}*.{ext}")
            matching_files = glob.glob(pattern)
            
            if matching_files:
                filename = os.path.basename(matching_files[0])
                logging.info(f"   ✅ Nalezeno wildcard shodou: '{filename}'")
                return True, matching_files[0]
        
        # Metoda 3c: NOVÁ - Kontrola zkrácených názvů (až 20 znaků + kvalita)
        # Magisto zkracuje dlouhé názvy na ~20 znaků a přidává _FULL_HD, _HD, atd.
        if len(video_name) > 20:
            truncated_name = video_name[:20]  # Prvních 20 znaků
            logging.info(f"   🔍 Název je dlouhý ({len(video_name)} znaků), zkouším zkrácenou verzi: '{truncated_name}'")
            
            for ext in video_extensions:
                # Hledat soubory začínající zkráceným názvem
                truncated_patterns = [
                    f"{truncated_name}*.{ext}",  # Wildcard pro jakékoliv zakončení
                ]
                
                for pattern in truncated_patterns:
                    matching_files = glob.glob(os.path.join(download_dir, pattern))
                    
                    for match in matching_files:
                        filename = os.path.basename(match)
                        # Ověřit, že soubor skutečně začíná názvem videa (ne jen náhodou)
                        if filename.lower().startswith(truncated_name.lower()):
                            logging.info(f"   ✅ Nalezeno podle zkráceného názvu: '{filename}'")
                            return True, match
        
        # Metoda 3d: Flexibilní hledání podle začátku názvu (pro různé délky zkrácení)
        # Zkusíme různé délky zkrácení (15-25 znaků)
        for truncate_length in range(15, min(26, len(video_name) + 1)):
            if truncate_length >= len(video_name):
                continue  # Už jsme zkoušeli přesnou shodu
                
            truncated = video_name[:truncate_length]
            
            for ext in video_extensions:
                pattern = os.path.join(download_dir, f"{truncated}*.{ext}")
                matching_files = glob.glob(pattern)
                
                for match in matching_files:
                    filename = os.path.basename(match)
                    # Ověřit, že se jedná o stejné video (začátek názvu se shoduje)
                    base_name = os.path.splitext(filename)[0]  # Bez přípony
                    # Odstranit kvalitativní sufixy
                    clean_base = base_name.replace('_FULL_HD', '').replace('_HD', '').replace('_HQ', '').replace('_FULL', '')
                    
                    if clean_base.lower().startswith(truncated.lower()) and len(clean_base) <= len(video_name):
                        logging.info(f"   ✅ Nalezeno flexibilním hledáním (zkráceno na {truncate_length} znaků): '{filename}'")
                        return True, match
        
        logging.info(f"   ❌ Žádný soubor pro název '{video_name}' nenalezen (ani zkrácený)")
    else:
        logging.warning("   ⚠️ Nepodařilo se získat název videa z widgetu")
    
    return False, None

def save_download_mapping(video_url, downloaded_file, download_dir):
    """Uloží mapování URL -> název souboru pro budoucí skip detekci"""
    try:
        mapping_file = os.path.join(download_dir, "download_mapping.txt")
        file_name = os.path.basename(downloaded_file)
        
        # Zkontrolovat, zda už mapování neexistuje
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
        logging.warning(f"Nepodařilo se uložit mapování: {e}")

def download_video(video_url, video_index, total_videos):
    """Stáhnutí jednoho videa s error handlingem a vylepšenou skip kontrolou podle názvu"""
    import glob
    import os
    
    download_dir = DOWNLOAD_DIR  # Použít správnou configured cestu!
    
    try:
        # Načíst stránku s videem
        driver.get(video_url)
        time.sleep(3)  # Čekání pro načtení stránky
        
        # NOVÝ PŘÍSTUP: Nejdřív zkontrolovat skip detection s načtenou stránkou
        already_downloaded, existing_file = is_video_already_downloaded_by_name(driver, video_url, download_dir)
        
        if already_downloaded:
            logging.info(f"[4/5] ({video_index}/{total_videos}) ⏭️  PŘESKAKUJI - už staženo: {os.path.basename(existing_file)}")
            return True  # Počítáme jako úspěch
        
        logging.info(f"[4/5] ({video_index}/{total_videos}) Navštěvuji {video_url}")
        
        # Stránka už je načtená, jen počkáme na widget
        time.sleep(5)  # Dodatečné čekání pro načtení video widgetu
        
        # OPRAVENÉ selektory pro download tlačítko
        download_selectors = [
            "//span[contains(text(),'Download')]",  # ✅ Hlavní selector - SPAN element
            "//button[contains(text(),'Download')]",
            "//button[contains(text(),'download')]",
            "//a[contains(text(),'Download')]",
            "//a[contains(text(),'download')]",
            "//button[contains(@class,'download')]",
            "//a[contains(@class,'download')]",
            "//span[contains(@class,'download')]",  # Přidáno pro span elementy
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
            # Uložit seznam souborů před kliknutím
            initial_files = set(glob.glob(os.path.join(download_dir, "*")))
            
            download_btn.click()
            logging.info("     → Kliknuto na Download tlačítko...")
            
            # Počkat chvíli a zkontrolovat, jestli se neobjevil popup
            time.sleep(3)
            
            # OPRAVENÉ selektory pro potvrzovací popup pro starší videa
            confirmation_selectors = [
                "//button[contains(text(),'Download')]",  # Druhé download tlačítko v popupu
                "//span[contains(text(),'Download')]",   # Druhé download span v popupu
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
                    # Všechny jsou XPath selektory
                    confirmation_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    # Ověřit, že to není stejné tlačítko jako předtím
                    if confirmation_btn != download_btn:
                        confirmation_btn.click()
                        logging.info("     → Potvrzeno v popup dialogu...")
                        popup_found = True
                        break
                except TimeoutException:
                    continue
            
            if not popup_found:
                logging.info("     → Žádný popup nebyl detekován")
            
            # Čekání na začátek downloadu
            time.sleep(WAIT_AFTER_DOWNLOAD)
            
            # Zkontrolujeme, jestli se objevil nový soubor
            final_files = set(glob.glob(os.path.join(download_dir, "*")))
            new_files = final_files - initial_files
            
            if new_files:
                new_file_path = list(new_files)[0]
                new_file_name = os.path.basename(new_file_path)
                logging.info(f"     ✅ Nový soubor stažen: {new_file_name}")
                
                # Uložit mapování pro budoucí skip detekci
                save_download_mapping(video_url, new_file_path, download_dir)
            else:
                logging.info("     ⏳ Download možná stále probíhá...")
            
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
skipped_downloads = 0

logging.info(f"🚀 Zahajuji stahování {len(video_urls)} videí...")
logging.info("   (Již stažená videa budou automaticky přeskočena)")

for idx, url in enumerate(video_urls, 1):
    # Kontrola, zda už není video stažené (pro statistiky před voláním download_video)
    download_dir = DOWNLOAD_DIR  # Použít správnou configured cestu!
    
    # Krátce načíst stránku pro kontrolu
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
logging.info(f"[5/5] ✅ DOKONČENO! Celkové statistiky:")
logging.info(f"   📥 Nově staženo: {successful_downloads}")
logging.info(f"   ⏭️  Přeskočeno (už staženo): {skipped_downloads}")
logging.info(f"   ❌ Chyby: {failed_downloads}")
logging.info(f"   📊 Celkem zpracováno: {successful_downloads + skipped_downloads + failed_downloads}")

# Zobrazit informace o stažených souborech
download_dir = DOWNLOAD_DIR  # Použít správnou configured cestu!
if os.path.exists(download_dir):
    import glob
    all_videos = []
    for ext in ['*.mp4', '*.mov', '*.avi', '*.mkv', '*.webm']:
        all_videos.extend(glob.glob(os.path.join(download_dir, ext)))
    
    logging.info(f"📁 Celkem videí ve složce downloads: {len(all_videos)}")
    
    # Zobrazit velikost složky
    try:
        total_size = sum(os.path.getsize(f) for f in all_videos if os.path.isfile(f))
        size_gb = total_size / (1024**3)
        logging.info(f"💾 Celková velikost: {size_gb:.2f} GB")
    except:
        pass

logging.info("=" * 60)
driver.quit()
