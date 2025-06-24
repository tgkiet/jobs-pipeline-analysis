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