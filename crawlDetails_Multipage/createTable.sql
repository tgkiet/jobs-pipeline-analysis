CREATE TABLE IF NOT EXISTS topcv_job_url_queue (
    id SERIAL PRIMARY KEY,
    job_url TEXT UNIQUE NOT NULL, -- Dùng UNIQUE để không bị trùng URL
    status VARCHAR(20) DEFAULT 'pending', -- Trạng thái: pending, completed, error
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITHOUT TIME ZONE
);
-- Tạo một index trên cột status để truy vấn nhanh hơn sau này
CREATE INDEX IF NOT EXISTS idx_status ON topcv_job_url_queue (status);

-- id: Mã định danh duy nhất cho mỗi dòng, tự động tăng.
-- job_url: Địa chỉ của "ngôi nhà" mà chúng ta cần đến.
-- status: Trạng thái của "ngôi nhà". Hiện tại tất cả đều là pending (chưa xử lý).
-- created_at: Thời điểm "ngôi nhà" này được phát hiện và ghi vào sổ (tức là thời điểm Script 1 chạy và thêm URL này vào).
-- processed_at: Thời điểm "ngôi nhà" này được xử lý xong (tức là thời điểm Script 2 vào bên trong, lấy hết thông tin chi tiết và lưu vào bảng dữ liệu chính).