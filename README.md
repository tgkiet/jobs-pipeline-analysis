# 📊 The First Personal Project: Phân tích Thị trường Việc làm tại TP.HCM

**Roles:** Data Engineer, Data Analyst

---

## 📁 Cấu trúc các thư mục chính

```
/phase1/crawlBasic_firstpage
    → Crawl thông tin cơ bản của một job ở trang đầu tiên của TopCV

/phase1/crawlBasic_Multipage
    → Crawl thông tin cơ bản của nhiều job, nhiều trang TopCV

/phase2/topcv_details_Multipage_crawl
    → Crawl chi tiết các job ở nhiều trang TopCV
        ver1: Gộp tất cả logic vào 1 ipynb (khó quản lý)
        ver2: Tách từng phần, dễ hiểu hơn

/detailJobsCrawl_topcv
    → Tách biệt rõ các luồng xử lý, dễ mở rộng cho nhiều website khác
```

---

# 📦 detailJobsCrawl_topcv

**Vietnam Job Scraper for TopCV.vn**  
Thu thập dữ liệu tin tuyển dụng (danh sách + chi tiết) từ TopCV.vn và lưu vào PostgreSQL để phục vụ phân tích nhu cầu việc làm tại Việt Nam.

---

## 🎯 Mục tiêu

- Crawl danh sách tin tuyển dụng từ TopCV (list page)
- Crawl chi tiết tin tuyển dụng (detail page)
- Lưu dữ liệu vào PostgreSQL
- Tích hợp `.env` để quản lý cấu hình dễ dàng

---

## 📌 Cấu trúc thư mục `detailJobsCrawl_topcv/`

```
detailJobsCrawl_topcv/
│
├── detailScraper.py         # Crawl chi tiết job
├── listPageScraper.py       # Crawl danh sách job
├── jobs_detailed.sql        # SQL tạo bảng trong PostgreSQL
├── sites_config.json        # Selectors & cấu hình crawl
├── scraper.log              # File log
├── requirements.txt         # Danh sách Python package
├── .env                     # Biến môi trường
└── README.md                # Hướng dẫn sử dụng
```

---

## ⚙️ Yêu cầu

- Python 3.8+
- PostgreSQL (cài sẵn và đang chạy)
- Tài khoản PostgreSQL có quyền kết nối và insert

---

## 💾 Database

- **Tên bảng mặc định:** `topcv_jobs_detailed`
- ✅ Tạo bảng bằng script SQL có sẵn trong file `jobs_detailed.sql`

---

## 🗂️ Cài đặt môi trường

### 1️⃣ Clone repo

```sh
git clone <repo_link>
cd detailJobsCrawl_topcv
```

---

### 2️⃣ Tạo file `.env`

Với nội dung mẫu:

```env
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36
```

📌 Thay thế giá trị theo cấu hình của bạn.

---

### 3️⃣ Cài Python packages

```sh
pip install -r requirements.txt
```

---

## 🚀 Cách sử dụng

### ✅ Crawl danh sách tin tuyển dụng

```sh
python3 listPageScraper.py
```

- Thu thập danh sách job URL
- Lưu vào PostgreSQL với `status = 'pending_details'`

---

### ✅ Crawl chi tiết tin tuyển dụng

```sh
python3 detailScraper.py
```

- Đọc `job_url` từ DB với `status='pending_details'`
- Trích xuất chi tiết tin tuyển dụng
- Cập nhật DB với thông tin chi tiết và đổi `status='completed'`

---

## 📈 Workflow gợi ý

1. Chạy `listPageScraper.py` để crawl danh sách nhiều page  
2. Chạy `detailScraper.py` để thu chi tiết  
3. Kiểm tra dữ liệu trong PostgreSQL  
4. Xuất CSV cho phân tích / dashboard  

---

## 🗃️ File log

- Log crawl lưu trong **scraper.log** để dễ debug
- Có log trạng thái, lỗi kết nối, lỗi selector

---

## ✨ Author

- **Trần Gia Kiệt (gkinhere)**
- 📧 Liên hệ: giakiettran14102005@gmail.com