# The First Personal Project: Phân tích Thị trường Việc làm tại TP.HCM
# Roles: Data Engineer, Data Analyst


/jobs-pipeline-analysis/crawlBasic_firstpage
=> dùng để crawl thông tin cơ bản của một jobs ở trang đầu tiên của website TopCV

/jobs-pipeline-analysis/crawlBasic_Multipage
=> dùng để crawl thông tin cơ bản của một jobs, crawl được nhiều trang của website TopCV

/jobs-pipeline-analysis/topcv_details_Multipage_crawl
=> dùng để crawl chi tiết các jobs ở nhiều trang của website TopCV
    ver1: gộp tất cả logic vào 1 ipynb (khó hiểu, khó quản lý)
    ver2: tách từng phần dễ hiểu dễ quản lý

/jobs-pipeline-analysis/detailJobsCrawl
=> dùng để tách biệt rõ ràng các luồng xử lý hơn nữa, nhằm khi cần crawl thêm các website khác


# 📦 detailJobsCrawl_topcv

## 📌 Mục tiêu
Xây dựng một pipeline crawler để thu thập tin tuyển dụng từ TopCV.vn (bao gồm danh sách và chi tiết), lưu trữ vào cơ sở dữ liệu PostgreSQL.  
Mục đích chính: phục vụ phân tích dữ liệu thị trường việc làm tại Việt Nam.

---

## ⚙️ Yêu cầu cài đặt

**1️⃣ Tạo file `.env` trong thư mục dự án**

Ví dụ:
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36

---

**2️⃣ Cài đặt Python packages**
pip install -r requirements.txt

---

## 💾 Database

- Sử dụng PostgreSQL
- Tên bảng: `topcv_jobs_detailed`
- Schema có sẵn trong file **jobs_detailed.sql**

Để tạo bảng trong DB, có thể chạy:

```sql
\i jobs_detailed.sql
trong psql hoặc tool như pgAdmin.

🚀 Cách chạy
🔹 Bước 1. Crawl danh sách job

python3 listPageScraper.py

Thu thập URL và thông tin sơ bộ của job
Lưu vào bảng với status pending_details

Bước 2. Crawl chi tiết job

python3 detailScraper.py

Lấy chi tiết thông tin từng job (mô tả, yêu cầu, kỹ năng)
Cập nhật vào bảng

🗂️ File cấu hình
✅ sites_config.json
Chứa các selector CSS cho trang list và trang detail.

📝 Log
Các hoạt động và lỗi được ghi vào: scraper.log





