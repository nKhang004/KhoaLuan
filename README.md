
1. Tính năng chính
- Xác thực & phân quyền: JWT, phân quyền 3 cấp (Admin, Giáo viên, Học sinh), đổi mật khẩu lần đầu bắt buộc.
- Quản lý nội dung: Môn học, chủ đề, ngân hàng câu hỏi (3 loại: một đáp án, nhiều đáp án, đúng/sai).
- Quản lý đề thi: Tạo thủ công, sinh tự động ngẫu nhiên, công bố/gỡ đề.
- Làm bài thi: Xáo trộn câu hỏi/đáp án, bắt buộc trả lời đủ câu, thời gian tối thiểu 50%, giám sát thoát tab (dừng đồng hồ), tự động nộp bài khi vi phạm 3 lần.
- Thống kê & báo cáo: Xem kết quả, tỷ lệ đúng/sai từng câu, xuất báo cáo Excel.
- Quản lý người dùng: Admin có thể khóa/mở, xóa, thay đổi vai trò, import tài khoản sinh viên từ Excel.
- Import/Export: Nhập câu hỏi từ Excel theo mẫu, xuất đề thi và kết quả ra Excel.

2. Các bước cài đặt
- Tạo môi trường ảo và cài đặt dependencies
   python -m venv venv
venv\Scripts\activate     
pip install -r requirements.txt
- Chạy ứng dụng
uvicorn main:app --reload

3. Tài khoản mặc định
admin   123456
giaovien1   123456
sinhvien1   123456