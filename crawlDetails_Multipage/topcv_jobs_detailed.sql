-- Chạy câu lệnh này trong query tool của pgAdmin
CREATE TABLE IF NOT EXISTS topcv_jobs_detailed (
    job_id SERIAL PRIMARY KEY,
    job_url TEXT UNIQUE NOT NULL, -- job_url là duy nhất, đảm bảo mỗi job chỉ có 1 dòng chi tiết
    
    scrape_date DATE,
    job_title TEXT,
    
    -- Thông tin công ty
    company_name TEXT,
    company_scale TEXT,
    company_field TEXT,
    company_address TEXT,
    
    -- Thông tin chung về job
    salary_raw TEXT,
    experience_raw TEXT,
    job_level TEXT,
    employment_type TEXT,
    quantity_needed TEXT,
    gender_requirement TEXT,
    application_deadline DATE,
    
    -- Nội dung chính của job (dạng text)
    job_description TEXT,
    job_requirements TEXT,
    job_benefits TEXT,
    
    -- Các kỹ năng (dạng text, ngăn cách bởi dấu phẩy)
    skill_tags TEXT,
    
    -- Cột quản lý
    inserted_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);