# detail_worker_scraper.py (VERSION FINAL - Robust & Resilient)

import os
import re
import time
import random
from datetime import datetime

import psycopg2
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from psycopg2 import sql
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import undetected_chromedriver as uc

# --- 1. Cấu hình (Giữ nguyên) ---
load_dotenv()
DB_TABLE_NAME = 'topcv_jobs_detailed'
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


# --- 2. Kết nối Database (Giữ nguyên) ---
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        # Tắt autocommit để có thể rollback khi cần
        conn.autocommit = False
        print("=> Kết nối Database thành công!")
        return conn
    except psycopg2.Error as e:
        print(f"Lỗi kết nối Database: {e}")
        return None

# --- 3. Các hàm Helper Parse Detail (Lấy từ notebook gốc của em) ---
# ... (Toàn bộ các hàm parse_... của em nằm ở đây, anh sẽ rút gọn để dễ nhìn)
def parse_company_info_from_detail(soup_detail):
     company_info = {'company_name_detail': None, 'company_scale': None, 'company_field': None, 'company_full_address': None}
     container = soup_detail.find("div", class_="job-detail__company--information")
     if not container: return company_info
     if name_tag := container.select_one("div.company-name-label a.name"): company_info['company_name_detail'] = name_tag.get_text(strip=True)
     if scale_item := container.find("div", class_="company-scale"): 
         if val_tag := scale_item.find("div", class_="company-value"): company_info['company_scale'] = val_tag.get_text(strip=True)
     if field_item := container.find("div", class_="company-field"):
         if val_tag := field_item.find("div", class_="company-value"): company_info['company_field'] = val_tag.get_text(strip=True)
     if address_item := container.find("div", class_="company-address"):
         if val_div := address_item.find("div", class_="company-value"):
             company_info['company_full_address'] = val_div.get('data-original-title', val_div.get_text(strip=True))
     return company_info

def parse_general_job_info_from_detail(soup_detail):
     general_info = {'job_level': None, 'education_level': None, 'quantity_needed': None, 'employment_type': None, 'gender_requirement': None}
     box = soup_detail.find("div", class_="job-detail__body-right--box-general")
     if not box: return general_info
     for group in box.find_all("div", class_="box-general-group"):
         if title_tag := group.find("div", class_="box-general-group-info-title"):
             if value_tag := group.find("div", class_="box-general-group-info-value"):
                 title, value = title_tag.get_text(strip=True), value_tag.get_text(strip=True)
                 if "Cấp bậc" in title: general_info['job_level'] = value
                 elif "Học vấn" in title: general_info['education_level'] = value
                 elif "Số lượng tuyển" in title: general_info['quantity_needed'] = value 
                 elif "Hình thức làm việc" in title: general_info['employment_type'] = value
                 elif "Giới tính" in title: general_info['gender_requirement'] = value
     return general_info

def parse_skills_categories_from_detail(soup_detail):
     skills_cats = {'related_job_categories': [], 'required_skills_tags': [], 'preferred_skills_tags': []}
     container = soup_detail.find("div", class_="job-detail__body-right--box-category")
     if not container: return skills_cats
     for box in container.find_all("div", class_="box-category"):
         if title_tag := box.find("div", class_="box-title"):
             if tags_container := box.find("div", class_="box-category-tags"):
                 title = title_tag.get_text(strip=True)
                 if "Danh mục Nghề" in title: 
                     skills_cats['related_job_categories'] = [a.get_text(strip=True) for a in tags_container.select("a.box-category-tag")] or []
                 elif "Kỹ năng cần có" in title: 
                     skills_cats['required_skills_tags'] = [s.get_text(strip=True) for s in tags_container.select("span.box-category-tag")] or []
                 elif "Kỹ năng nên có" in title: 
                     skills_cats['preferred_skills_tags'] = [s.get_text(strip=True) for s in tags_container.select("span.box-category-tag")] or []
     return skills_cats

def parse_job_content_from_detail(soup_detail):
    content = {'job_description_text': None, 'job_requirements_text': None, 'job_benefits_text': None, 'working_time_text': None}
    content_container = soup_detail.select_one("div.job-detail__information-detail--content div.job-description")
    if not content_container: return content
    for item in content_container.find_all("div", class_="job-description__item", recursive=False):
        h3_tag = item.find("h3")
        item_content_div = item.find("div", class_="job-description__item--content")
        if h3_tag and item_content_div:
            section_title = h3_tag.get_text(strip=True)
            text_parts = []
            if "Thời gian làm việc" in section_title:
                list_items = item_content_div.find_all("div", class_="job-description__item--content-list")
                if list_items:
                    for li in list_items:
                        if li_text := li.get_text(strip=True): text_parts.append(li_text)
                elif item_content_div.get_text(strip=True):
                     text_parts.append(item_content_div.get_text(strip=True))
                section_text = "\n".join(text_parts) if text_parts else None
                content['working_time_text'] = section_text
            else:
                for element in item_content_div.children:
                    if isinstance(element, str) and element.strip(): text_parts.append(element.strip())
                    elif element.name == 'p' and element.get_text(strip=True): text_parts.append(element.get_text(strip=True))
                    elif element.name in ['ul', 'ol']:
                        for li_tag in element.find_all('li', recursive=False): 
                            if li_text_content := li_tag.get_text(strip=True): text_parts.append(f"- {li_text_content}")
                section_text = "\n".join(text_parts) if text_parts else None
                if "Mô tả công việc" in section_title: content['job_description_text'] = section_text
                elif "Yêu cầu ứng viên" in section_title: content['job_requirements_text'] = section_text
                elif "Quyền lợi" in section_title: content['job_benefits_text'] = section_text
    return content

def parse_application_deadline_from_detail(soup_detail):
     if deadline_tag := soup_detail.find("div", class_="job-detail__information-detail--actions-label"):
         if match := re.search(r'(\d{2}/\d{2}/\d{4})', deadline_tag.get_text(strip=True)):
             return match.group(1)
     return None


# --- 4. Vòng lặp chính của Worker ---
def main_worker():
    print("Bắt đầu Script 2 (Final): Worker xử lý chi tiết job...")
    
    driver = None
    conn = None
    
    try:
        # Khởi tạo WebDriver và DB Connection một lần bên ngoài vòng lặp
        options = uc.ChromeOptions()
        options.add_argument(f'--user-agent={USER_AGENT}')
        options.add_argument('--window-size=1920,1080')
        driver = uc.Chrome(options=options)
        conn = get_db_connection()
        if not conn:
            return

        while True: # Vòng lặp vô tận để liên tục kiểm tra và xử lý
            cur = conn.cursor()
            
            # Lấy 1 job đang chờ xử lý
            cur.execute(sql.SQL("SELECT job_id, job_url FROM {} WHERE status = 'pending_details' ORDER BY job_id LIMIT 1;").format(sql.Identifier(DB_TABLE_NAME)))
            job_to_process = cur.fetchone()
            cur.close() # Đóng con trỏ ngay sau khi lấy dữ liệu
            
            if not job_to_process:
                print("Không còn job nào đang chờ. Tạm nghỉ 10 phút rồi kiểm tra lại...")
                time.sleep(600) # Nghỉ 10 phút
                continue
            
            job_id, detail_url = job_to_process
            print(f"\n=> Đang xử lý Job ID: {job_id}, URL: {detail_url[:70]}")

            # *** BỘ LỌC GIAO DIỆN ***
            if "/brand/" in detail_url:
                print("   [BỎ QUA] Đây là trang 'brand', có giao diện khác. Đánh dấu là 'skipped'.")
                cur = conn.cursor()
                cur.execute(sql.SQL("UPDATE {} SET status = %s WHERE job_id = %s;").format(sql.Identifier(DB_TABLE_NAME)), ('skipped_brand_page', job_id))
                conn.commit()
                cur.close()
                # Nghỉ một chút rồi sang job tiếp theo
                time.sleep(random.uniform(1, 2))
                continue # Chuyển ngay sang vòng lặp tiếp theo
            # *** KẾT THÚC BỘ LỌC ***

            job_status = 'completed'
            try:
                # Truy cập trang chi tiết
                driver.get(detail_url)
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-detail__information-detail--content")))
                time.sleep(random.uniform(3, 5)) # Chờ thêm cho chắc
                
                detail_html = driver.page_source
                soup_detail = BeautifulSoup(detail_html, 'html.parser')
                
                # Parse tất cả thông tin
                print("   - Đang parse thông tin...")
                company_info = parse_company_info_from_detail(soup_detail)
                general_info = parse_general_job_info_from_detail(soup_detail)
                skills_cats = parse_skills_categories_from_detail(soup_detail)
                content_info = parse_job_content_from_detail(soup_detail)
                deadline_str = parse_application_deadline_from_detail(soup_detail)

                # Tổng hợp dữ liệu để UPDATE
                update_data = {
                    **company_info, **general_info, **skills_cats,
                    **content_info, 'application_deadline_date': deadline_str
                }
                
                print("   - Chuẩn bị dữ liệu để ghi vào DB...")
                # Tạo câu lệnh UPDATE động
                set_clauses = sql.SQL(', ').join([
                    sql.SQL("{} = %s").format(sql.Identifier(key)) for key in update_data.keys()
                ])
                
                values = list(update_data.values())
                values.append(job_id) # Thêm job_id vào cuối cho mệnh đề WHERE

                # Thêm status vào câu lệnh UPDATE
                final_set_clauses = sql.SQL("{}, status = %s").format(set_clauses)
                values.insert(-1, job_status) # Thêm 'completed' vào list values

                update_query = sql.SQL("UPDATE {} SET {} WHERE job_id = %s;").format(
                    sql.Identifier(DB_TABLE_NAME),
                    final_set_clauses
                )
                
                cur = conn.cursor()
                cur.execute(update_query, values)
                conn.commit()
                print(f"   [THÀNH CÔNG] Đã cập nhật chi tiết cho Job ID: {job_id}")

            except Exception as e:
                print(f"   [LỖI] Khi xử lý Job ID {job_id}: {e}")
                conn.rollback() # Rất quan trọng: Hủy bỏ mọi thay đổi nếu có lỗi
                job_status = 'error' # Đánh dấu là lỗi
                
                # Ghi nhận lỗi vào DB
                cur = conn.cursor()
                cur.execute(sql.SQL("UPDATE {} SET status = %s WHERE job_id = %s;").format(sql.Identifier(DB_TABLE_NAME)), (job_status, job_id))
                conn.commit()
            
            finally:
                if 'cur' in locals() and not cur.closed:
                    cur.close()

            # Nghỉ một khoảng thời gian dài và ngẫu nhiên để tránh bị block
            sleep_duration = random.uniform(25, 50)
            print(f"   Nghỉ {sleep_duration:.1f} giây trước khi xử lý job tiếp theo...")
            time.sleep(sleep_duration)

    except KeyboardInterrupt:
        print("\nĐã nhận lệnh dừng (Ctrl+C). Kết thúc worker.")
    except Exception as e:
        print(f"\nLỗi không xác định trong vòng lặp chính: {e}")
    finally:
        # Dọn dẹp tài nguyên khi kết thúc
        print("Đang dọn dẹp tài nguyên...")
        if conn:
            conn.close()
            print("Đã đóng kết nối Database.")
        if driver:
            driver.quit()
            print("Đã đóng WebDriver.")

if __name__ == "__main__":
    main_worker()