# list_page_scraper.py (VERSION FRAMEWORK - Reads from config)

import os
import time
import random
import json
from datetime import datetime
from urllib.parse import urljoin

import psycopg2
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from psycopg2 import sql
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc

# --- 1. Cấu hình ---
load_dotenv()
# Bỏ các hằng số URL, chúng sẽ được đọc từ config
DB_TABLE_NAME = 'topcv_jobs_detailed'
MAX_PAGES_TO_SCRAPE = 10 
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

# --- 2. Các hàm Helper ---
def get_db_connection():
    # Giữ nguyên hàm này
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except psycopg2.Error as e:
        print(f"Lỗi kết nối Database: {e}")
        return None

def load_config(site_name="topcv"): # Mặc định là topcv
    """Tải cấu hình cho một site cụ thể từ file JSON."""
    try:
        with open('sites_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config[site_name]
    except (FileNotFoundError, KeyError):
        print(f"Lỗi: Không tìm thấy file 'sites_config.json' hoặc không có cấu hình cho '{site_name}'.")
        return None

def safe_get_text(element, selector):
    """Lấy text từ element con một cách an toàn."""
    tag = element.select_one(selector)
    return tag.get_text(strip=True) if tag else None

# --- 3. Hàm chính ---
def main():
    SITE_NAME = "topcv" # Sau này có thể truyền vào từ command line
    print(f"Bắt đầu Script (Framework): Càn quét trang danh sách cho '{SITE_NAME}'...")
    
    config = load_config(SITE_NAME)
    if not config:
        return
        
    # Lấy các thông tin cấu hình cần thiết
    base_url = config['base_url']
    initial_url = config['list_page_url']
    list_selectors = config['selectors']['list_page']

    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument(f'--user-agent={USER_AGENT}')
        options.add_argument('--window-size=1920,1080')
        print("Khởi tạo Selenium WebDriver...")
        driver = uc.Chrome(options=options)
        print("WebDriver đã được khởi tạo.")
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi khởi tạo WebDriver: {e}")
        return

    conn = get_db_connection()
    if not conn:
        if driver: driver.quit()
        return

    current_page_num = 1
    current_list_page_url = initial_url
    jobs_inserted_this_session = 0

    while current_page_num <= MAX_PAGES_TO_SCRAPE:
        print(f"\n--- Đang quét trang: {current_page_num} | URL: {current_list_page_url} ---")
        
        try:
            driver.get(current_list_page_url)
            WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, list_selectors['job_item'])))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))
            
            soup_list = BeautifulSoup(driver.page_source, 'html.parser')
            job_items = soup_list.select(list_selectors['job_item'])
            
            if not job_items:
                print(f"Không tìm thấy job nào trên trang {current_page_num}. Kết thúc.")
                break

            print(f"Tìm thấy {len(job_items)} jobs trên trang.")
            
            scrape_date = datetime.now().strftime('%Y-%m-%d')
            cur = conn.cursor()
            page_insert_count = 0
            for item in job_items:
                # Lấy URL trước tiên
                url_tag = item.select_one(list_selectors['job_url'])
                if not url_tag or not url_tag.get('href'):
                    continue
                job_url = urljoin(base_url, url_tag['href'])

                # Lấy các thông tin khác bằng hàm helper
                job_title = safe_get_text(item, list_selectors['job_title'])
                company_name = safe_get_text(item, list_selectors['company_name'])
                salary_raw = safe_get_text(item, list_selectors['salary'])
                location_raw = safe_get_text(item, list_selectors['location'])
                post_date_raw = safe_get_text(item, list_selectors['post_date'])
                if post_date_raw: post_date_raw = post_date_raw.replace('Đăng','').strip()

                try:
                    # Thêm source_site vào DB
                    cur.execute(
                        sql.SQL("""
                            INSERT INTO {} (job_url, source_site, job_title, company_name_raw_list, salary_raw_list, location_raw_list, post_date_raw_list, scrape_date, status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (job_url) DO NOTHING;
                        """).format(sql.Identifier(DB_TABLE_NAME)),
                        (job_url, SITE_NAME, job_title, company_name, salary_raw, location_raw, post_date_raw, scrape_date, 'pending_details')
                    )
                    if cur.rowcount > 0:
                        page_insert_count += 1
                        jobs_inserted_this_session += 1
                except psycopg2.Error as e:
                    print(f"Lỗi khi INSERT vào DB: {e}")
                    conn.rollback()
                else:
                    conn.commit()
            cur.close()
            print(f"Đã thêm {page_insert_count} job mới từ trang này.")
            
            next_page_tag = soup_list.select_one(list_selectors['next_page_button'])
            if next_page_tag:
                # Lấy href từ data-href hoặc href
                next_page_href = next_page_tag.get('data-href') or next_page_tag.get('href')
                if next_page_href:
                    current_list_page_url = urljoin(base_url, next_page_href)
                else:
                    print("Nút 'Next' không có href. Kết thúc.")
                    break
            else:
                print("Không tìm thấy link 'Next' page. Đã đến trang cuối cùng. Kết thúc quét.")
                break

            current_page_num += 1
            
            if current_page_num % 20 == 0:
                long_sleep = random.uniform(60, 90)
                print(f"Đã hoàn thành một chặng 20 trang. Nghỉ dài {long_sleep:.1f} giây...")
                time.sleep(long_sleep)
            else:
                sleep_duration = random.uniform(7, 12)
                print(f"Đã xử lý xong trang. Nghỉ {sleep_duration:.1f} giây trước khi sang trang tiếp theo.")
                time.sleep(sleep_duration)

        except TimeoutException:
            print(f"Lỗi Timeout khi chờ trang {current_page_num}. Thử lại sau 30 giây...")
            time.sleep(30)
            continue
        except Exception as e:
            print(f"Lỗi không xác định khi quét trang {current_page_num}: {e}")
            break

    print("\n--- HOÀN TẤT QUÁ TRÌNH CÀN QUÉT ---")
    print(f"Tổng số job mới đã được thêm vào DB trong phiên này: {jobs_inserted_this_session}")
    if conn: conn.close()
    if driver: driver.quit()
    print("=> Đã đóng kết nối DB và WebDriver.")

if __name__ == "__main__":
    main()