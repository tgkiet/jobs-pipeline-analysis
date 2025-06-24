-- Schema hoàn chỉnh đã có cột source_site
CREATE TABLE IF NOT EXISTS topcv_jobs_detailed (
    job_id SERIAL PRIMARY KEY,
    source_site VARCHAR(50), -- <<== CỘT MỚI ĐÃ ĐƯỢC THÊM VÀO ĐÂY
    job_title TEXT,
    job_url TEXT UNIQUE NOT NULL,
    scrape_date DATE,
    status VARCHAR(20) DEFAULT 'pending_details',
    
    -- Các trường từ trang LIST
    company_name_raw_list TEXT,
    salary_raw_list TEXT,
    location_raw_list TEXT,
    post_date_raw_list TEXT,

    -- Các trường từ trang DETAIL
    company_name_detail TEXT, 
    company_scale TEXT,
    company_field TEXT,
    company_full_address TEXT,
    job_level TEXT,
    education_level TEXT,
    quantity_needed TEXT,
    employment_type TEXT,
    gender_requirement TEXT,
    related_job_categories TEXT[],
    required_skills_tags TEXT[],
    preferred_skills_tags TEXT[],
    job_description_text TEXT,
    job_requirements_text TEXT,
    job_benefits_text TEXT,
    working_time_text TEXT,
    application_deadline_date TEXT,
    
    -- Thời gian ghi log
    inserted_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE
);

-- Tạo lại các trigger và index (giữ nguyên như cũ)
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

CREATE INDEX IF NOT EXISTS idx_topcv_jobs_status ON topcv_jobs_detailed (status);
CREATE INDEX IF NOT EXISTS idx_topcv_jobs_source ON topcv_jobs_detailed (source_site); -- Thêm index cho source_site