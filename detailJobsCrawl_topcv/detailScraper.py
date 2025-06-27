# detail_worker_scraper.py (Updated with better fallback, brand job detection, and logging)

import os
import re
import time
import random
import json
import logging
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

# --- Logging ---
logging.basicConfig(
    filename="scraper.log",
    filemode='a',
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- 1. Load config + .env ---
load_dotenv()
DB_TABLE_NAME = 'topcv_jobs_detailed'
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

# --- 2. Helpers ---
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        conn.autocommit = False
        logging.info("=> Kết nối Database thành công!")
        return conn
    except psycopg2.Error as e:
        logging.error(f"Lỗi kết nối Database: {e}")
        return None

def load_config(site_name="topcv"):
    try:
        with open('sites_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config[site_name]
    except (FileNotFoundError, KeyError):
        logging.error(f"Lỗi: Không tìm thấy file 'sites_config.json' hoặc không có cấu hình cho '{site_name}'.")
        return None

# --- 3. Parsers ---
def parse_company_info(soup, selector_cfg):
    return {
        "company_name_detail": get_text(soup, selector_cfg.get("company_name")),
        "company_scale": get_text(soup, selector_cfg.get("company_scale")),
        "company_field": get_text(soup, selector_cfg.get("company_field")),
        "company_full_address": get_text(soup, selector_cfg.get("company_address")),
    }

def parse_general_info(soup, config):
    result = {"job_level": None, "education_level": None, "quantity_needed": None,
              "employment_type": None, "gender_requirement": None}
    container = soup.select_one(config.get("container", ""))
    if not container: return result
    for group in container.select(".box-general-group"):
        title_el = group.select_one(".box-general-group-info-title")
        value_el = group.select_one(".box-general-group-info-value")
        if not title_el or not value_el: continue
        title = title_el.get_text(strip=True)
        value = value_el.get_text(strip=True)
        if "Cấp bậc" in title: result["job_level"] = value
        elif "Học vấn" in title: result["education_level"] = value
        elif "Số lượng tuyển" in title: result["quantity_needed"] = value
        elif "Hình thức làm việc" in title: result["employment_type"] = value
        elif "Giới tính" in title: result["gender_requirement"] = value
    return result

def parse_job_content(soup, config):
    result = {"job_description_text": None, "job_requirements_text": None,
              "job_benefits_text": None, "working_time_text": None}
    container = soup.select_one(config.get("container", ""))
    if not container: return result
    for item in container.select(".job-description__item"):
        title = item.find("h3")
        content = item.select_one(".job-description__item--content")
        if not title or not content: continue
        t_text = title.get_text(strip=True)
        c_text = content.get_text(strip=True)
        if "Mô tả công việc" in t_text: result["job_description_text"] = c_text
        elif "Yêu cầu ứng viên" in t_text: result["job_requirements_text"] = c_text
        elif "Quyền lợi" in t_text: result["job_benefits_text"] = c_text
        elif "Thời gian làm việc" in t_text: result["working_time_text"] = c_text
    return result

def parse_skills_tags(soup, config):
    result = {
        "related_job_categories": [],
        "required_skills_tags": [],
        "preferred_skills_tags": []
    }

    for section in soup.select(config.get("container", ".box-category")):
        title_el = section.select_one("div.box-title")
        if not title_el: continue
        title = title_el.get_text(strip=True).lower()
        tags = [el.get_text(strip=True) for el in section.select("span.box-category-tag")]
        if "cần có" in title:
            result["required_skills_tags"] = tags
        elif "nên có" in title:
            result["preferred_skills_tags"] = tags
        elif "liên quan" in title:
            result["related_job_categories"] = tags

    if not any(result.values()):
        logging.warning("[!] Không tìm thấy kỹ năng ở job này")

    return result

def parse_application_deadline(soup, selector):
    tag = soup.select_one(selector)
    if tag:
        if match := re.search(r'(\d{2}/\d{2}/\d{4})', tag.get_text(strip=True)):
            return match.group(1)
    return None

def get_text(soup, selector):
    tag = soup.select_one(selector)
    return tag.get_text(strip=True) if tag else None

# --- 4. Main worker ---
def main_worker():
    logging.info("[Start] Worker xử lý chi tiết job theo config...")
    driver, conn = None, None
    try:
        options = uc.ChromeOptions()
        options.add_argument(f'--user-agent={USER_AGENT}')
        options.add_argument('--window-size=1920,1080')
        driver = uc.Chrome(options=options)
        conn = get_db_connection()
        if not conn: return

        while True:
            cur = conn.cursor()
            cur.execute(sql.SQL("SELECT job_id, job_url, source_site FROM {} WHERE status = 'pending_details' ORDER BY job_id LIMIT 1;").format(sql.Identifier(DB_TABLE_NAME)))
            job_to_process = cur.fetchone(); cur.close()

            if not job_to_process:
                logging.info("[WAIT] Không còn job nào. Nghỉ 10 phút..."); time.sleep(600); continue

            job_id, detail_url, source_site = job_to_process
            logging.info(f"[PROCESS] Job ID: {job_id} | URL: {detail_url[:70]}...")

            if "/brand/" in detail_url:
                logging.warning(f"[SKIP] Job ID {job_id} thuộc brand, bỏ qua.")
                cur = conn.cursor()
                cur.execute(sql.SQL("UPDATE {} SET status = 'skipped' WHERE job_id = %s;").format(sql.Identifier(DB_TABLE_NAME)), (job_id,))
                conn.commit(); cur.close()
                continue

            config = load_config(source_site)
            if not config: continue

            detail_cfg = config['selectors']['detail_page']

            try:
                driver.get(detail_url)
                logging.info("[WAIT] Chờ tải trang trong 30s...")
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, detail_cfg['wait_for_element'])))
                sleep_time = round(random.uniform(2, 4), 2)
                logging.info(f"[SLEEP] Nghỉ {sleep_time}s để tránh bị chặn...")
                time.sleep(sleep_time)
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                parsed_data = {
                    **parse_company_info(soup, detail_cfg['selectors']['company_info']),
                    **parse_general_info(soup, detail_cfg['selectors']['general_info']),
                    **parse_job_content(soup, detail_cfg['selectors']['job_content']),
                    **parse_skills_tags(soup, detail_cfg['selectors']['skills_categories']),
                    "application_deadline_date": parse_application_deadline(soup, detail_cfg['selectors']['application_deadline']),
                    "status": "completed"
                }

                set_clauses = sql.SQL(', ').join([sql.SQL("{} = %s").format(sql.Identifier(k)) for k in parsed_data.keys()])
                values = list(parsed_data.values()) + [job_id]

                update_query = sql.SQL("UPDATE {} SET {} WHERE job_id = %s;").format(sql.Identifier(DB_TABLE_NAME), set_clauses)
                cur = conn.cursor(); cur.execute(update_query, values); conn.commit(); cur.close()
                logging.info(f"[OK] Đã cập nhật chi tiết Job ID: {job_id}")

            except Exception as e:
                logging.error(f"[ERR] Lỗi Job ID {job_id}: {e}")
                conn.rollback()
                cur = conn.cursor()
                cur.execute(sql.SQL("UPDATE {} SET status = 'error' WHERE job_id = %s;").format(sql.Identifier(DB_TABLE_NAME)), (job_id,))
                conn.commit(); cur.close()

            sleep_time = round(random.uniform(25, 50), 2)
            logging.info(f"[SLEEP] Nghỉ {sleep_time}s trước khi xử lý job kế tiếp...")
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        logging.info("\n[STOP] Đã dừng bằng tay (Ctrl+C)")
    except Exception as e:
        logging.critical(f"[FATAL] Lỗi tổng thể: {e}")
    finally:
        if conn: conn.close()
        if driver: driver.quit()

if __name__ == "__main__":
    main_worker()
