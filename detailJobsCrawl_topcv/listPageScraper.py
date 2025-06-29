import os
import time
import random
import json
import logging
from datetime import datetime
import psycopg2
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from psycopg2 import sql
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
from urllib.parse import urljoin, urlsplit, urlunsplit

# --- ADDED: Basic Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("list_scraper.log", mode='a'),
        logging.StreamHandler()
    ]
)

# --- Configuration ---
load_dotenv()
DB_TABLE_NAME = 'topcv_jobs_detailed'
MAX_PAGES_TO_SCRAPE = 50 
USER_AGENT = os.getenv('USER_AGENT')
SITE_NAME = "topcv"

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        logging.info("=> Kết nối Database thành công!")
        return conn
    except psycopg2.Error as e:
        logging.error(f"Lỗi kết nối Database: {e}")
        return None

def load_config(site_name="topcv"):
    try:
        with open('sites_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        logging.info(f"Tải config cho '{site_name}' thành công.")
        return config[site_name]
    except (FileNotFoundError, KeyError) as e:
        logging.error(f"Lỗi: Không tìm thấy file config hoặc không có config cho '{site_name}'. Lỗi: {e}") # CHANGED
        return None

def safe_get_text(element, selector):
    tag = element.select_one(selector)
    return tag.get_text(strip=True) if tag else None

# --- ADDED: Function to normalize job URLs ---
# Chuẩn hóa URL để loại bỏ query và fragment, ép scheme về https, netloc và path thành lowercase, và bỏ / dư ở cuối path
def normalize_job_url(raw_url):
    """
    Chuẩn hóa URL một cách toàn diện:
    1. Ép scheme về 'https' để thống nhất.
    2. Chuyển domain (netloc) về chữ thường.
    3. Chuyển đường dẫn (path) về chữ thường.
    4. Xóa dấu gạch chéo (/) dư thừa ở cuối đường dẫn.
    5. Loại bỏ hoàn toàn các tham số truy vấn (query) và fragment.
    """
    parts = urlsplit(raw_url)
    
    # Ép scheme về https, chuyển netloc và path về chữ thường
    scheme = 'https'
    netloc = parts.netloc.lower()
    path = parts.path.lower()
    
    # Bỏ dấu / dư ở cuối path
    if path.endswith('/'):
        path = path[:-1]
        
    # Tạo lại URL đã được chuẩn hóa, bỏ qua query và fragment
    return urlunsplit((scheme, netloc, path, '', ''))

def main():
    logging.info(f"[START] Quét danh sách jobs từ site: {SITE_NAME}")
    config = load_config(SITE_NAME)
    if not config: return

    base_url = config['base_url']
    current_list_page_url = config['list_page_url']
    list_selectors = config['selectors']['list_page']

# --- OPTIONS CHROME / SELENIUM ---
    options = uc.ChromeOptions()
    options.add_argument(f'--user-agent={USER_AGENT}')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')

    # FIXED: Docker-specific Chrome configuration
    if os.environ.get("DOCKER_ENV"):
        logging.info("Detected DOCKER_ENV → force headless, no-sandbox, disable-gpu")
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-features=VizDisplayCompositor')
    else:
        # LOCAL DEVELOPMENT MODE
        local_headless = os.environ.get("LOCAL_HEADLESS", "false").lower() == "true"
        if local_headless:
            logging.info("Local run with headless mode enabled via LOCAL_HEADLESS=true")
            options.add_argument('--headless=new')
        else:
            logging.info("Local run without headless (for debugging in real browser window)")

    # Always disable extensions and automation flags
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')

    # FIXED: Chrome binary detection and driver initialization
    chrome_executable_path = os.environ.get("CHROME_BIN")
    if chrome_executable_path and os.path.exists(chrome_executable_path):
        logging.info(f"Chrome binary found at: {chrome_executable_path}")
        options.binary_location = chrome_executable_path

    logging.info("🚀 Chuẩn bị khởi tạo Chrome driver...")
    
    # FIXED: Explicit browser_executable_path for Docker
    try:
        if os.environ.get("DOCKER_ENV") and chrome_executable_path:
            # In Docker, explicitly specify the browser executable path
            driver = uc.Chrome(
                options=options,
                browser_executable_path=chrome_executable_path
            )
        else:
            # Local development - let undetected-chromedriver auto-detect
            driver = uc.Chrome(options=options)
        
        logging.info("✅ Chrome driver đã khởi tạo thành công.")
    except Exception as e:
        logging.error(f"❌ Lỗi khởi tạo Chrome driver: {e}")
        # ADDED: Fallback mechanism
        if os.environ.get("DOCKER_ENV"):
            logging.info("🔄 Thử fallback với standard ChromeDriver...")
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            
            # Convert uc.ChromeOptions to standard Options
            chrome_options = Options()
            for arg in options.arguments:
                chrome_options.add_argument(arg)
            if hasattr(options, 'binary_location'):
                chrome_options.binary_location = options.binary_location
            
            try:
                service = Service()
                driver = webdriver.Chrome(service=service, options=chrome_options)
                logging.info("✅ Fallback ChromeDriver đã khởi tạo thành công.")
            except Exception as fallback_error:
                logging.error(f"❌ Fallback cũng thất bại: {fallback_error}")
                return
        else:
            return
    
    conn = get_db_connection()

    # --- ADDED: try...finally to ensure resources are always cleaned up ---
    try:
        if not conn:
            return

        current_page = 1
        total_inserted = 0

        while current_page <= MAX_PAGES_TO_SCRAPE:
            logging.info(f"\n[PAGE {current_page}] Đang xử lý: {current_list_page_url}") # CHANGED
            try:
                driver.get(current_list_page_url)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, list_selectors['job_item'])))
                time.sleep(random.uniform(2, 4))
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                jobs = soup.select(list_selectors['job_item'])

                if not jobs:
                    logging.warning("Không tìm thấy job nào trên trang này. Kết thúc.") # CHANGED
                    break

                cur = conn.cursor()
                scrape_date = datetime.now().strftime('%Y-%m-%d')
                insert_count = 0

                for job in jobs:
                    url_tag = job.select_one(list_selectors['job_url'])
                    if not url_tag or not url_tag.get("href"): continue

                    raw_full_url = urljoin(base_url, url_tag["href"])

                    # --- SỬ DỤNG HÀM CHUẨN HÓA URL ---
                    job_url = normalize_job_url(raw_full_url)

                    job_title = safe_get_text(job, list_selectors['job_title'])
                    
                    company = safe_get_text(job, list_selectors['company_name'])
                    salary = safe_get_text(job, list_selectors['salary'])
                    location = safe_get_text(job, list_selectors['location'])
                    post_date = safe_get_text(job, list_selectors['post_date'])
                    if post_date: post_date = post_date.replace("Đăng", "").strip()

                    try:
                        cur.execute(
                            sql.SQL("""
                                INSERT INTO {} (job_url, source_site, job_title, company_name_raw_list, salary_raw_list, location_raw_list, post_date_raw_list, scrape_date, status)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (job_url) DO NOTHING;
                            """).format(sql.Identifier(DB_TABLE_NAME)),
                            (job_url, SITE_NAME, job_title, company, salary, location, post_date, scrape_date, 'pending_details')
                        )
                        if cur.rowcount > 0:
                            insert_count += 1
                            total_inserted += 1
                    except Exception as e:
                        logging.error(f"Lỗi DB khi insert job {job_url}: {e}") # CHANGED
                        conn.rollback()
                    else:
                        conn.commit()
                cur.close()
                logging.info(f"[OK] Thêm mới {insert_count} job từ trang này.") # CHANGED

                next_tag = soup.select_one(list_selectors['next_page_button'])
                if next_tag:
                    next_href = next_tag.get('data-href') or next_tag.get('href')
                    if not next_href or 'javascript:void(0)' in next_href:
                        logging.info("[DONE] Nút 'Next' không hợp lệ hoặc đã đến trang cuối.")
                        break
                    current_list_page_url = urljoin(base_url, next_href)
                else:
                    logging.info("[DONE] Không tìm thấy nút 'Next'. Đã đến trang cuối.") # CHANGED
                    break

                current_page += 1
                time.sleep(random.uniform(6, 12))

            except TimeoutException:
                logging.warning("Timeout trang, thử lại sau 20s...") # CHANGED
                time.sleep(20)
                continue
            except Exception as e:
                logging.error(f"Lỗi không xác định trong vòng lặp: {e}", exc_info=True) # CHANGED
                break

        logging.info(f"\n[TOTAL] Tổng số job mới được thêm vào DB: {total_inserted}") # CHANGED
    finally:
        # --- ADDED: Cleanup block ---
        if driver:
            driver.quit()
            logging.info("Đã đóng trình duyệt Selenium.")
        if conn:
            conn.close()
            logging.info("Đã đóng kết nối Database.")

if __name__ == "__main__":
    main()