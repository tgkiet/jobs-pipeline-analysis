CREATE TABLE IF NOT EXISTS topcv_job_url_queue (
    id SERIAL PRIMARY KEY,
    job_url TEXT UNIQUE NOT NULL, -- Dùng UNIQUE để không bị trùng URL
    status VARCHAR(20) DEFAULT 'pending', -- Trạng thái: pending, completed, error
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITHOUT TIME ZONE
);
-- Tạo một index trên cột status để truy vấn nhanh hơn sau này
CREATE INDEX IF NOT EXISTS idx_status ON topcv_job_url_queue (status);