# Lộ trình làm website chatbot tư vấn điện thoại

Bộ hướng dẫn này chia kiến trúc trong [`data/kientruc.md`](../../data/kientruc.md) thành các buổi làm việc nhỏ. Mỗi buổi nên kết thúc bằng kết quả có thể kiểm tra; chưa đạt tiêu chí buổi hiện tại thì tiếp tục xử lý trước khi chuyển sang buổi sau.

## Cách học theo bộ tài liệu

1. Mỗi buổi dự kiến khoảng 1,5–3 giờ; phần PostgreSQL có thể cần thêm thời gian cài đặt theo máy.
2. Đầu buổi đọc mục kiến trúc được dẫn trong file buổi đó và xem tiêu chí hoàn thành.
3. Làm theo thứ tự từng bước. Ghi lại lệnh, lỗi gặp phải và cách xử lý trong README dự án hoặc nhật ký riêng.
4. Cuối buổi chạy phần tự kiểm tra, đánh dấu checklist và lưu mốc Git nếu dự án đang dùng Git.
5. Chưa tích hợp Ollama trước khi catalog, parser và hợp đồng tool hoạt động độc lập.
6. Cập nhật [`TIEN_DO.md`](TIEN_DO.md) sau mỗi buổi; chỉ đánh dấu hoàn tất khi đạt tiêu chí tương ứng.

## Các buổi

| Buổi | Nội dung | Kết quả cần có | Đọc trong kiến trúc |
|---:|---|---|---|
| 1 | Môi trường và khung dự án | Flask chạy được; có cấu trúc app và cấu hình cơ bản | Mục 3, 9, 10 |
| 2 | Kiểm tra CSV ban đầu | Data dictionary và danh sách vấn đề dữ liệu | Mục 5.1, `docs/mo_ta_du_lieu.md` |
| 3 | PostgreSQL, models và migrations | Database local có schema products/tags/product_tags | Mục 3, 5.1, 9 |
| 4 | Import CSV và repository PostgreSQL | CSV được seed có kiểm soát; catalog truy vấn DB, không đọc CSV runtime | Mục 5.1 |
| 5 | Tìm kiếm và duyệt danh mục | Truy vấn DB đúng, phân trang và thứ tự ổn định | Mục 5.2, 6.4 |
| 6 | Gợi ý, chi tiết và so sánh | Ranking ổn định, không vi phạm điều kiện cứng | Mục 5.3, 6.1–6.3 |
| 7 | Chuẩn hóa tiếng Việt, giá và alias | Nhiều cách viết cùng tạo ra giá trị chuẩn | Mục 4.2 A, C, D, D½ |
| 8 | Intent, slot và làm rõ | Câu hỏi thành request đã xác thực | Mục 4.1, 4.2 B, C, E |
| 9 | State hội thoại theo phiên | Câu tiếp nối giữ đúng điều kiện, không lẫn phiên | Mục 4.2 E½ |
| 10 | Tool schema và whitelist | Tool chỉ nhận request hợp lệ, chỉ đọc catalog DB | Mục 6.1–6.5 |
| 11 | Tích hợp Agent/Ollama | Agent gọi đúng tool, có timeout/fallback | Mục 6.6, 9 |
| 12 | API Flask cho chat | API trả kết quả, hỏi làm rõ và lỗi theo hợp đồng | Mục 2, 8 |
| 13 | Giao diện chat | Người dùng hỏi, xem sản phẩm và tiếp tục hội thoại | Mục 8 |
| 14 | Đánh giá và demo | Có kết quả đánh giá và kịch bản chạy lại được | Mục 10, 11, 12 |

## Các mốc kiểm tra

- **Sau buổi 3:** schema PostgreSQL được tạo bằng migration; chưa cần có sản phẩm.
- **Sau buổi 4:** sản phẩm/tag đã seed; website lấy catalog từ PostgreSQL kể cả khi không có CSV.
- **Sau buổi 6:** thao tác catalog chạy độc lập và ổn định.
- **Sau buổi 9:** câu hỏi tự nhiên và câu tiếp nối tạo state đúng.
- **Sau buổi 12:** API chạy được cả khi Ollama tắt.
- **Sau buổi 14:** demo có thể chạy lại từ hướng dẫn; kết quả được đánh giá trên tập câu riêng.

## Nguyên tắc dữ liệu xuyên suốt

- PostgreSQL là nguồn dữ liệu chuẩn khi web chạy; CSV chỉ dùng cho import/seed có chủ đích.
- Không tự seed hoặc ghi đè database khi Flask khởi động.
- Agent chỉ có quyền đọc catalog; thao tác ghi nếu bổ sung sau này phải nằm ở luồng quản trị riêng.
- Không lấy giá hoặc thông số từ trí nhớ LLM; giá trong DB vẫn là snapshot, không phải giá thị trường trực tiếp.
- Điều kiện bắt buộc dùng để lọc; sở thích chỉ dùng để xếp hạng.
- Giá và tag phải so sánh theo toán tử/giá trị chuẩn, không tìm bằng chuỗi con.
- Nếu chưa rõ model, ngân sách hoặc quan hệ điều kiện, hỏi người dùng.
