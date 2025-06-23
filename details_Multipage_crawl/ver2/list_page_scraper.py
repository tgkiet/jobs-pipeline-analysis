import os
import time
import random
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

load_dotenv()
TARGET_URL_BASE = "https://www.topcv.vn"
INITIAL_TARGET_URL = "https://www.topcv.vn/tim-viec-lam-moi-nhat-tai-ho-chi-minh-l2" 
MAX_PAGES_TO_SCRAPE = 19 # Đặt mục tiêu cao nhất có thể
DB_TABLE_NAME = 'topcv_jobs_detailed'
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

# --- 2. Kết nối Database ---
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        print("=> Kết nối Database thành công!")
        return conn
    except psycopg2.Error as e:
        print(f"Lỗi kết nối Database: {e}")
        return None

# --- 3. Hàm chính ---
def main():
    print("Bắt đầu Script 1 (v6 - Strictly Original Logic): Càn quét trang danh sách...")
    
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
    current_list_page_url = INITIAL_TARGET_URL
    jobs_inserted_this_session = 0

    while current_page_num <= MAX_PAGES_TO_SCRAPE:
        print(f"\n--- Đang quét trang: {current_page_num} | URL: {current_list_page_url} ---")
        
        try:
            driver.get(current_list_page_url)
            WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.box-job-list div.job-item-search-result"))
            )
            # Gia cố bằng cách cuộn trang - không thay đổi logic tìm dữ liệu
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))
            
            soup_list = BeautifulSoup(driver.page_source, 'html.parser')
            # Selector hoàn toàn là của em, không thay đổi
            job_items = soup_list.select('div.box-job-list div.job-item-search-result')
            
            if not job_items:
                print(f"Không tìm thấy job nào trên trang {current_page_num}. Kết thúc.")
                break

            print(f"Tìm thấy {len(job_items)} jobs trên trang.")
            
            # Phần xử lý và INSERT vào DB giữ nguyên
            # ...
            scrape_date = datetime.now().strftime('%Y-%m-%d')
            cur = conn.cursor()
            page_insert_count = 0
            for item in job_items:
                # Toàn bộ logic trích xuất này là của em
                job_url, job_title, company_name, salary_raw, location_raw, post_date_raw = None, None, None, None, None, None
                
                if title_a_tag := item.select_one('h3.title a, h3.title.highlight a'):
                    job_title = title_a_tag.get_text(strip=True)
                    href = title_a_tag.get('href')
                    if href: job_url = urljoin(TARGET_URL_BASE, href)
                if not job_url: continue
                if company_a := item.select_one('a.company, a.company.job-pro span.company-name'): company_name = company_a.get_text(strip=True)
                if salary_tag := item.find(['span','div','p','label'], class_='title-salary'): salary_raw = salary_tag.get_text(strip=True).replace('\\n','').strip()
                if location_label := item.find('label', class_='address'): location_raw = location_label.get_text(strip=True)
                if date_label := item.find('label', class_='label-update'): post_date_raw = date_label.get_text(strip=True).replace('Đăng','').strip()

                try:
                    cur.execute(
                        sql.SQL("""
                            INSERT INTO {} (job_url, job_title, company_name_raw_list, salary_raw_list, location_raw_list, post_date_raw_list, scrape_date, status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (job_url) DO NOTHING;
                        """).format(sql.Identifier(DB_TABLE_NAME)),
                        (job_url, job_title, company_name, salary_raw, location_raw, post_date_raw, scrape_date, 'pending_details')
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
            
            # Đặt logic nghỉ ngơi ở ĐÚNG VỊ TRÍ, SAU KHI xử lý xong trang
            # Kiểm tra trên trang vừa hoàn thành (current_page_num)
            if current_page_num % 20 == 0 and current_page_num > 0:
                long_sleep = random.uniform(60, 90)
                print(f"Đã hoàn thành chặng trang thứ {current_page_num}. Nghỉ dài {long_sleep:.1f} giây...")
                time.sleep(long_sleep)
            else:
                sleep_duration = random.uniform(7, 12)
                print(f"Đã xử lý xong trang. Nghỉ {sleep_duration:.1f} giây trước khi sang trang tiếp theo.")
                time.sleep(sleep_duration)

            # *** PHỤC HỒI 100% LOGIC CHUYỂN TRANG GỐC CỦA EM ***
            next_page_tag = soup_list.select_one("ul.pagination a[rel='next'][data-href]")
            if next_page_tag:
                current_list_page_url = urljoin(TARGET_URL_BASE, next_page_tag['data-href'])
            else:
                print("Không tìm thấy link 'Next' page. Đã đến trang cuối cùng. Kết thúc quét.")
                break

            current_page_num += 1
            
            # Gia cố bằng chiến lược nghỉ ngơi thông minh
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

    # --- Dọn dẹp ---
    print("\n--- HOÀN TẤT QUÁ TRÌNH CÀN QUÉT ---")
    print(f"Tổng số job mới đã được thêm vào DB trong phiên này: {jobs_inserted_this_session}")
    if conn: conn.close()
    if driver: driver.quit()
    print("=> Đã đóng kết nối DB và WebDriver.")


if __name__ == "__main__":
    main()