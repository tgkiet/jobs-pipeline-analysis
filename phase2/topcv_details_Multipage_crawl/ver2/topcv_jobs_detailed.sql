-- Chạy câu lệnh này trực tiếp trong pgAdmin Query Tool

-- Đầu tiên, nếu bảng cũ đã tồn tại, có thể xóa đi để làm lại từ đầu cho sạch
-- DROP TABLE IF EXISTS topcv_jobs_detailed;

-- Tạo bảng mới với schema hoàn chỉnh, có thêm cột STATUS
CREATE TABLE IF NOT EXISTS topcv_jobs_detailed (
    job_id SERIAL PRIMARY KEY,
    job_title TEXT,
    job_url TEXT UNIQUE NOT NULL, -- URL là duy nhất và không được NULL
    scrape_date DATE,
    status VARCHAR(20) DEFAULT 'pending_details', -- TRẠNG THÁI: pending_details, completed, error
    
    -- Các trường lấy từ trang LIST (sẽ được điền bởi script 1)
    company_name_raw_list TEXT,
    salary_raw_list TEXT,
    location_raw_list TEXT,
    post_date_raw_list TEXT,

    -- Các trường lấy từ trang DETAIL (sẽ được điền bởi script 2)
    company_name_detail TEXT, 
    company_scale TEXT,
    company_field TEXT,
    company_full_address TEXT,
    job_level TEXT,
    education_level TEXT,
    quantity_needed TEXT, -- Giữ dạng thô
    employment_type TEXT,
    gender_requirement TEXT,
    related_job_categories TEXT[], -- Lưu dạng mảng (array) của Postgres
    required_skills_tags TEXT[],
    preferred_skills_tags TEXT[],
    job_description_text TEXT,
    job_requirements_text TEXT,
    job_benefits_text TEXT,
    working_time_text TEXT,
    application_deadline_date TEXT, -- Giữ dạng thô
    
    -- Thời gian ghi log
    inserted_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE
);

-- Tạo một trigger để tự động cập nhật `updated_at` mỗi khi dòng được UPDATE
-- Điều này rất hữu ích để biết lần cuối một job được xử lý là khi nào.
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON topcv_jobs_detailed
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

-- Tạo index để tăng tốc độ truy vấn các job đang chờ xử lý
CREATE INDEX IF NOT EXISTS idx_topcv_jobs_status ON topcv_jobs_detailed (status);