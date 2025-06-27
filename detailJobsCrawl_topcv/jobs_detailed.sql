-- Tạo bảng chính
CREATE TABLE IF NOT EXISTS topcv_jobs_detailed (
    job_id SERIAL PRIMARY KEY,
    source_site VARCHAR(50),
    job_title TEXT,
    job_url TEXT UNIQUE NOT NULL,
    scrape_date DATE,
    status VARCHAR(20) DEFAULT 'pending_details',
    
    -- Dữ liệu từ trang list
    company_name_raw_list TEXT,
    salary_raw_list TEXT,
    location_raw_list TEXT,
    post_date_raw_list TEXT,

    -- Dữ liệu từ trang detail
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

    -- Timestamps
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Trigger cập nhật updated_at mỗi lần update
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

-- Index phụ trợ
CREATE INDEX IF NOT EXISTS idx_topcv_jobs_status ON topcv_jobs_detailed (status);
CREATE INDEX IF NOT EXISTS idx_topcv_jobs_source ON topcv_jobs_detailed (source_site);
