-- Tạo bảng chính
CREATE TABLE IF NOT EXISTS topcv_jobs_detailed (
    job_id BIGSERIAL PRIMARY KEY, -- CHỈNH SỬA: Dùng BIGSERIAL để chuẩn bị cho dữ liệu lớn.
    source_site VARCHAR(50) NOT NULL, -- THÊM: NOT NULL để đảm bảo luôn có nguồn.
    job_title TEXT,
    job_url TEXT UNIQUE NOT NULL,
    scrape_date DATE NOT NULL DEFAULT CURRENT_DATE, -- CHỈNH SỬA: Có giá trị mặc định là ngày hiện tại.
    status VARCHAR(20) NOT NULL DEFAULT 'pending_details', -- THÊM: NOT NULL để quản lý trạng thái chặt chẽ.
    
    -- Dữ liệu từ trang list (giữ nguyên)
    company_name_raw_list TEXT,
    salary_raw_list TEXT,
    location_raw_list TEXT,
    post_date_raw_list TEXT,

    -- Dữ liệu từ trang detail (có nhiều chỉnh sửa quan trọng)
    company_name_detail TEXT,
    company_scale VARCHAR(100), -- CHỈNH SỬA: VARCHAR(100) là đủ cho quy mô (vd: "100-499 nhân viên").
    company_field TEXT, -- Giữ nguyên TEXT vì lĩnh vực có thể dài.
    company_full_address TEXT,
    job_level VARCHAR(100), -- CHỈNH SỬA: VARCHAR(100) cho cấp bậc (vd: "Nhân viên", "Trưởng nhóm").
    education_level VARCHAR(100), -- CHỈNH SỬA: VARCHAR(100) cho học vấn.
    quantity_needed SMALLINT, -- CHỈNH SỬA: Dùng kiểu số cho số lượng.
    employment_type VARCHAR(100), -- CHỈNH SỬA: VARCHAR(100) cho hình thức làm việc.
    gender_requirement VARCHAR(50), -- CHỈNH SỬA: VARCHAR(50) cho giới tính.
    related_job_categories TEXT[],
    required_skills_tags TEXT[],
    preferred_skills_tags TEXT[],
    job_description_text TEXT,
    job_requirements_text TEXT,
    job_benefits_text TEXT,
    working_time_text TEXT,
    application_deadline_date DATE, -- CHỈNH SỬA: Dùng kiểu DATE thay vì TEXT.

    -- Timestamps
    inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), -- CHỈNH SỬA: Dùng TIMESTAMPTZ và NOT NULL.
    updated_at TIMESTAMPTZ -- CHỈNH SỬA: Dùng TIMESTAMPTZ.
);

-- Trigger cập nhật updated_at mỗi lần update
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER set_timestamp -- CHỈNH SỬA: Thêm OR REPLACE cho an toàn.
BEFORE UPDATE ON topcv_jobs_detailed
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

-- Index phụ trợ (thêm một vài index quan trọng)
CREATE INDEX IF NOT EXISTS idx_topcv_jobs_status ON topcv_jobs_detailed (status);
CREATE INDEX IF NOT EXISTS idx_topcv_jobs_source ON topcv_jobs_detailed (source_site);
CREATE INDEX IF NOT EXISTS idx_topcv_jobs_scrape_date ON topcv_jobs_detailed (scrape_date); -- THÊM: Index cho ngày cào.
CREATE INDEX IF NOT EXISTS idx_topcv_jobs_job_level ON topcv_jobs_detailed (job_level); -- THÊM: Index cho các cột hay được filter.
CREATE INDEX IF NOT EXISTS idx_topcv_jobs_location ON topcv_jobs_detailed (location_raw_list); -- THÊM: Index cho địa điểm.