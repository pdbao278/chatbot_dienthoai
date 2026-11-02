# KIẾN TRÚC VÀ HƯỚNG DẪN THỰC HIỆN CHATBOT TƯ VẤN ĐIỆN THOẠI

> **Phạm vi:** website mô phỏng tư vấn điện thoại bằng Flask, PostgreSQL, NLP tiếng Việt và AI Agent chạy qua Ollama. CSV chỉ là dữ liệu đầu vào để nạp ban đầu.
>
> **Không nằm trong phiên bản này:** chính sách bảo hành, kiểm tra tồn kho, cập nhật giá trực tuyến, đặt hàng/thanh toán và tư vấn dựa trên tài liệu dài.

---

## 1. Tóm tắt quyết định kiến trúc

Đề xuất làm một **ứng dụng Flask dạng modular monolith**: một ứng dụng chạy trên máy, bên trong chia thành các module có trách nhiệm riêng.

- Dùng **PostgreSQL làm nguồn dữ liệu chuẩn khi ứng dụng chạy**. Nạp `dien_thoai_chuan_hoa.csv` vào database bằng một lệnh riêng ở bước khởi tạo; sau đó website đọc database, không đọc CSV mỗi lần khởi động hay mỗi yêu cầu. Chức năng tư vấn chỉ đọc catalog; trang quản trị ghi dữ liệu là phần mở rộng. `dien_thoai_chuan_hoa.json` chỉ là bản tham chiếu/xuất, không tham gia runtime.
- Dùng SQLAlchemy 2.x để ánh xạ model và truy vấn, Alembic để quản lý thay đổi schema bằng migration. Mỗi request dùng một database session riêng rồi đóng session sau khi xử lý.
- Dùng **NLP** để chuẩn hóa tiếng Việt, nhận diện ý định, trích xuất điều kiện bắt buộc và sở thích.
- Dùng **AI Agent qua Ollama** để gọi tool được backend cho phép và diễn đạt kết quả. Backend xác định tool theo intent; Agent không được tự sửa hoặc nới điều kiện đã xác nhận.
- Chỉ cho Agent gọi các công cụ đọc dữ liệu có schema và giới hạn rõ ràng; kiểm tra mọi lời gọi ở backend trước khi truy vấn.
- Chưa dùng RAG, embedding hoặc vector database: dữ liệu hiện tại là bảng thuộc tính, không phải kho tài liệu văn bản dài.
- Giao diện nhận câu hỏi và hiển thị tối đa ba gợi ý kèm thông số, lý do gợi ý, ảnh và liên kết sản phẩm nếu các trường đó có dữ liệu.

### Vì sao chọn cách này?

Danh mục hiện có 162 dòng và 17 cột như hãng, giá, RAM, ROM, pin, màn hình, camera và tags nhu cầu. Các câu hỏi thường cần lọc chính xác, ví dụ “Xiaomi dưới 15 triệu”, nên truy vấn cấu trúc dễ kiểm soát và dễ giải thích hơn tìm kiếm vector. LLM phù hợp để hiểu cách diễn đạt và trình bày câu trả lời; các phép lọc và dữ liệu thực tế do chương trình xử lý. Nếu ngày thu thập giá không được lưu trong dữ liệu, bot không được tự nêu ngày hoặc gọi giá là giá hiện tại.

---

## 2. Sơ đồ thành phần và luồng dữ liệu

~~~mermaid
flowchart TD
    User[Người dùng] <--> UI[Giao diện chat]
    UI <--> Flask[Flask Web/API]
    Flask --> State[Ngữ cảnh hội thoại]
    Flask --> NLP[NLP tiếng Việt]
    NLP --> Parsed[Yêu cầu đã chuẩn hóa]
    Parsed --> Validate[Backend xác thực điều kiện]
    Validate -->|hợp lệ| Agent[Agent điều phối Ollama]
    Validate -->|mơ hồ hoặc mâu thuẫn| Clarify[Hỏi lại người dùng]
    Clarify --> UI
    Flask --> Static[Trả lời mẫu greeting/out-of-scope]
    Static --> UI
    Agent --> Guard[Danh sách công cụ + kiểm tra tham số]
    Guard --> Tools[Công cụ tư vấn sản phẩm]
    Tools --> Catalog[Dịch vụ danh mục]
    Catalog --> DB[(PostgreSQL)]
    Catalog --> Results[Kết quả có cấu trúc]
    Results --> Agent
    Agent --> Answer[Câu trả lời tiếng Việt]
    Answer --> UI
    CSV[(dien_thoai_chuan_hoa.csv)] --> Seed[Lệnh nạp dữ liệu ban đầu]
    Seed --> DB
~~~

### Trách nhiệm từng phần

| Thành phần | Làm gì | Vì sao tách riêng |
|---|---|---|
| Giao diện chat | Gửi câu hỏi, hiển thị tin nhắn và thẻ điện thoại | Không để giao diện tự lọc hay tự suy diễn thông số |
| Flask | Nhận yêu cầu, gọi các module và trả kết quả | Là đầu mối giao tiếp giữa giao diện với xử lý phía máy chủ |
| NLP | Chuẩn hóa cách viết, nhận diện ý định và trích xuất điều kiện | Có thể kiểm tra riêng và trình bày rõ phần xử lý ngôn ngữ trong đồ án |
| Backend/policy | Xác thực trường, phát hiện mâu thuẫn và quyết định khi nào phải hỏi lại | Giữ điều kiện nhất quán trước khi gọi model hoặc catalog |
| Agent | Gọi tool đã được backend cho phép và diễn đạt kết quả | LLM xử lý hội thoại nhưng không làm nguồn dữ liệu hoặc thay đổi điều kiện đã xác thực |
| Công cụ | Xác thực tham số và gọi chức năng nghiệp vụ | Chặn gọi hàm ngoài phạm vi, giữ hợp đồng đầu vào rõ ràng |
| Dịch vụ danh mục | Truy vấn PostgreSQL, lọc, so sánh và xếp hạng điện thoại | Giữ logic dữ liệu tập trung, kết quả ổn định và có thể kiểm tra độc lập |
| PostgreSQL | Lưu sản phẩm/tag và là nguồn dữ liệu runtime duy nhất | Mô phỏng cách website thật lưu dữ liệu bền vững và phục vụ nhiều request qua backend |
| Lệnh seed CSV | Kiểm tra rồi nhập CSV vào PostgreSQL khi khởi tạo/cập nhật dữ liệu | Tách nhập dữ liệu khỏi phục vụ web; không làm chậm hoặc ghi đè dữ liệu khi app khởi động |

---

## 3. Cấu trúc thư mục đề xuất

Đây là cấu trúc mục tiêu cho đồ án; có thể tạo dần theo các bước ở mục 10, không cần tạo tất cả thư mục trống từ đầu.

~~~text
E:\NLP/
├── data/
│   ├── dien_thoai_chuan_hoa.csv   # dữ liệu seed ban đầu
│   ├── dien_thoai_chuan_hoa.json  # bản tham chiếu/xuất; không dùng runtime
│   └── kientruc.md                # vị trí hiện tại của tài liệu này
├── docs/
│   ├── mo_ta_du_lieu.md
│   └── huong_dan_tung_buoi/
│       ├── README.md
│       ├── TIEN_DO.md
│       └── buoi_*.md
├── src/
│   └── phone_advisor/
│       ├── __init__.py
│       ├── app.py
│       ├── config.py
│       ├── db/
│       │   ├── base.py
│       │   ├── models.py
│       │   └── session.py
│       ├── web/
│       │   ├── routes.py
│       │   ├── templates/
│       │   └── static/
│       ├── nlp/
│       │   ├── normalize.py
│       │   ├── aliases.py
│       │   ├── intent.py
│       │   ├── slots.py
│       │   └── dialogue_state.py
│       ├── agent/
│       │   ├── orchestrator.py
│       │   ├── prompts/
│       │   ├── tool_schemas.py
│       │   └── tool_registry.py
│       └── catalog/
│           ├── repository.py
│           ├── search.py
│           ├── recommend.py
│           ├── browse.py
│           └── compare.py
├── tests/
│   ├── test_nlp.py
│   ├── test_catalog.py
│   ├── test_agent_flow.py
│   └── fixtures/
├── evaluation/
│   └── intent_slots.csv
├── migrations/                    # migration do Alembic quản lý
├── scripts/
│   ├── __init__.py
│   └── seed_catalog.py            # lệnh nhập CSV tường minh, không chạy lúc app start
├── .env.example                   # tên biến mẫu, không chứa mật khẩu thật
├── .gitignore
├── requirements.txt
└── README.md
~~~

### Vai trò các module chính

- **web/**: route Flask, trang chat và thành phần hiển thị thẻ sản phẩm.
- **nlp/**: chuẩn hóa câu chữ, từ điển đồng nghĩa, nhận diện ý định, trích xuất điều kiện và giữ một số thông tin hội thoại cần thiết.
- **agent/**: lời nhắc hệ thống, điều phối Ollama, schema tham số và danh sách hàm Agent được phép gọi.
- **db/**: khai báo model PostgreSQL, tạo engine/session factory; không chia sẻ một Session giữa nhiều request.
- **catalog/**: gọi repository để lọc dữ liệu trong PostgreSQL, xếp hạng kết quả, lấy chi tiết và so sánh.
- **scripts/seed_catalog.py**: nhập CSV có kiểm tra vào PostgreSQL theo lệnh tường minh; mặc định từ chối nhập lại nếu đã có dữ liệu, không tự xóa hàng vắng khỏi CSV.
- **config.py**: đọc `DATABASE_URL`, tên model và cấu hình chạy; không gắn cứng đường dẫn máy tính hoặc mật khẩu trong mã nguồn.
- **data/**: CSV dùng để seed ban đầu/nhập một phiên bản dữ liệu mới theo quy trình; sau khi seed, PostgreSQL mới là nguồn chuẩn cho website. JSON không dùng runtime. Tài liệu này hiện ở `data/kientruc.md` theo vị trí của workspace.
- **docs/**: data dictionary và hướng dẫn thực hiện theo từng buổi trong [`docs/huong_dan_tung_buoi/README.md`](../docs/huong_dan_tung_buoi/README.md).

Không cần tách thành nhiều dịch vụ/microservice. Một ứng dụng Flask kết nối một PostgreSQL local là đủ để mô phỏng website thật mà vẫn giữ cấu hình vừa sức cho đồ án.

---

## 4. Thiết kế phần NLP tiếng Việt

### 4.1. NLP cần tạo ra gì?

Đầu vào là câu nói tự nhiên. Đầu ra là một yêu cầu có cấu trúc đã chuẩn hóa và được backend kiểm tra. Agent chỉ được dùng yêu cầu này để gọi công cụ; không được tự đổi điều kiện bắt buộc.

Ví dụ đầu vào:

> “Tìm giúp mình Xiaomi chơi game, pin trâu, dưới 15 củ.”

Kết quả NLP mong muốn:

~~~json
{
  "intent": "recommend",
  "filters": {
    "brand": "Xiaomi",
    "min_price_vnd": null,
    "max_price_vnd": 15000000,
    "min_price_inclusive": true,
    "max_price_inclusive": false,
    "min_ram_gb": null,
    "min_rom_gb": null,
    "min_battery_mah": null,
    "min_refresh_rate_hz": null,
    "required_tags": [],
    "required_tag_groups": []
  },
  "preferences": [
    {"any_of": ["choi_game"], "priority": 1},
    {"any_of": ["pin_trau", "pin_khung"], "priority": 1}
  ],
  "excluded_brands": [],
  "excluded_tags": [],
  "excluded_product_ids": [],
  "limit": 3
}
~~~

Câu hỏi khác nhau nhưng cùng ý nghĩa nên tạo ra yêu cầu gần tương đương. Ví dụ “15 củ”, “15tr” và “15 triệu” đều được chuẩn hóa về 15.000.000 đồng. `filters` là điều kiện bắt buộc; `preferences` chỉ dùng để xếp hạng. Chỉ đưa tag vào `required_tags` hoặc `required_tag_groups` khi người dùng nói rõ đó là điều kiện phải có, ví dụ “bắt buộc hỗ trợ 5G”.

### 4.2. Các bước xử lý ngôn ngữ

#### Bước A — Chuẩn hóa văn bản

- Lưu nguyên câu người dùng để giữ ngữ cảnh và có thể hiển thị lại.
- Tạo một bản dùng để so khớp: chuẩn hóa Unicode, chữ hoa/thường, khoảng trắng và dấu câu.
- Chuẩn hóa cách viết số tiền: “15tr”, “15 triệu”, “15 củ”.
- Giữ dấu tiếng Việt trong câu gốc. Nếu cần tìm không dấu, tạo thêm bản phụ để so khớp; không dùng bản bỏ dấu làm câu trả lời.
- Không tự cắt tên hãng hoặc tên model bằng quy tắc tách từ chung.

**Vì sao:** tên sản phẩm và từ tiếng Việt có dấu dễ bị biến dạng nếu chuẩn hóa quá mạnh. Tách câu gốc và bản so khớp giúp tìm linh hoạt mà vẫn giữ nội dung người dùng nói.

#### Bước B — Nhận diện ý định

Phiên bản đầu có thể nhận diện các ý định sau:

| Ý định | Hành vi | Ví dụ |
|---|---|---|
| recommend | Lọc điều kiện bắt buộc, xếp hạng sở thích và đưa tối đa ba gợi ý | “Gợi ý điện thoại chụp ảnh đẹp dưới 20 triệu” |
| search | Trả tối đa ba kết quả khớp điều kiện người dùng nêu; không tự suy ra sở thích | “Có máy Samsung RAM ít nhất 8GB không?” |
| detail | Tìm một model/phiên bản; hỏi lại nếu tên khớp nhiều sản phẩm | “Cho mình thông tin Xiaomi POCO X8 Pro” |
| compare | So sánh các sản phẩm đã xác định rõ | “So sánh iPhone 17 với Samsung Galaxy S25” |
| browse | Xem danh mục tổng quát hoặc duyệt danh sách theo hãng/giá có phân trang | “Có những hãng nào?”, “Liệt kê tất cả Samsung” |
| greeting | Trả lời bằng mẫu cố định, không cần gọi tool | “Xin chào”, “Chào bạn” |
| out_of_scope | Nêu giới hạn bằng mẫu cố định; không suy diễn thông tin sản phẩm | Câu hỏi ngoài phạm vi tư vấn sản phẩm |

“Máy nào dưới 5 triệu?” là `search` vì có điều kiện lọc; `browse` dành cho yêu cầu liệt kê hoặc khám phá danh mục. `search` không xếp hạng theo sở thích ngầm định; `recommend` mới áp dụng thứ tự ưu tiên. Khi cần liệt kê nhiều hơn ba máy, dùng `browse` để phân trang.

Bắt đầu bằng luật và từ khóa rõ ràng vì dễ giải thích, không cần dữ liệu huấn luyện ban đầu. Nếu muốn thử mô hình phân loại trong môn học, có thể tạo tập câu hỏi riêng, gán nhãn ý định rồi so sánh với baseline luật. **CSV sản phẩm không phải tập dữ liệu câu hỏi đã gán nhãn**, nên không thể dùng trực tiếp CSV để huấn luyện intent classifier.

**Xử lý câu hỏi ngoài phạm vi:**

| Câu hỏi ví dụ | Cách phản hồi |
|---|---|
| “Máy này có bảo hành không?” | Trả lời nhẹ nhàng rằng bot chưa có thông tin bảo hành, gợi ý liên hệ cửa hàng |
| “Mua ở đâu?” | Nếu sản phẩm có trường `url` → đưa liên kết; nếu không → nói chưa có thông tin |
| “Tại sao máy này đắt?” | Liệt kê thông số nổi bật có trong database nhưng không đánh giá giá cả hợp lý hay không |
| “So sánh với laptop” | Nói rõ bot chỉ tư vấn điện thoại từ danh mục hiện có |

#### Bước C — Trích xuất thực thể và điều kiện

Các trường nên nhận diện:

- **Hãng**: Apple, Samsung, Xiaomi, OPPO, vivo, realme, HONOR, Tecno, Motorola, Nothing Phone, Nubia.
- **Model**: đối chiếu tên máy trong database, hỗ trợ tên gọi rút gọn nếu xác định được duy nhất.
- **Ngân sách**: giá tối đa, giá tối thiểu hoặc khoảng giá.
- **Thông số tối thiểu**: RAM, ROM, pin, tần số quét nếu người dùng nêu rõ.
- **Nhu cầu**: chơi game, pin trâu, chụp ảnh đẹp, selfie, sạc nhanh, màn hình mượt, 5G...
- **Điều kiện loại trừ**: hãng (“không lấy Samsung”), tag (“không lấy máy gập”) hoặc model/ID cụ thể.
- **Mức ưu tiên**: “ưu tiên pin”, “quan trọng nhất là camera”.

Ví dụ:

~~~text
“Máy khoảng 10 đến 15 triệu, không phải iPhone, ưu tiên pin”
→ intent: recommend
→ filters.min_price_vnd: 10000000
→ filters.max_price_vnd: 15000000
→ excluded_brands: [Apple]
→ preferences: [{any_of: [pin_trau], priority: 2}]
~~~

Chỉ dùng điều kiện cứng khi câu chữ thể hiện yêu cầu bắt buộc hoặc điều kiện lọc rõ ràng. “Tìm máy có 5G” là điều kiện bắt buộc; “ưu tiên 5G” là sở thích để xếp hạng. Nếu cách nói không đủ rõ để phân biệt, hỏi lại thay vì tự chọn cách hiểu làm thay đổi tập kết quả.

Với giá tiền, cần nhận biết quan hệ:

- “dưới 15 triệu” → giá nhỏ hơn 15.000.000 (không bao gồm ngưỡng); “tối đa 15 triệu” → giá nhỏ hơn hoặc bằng ngưỡng.
- “trên 10 triệu” → giá lớn hơn 10.000.000 (không bao gồm ngưỡng); “ít nhất/từ 10 triệu” → giá lớn hơn hoặc bằng ngưỡng.
- “từ 10 đến 15 triệu” → khoảng giá bao gồm cả hai đầu, trừ khi người dùng nói khác.
- “khoảng 15 triệu” → chưa đủ để tạo khoảng giá chính xác; hỏi độ rộng mong muốn hoặc áp dụng mặc định cấu hình và nói rõ mặc định đó.

Các cụm như “giá rẻ”, “giá sinh viên”, “tầm trung”, “cao cấp” và “flagship” không có ngưỡng giá thống nhất cho mọi người. Không tự chuyển chúng thành điều kiện giá cứng. Mặc định nên hỏi ngân sách; nếu đồ án cần ánh xạ tự động, định nghĩa các khoảng trong cấu hình, coi chúng là mặc định mềm và thông báo cho người dùng. “Sinh viên” mô tả nhóm người dùng, không tự nó xác định ngân sách.


#### Bước D — Chuẩn hóa từ đồng nghĩa sang tag trong database

Tag phải lấy từ dữ liệu thật, không tự tạo tag mới khi truy vấn. Một số tag đang có trong database sau khi seed:

~~~text
choi_game, chip_gaming, pin_trau, pin_khung, chup_anh_dep,
selfie_dep, sac_nhanh, man_hinh_muot, 5g, nfc, flagship,
doanh_nhan, hoc_sinh_sinh_vien, hong_ngoai, thiet_ke_gap
~~~

Ví dụ từ điển đồng nghĩa ban đầu:

| Cách nói | Tag/điều kiện chuẩn |
|---|---|
| chơi game, game nặng | choi_game |
| chip gaming, chơi game mượt | chip_gaming hoặc choi_game |
| pin trâu, pin khỏe, dùng lâu | pin_trau |
| pin khủng | pin_khung |
| chụp hình đẹp, camera đẹp | chup_anh_dep |
| selfie đẹp, chụp ảnh tự sướng | selfie_dep |
| sạc nhanh | sac_nhanh |
| màn hình mượt, cuộn mượt | man_hinh_muot |
| máy gập, điện thoại gập | thiet_ke_gap |
| cao cấp, hàng đầu, dòng flagship | flagship |
| doanh nhân, công việc, sang trọng | doanh_nhan |
| học sinh, sinh viên, cho sinh viên | hoc_sinh_sinh_vien |
| hồng ngoại, điều khiển tivi, remote tivi | hong_ngoai |
| thanh toán chạm, NFC, chạm thanh toán | nfc |
| mạng 5G, hỗ trợ 5G, có 5G | 5g |

Một câu có thể tạo ra nhiều tag. Không nên coi “pin trâu” và “pin khủng” là hai từ giống hệt nhau nếu dữ liệu phân biệt chúng; có thể ánh xạ cả hai, hoặc dùng một tag làm ưu tiên và một tiêu chí xếp hạng theo pin_mah.

Các tag nhận diện từ lời nói mặc định là sở thích mềm. Chỉ chuyển thành điều kiện bắt buộc khi người dùng dùng cách nói như “phải có”, “chỉ lấy máy có”. Dùng `required_tags` khi phải có tất cả tag; dùng `required_tag_groups` khi phải khớp ít nhất một tag trong nhóm tương đương. Ví dụ “phải pin khỏe” có thể yêu cầu `pin_trau` **hoặc** `pin_khung`.

**Phân biệt pin_trau và pin_khung:** trong dữ liệu hiện tại, cả hai tag cùng tồn tại. Các ngưỡng tham khảo là pin_trau cho máy có pin ≥ 5.000mAh và pin_khung cho máy có pin ≥ 6.000mAh; cần kiểm tra lại các ngưỡng này nếu CSV được cập nhật. Khi người dùng nói “pin khỏe” hoặc “pin tốt” mà không nói rõ hơn, khớp một trong hai tag rồi xếp hạng theo `pin_mah` giảm dần.

#### Bước D½ — Ánh xạ tên model rút gọn

Người dùng thường không gọi đầy đủ tên sản phẩm. Cần xây dựng bảng `model_aliases` trong `aliases.py` để ánh xạ tên rút gọn về ID sản phẩm trong database.

Ví dụ:

| Người dùng nói | Có thể ánh xạ về |
|---|---|
| “POCO X8 Pro” | id duy nhất → trả chi tiết luôn |
| “Note 15” | nhiều id (Redmi Note 15, Note 15 Pro, Note 15 Pro 5G) → hỏi lại |
| “S25” | nhiều id (Galaxy S25, Galaxy S25 FE) → hỏi lại |
| “17 Pro Max” | id cùng model nhưng khác ROM (256GB, 512GB, 1TB) → liệt kê phiên bản |
| “iPhone mới nhất” | không ánh xạ chắc chắn → hỏi lại dòng cụ thể |

Quy tắc:

1. Tách tên model gốc khỏi phần dung lượng ROM (ví dụ “iPhone 17 Pro Max 256GB” → model gốc là “iPhone 17 Pro Max”).
2. Nếu tên rút gọn khớp **duy nhất 1 model gốc** nhưng có nhiều phiên bản ROM → liệt kê các phiên bản ROM kèm giá để người dùng chọn.
3. Nếu tên rút gọn khớp **nhiều model gốc** khác nhau → đưa danh sách tên đầy đủ và hỏi người dùng muốn xem máy nào.
4. Nếu không khớp model nào → báo không tìm thấy và gợi ý tên gần nhất (nếu có).

#### Bước E — Xử lý phủ định và câu mơ hồ

- “Không muốn Apple” phải đưa Apple vào danh sách loại trừ.
- “Không cần chơi game” hoặc “không cần máy gập” không tự động biến thành nhu cầu hay điều kiện loại trừ; chỉ loại khi người dùng nói rõ “không lấy/tránh”.
- Nếu loại một model có nhiều phiên bản ROM, đưa tất cả ID của model đó vào danh sách loại trừ.
- Nếu người dùng vừa nói “dưới 10 triệu” vừa nói “tối thiểu 15 triệu”, điều kiện mâu thuẫn; hỏi lại thay vì trả kết quả sai.
- Nếu tên model khớp nhiều sản phẩm, hỏi thêm phiên bản dung lượng hoặc đưa các lựa chọn để người dùng chọn.
- Nếu không có ngân sách hay nhu cầu nào, hỏi một câu ngắn như “Bạn dự kiến chi khoảng bao nhiêu?” hoặc đề nghị người dùng chọn ưu tiên.

#### Bước E½ — Quản lý ngữ cảnh hội thoại (Dialogue State)

Để xử lý câu tiếp nối (ví dụ người dùng nói “ưu tiên pin trâu nhé” sau khi đã nêu hãng và giá ở lượt trước), cần giữ một ngữ cảnh hội thoại tối thiểu:

**Thông tin cần lưu qua các lượt:**

~~~json
{
  "filters": {
    "brand": "Samsung",
    "min_price_vnd": null,
    "max_price_vnd": 15000000,
    "min_price_inclusive": true,
    "max_price_inclusive": true,
    "min_ram_gb": null,
    "min_rom_gb": null,
    "min_battery_mah": null,
    "min_refresh_rate_hz": null,
    "required_tags": [],
    "required_tag_groups": []
  },
  "preferences": [{"any_of": ["pin_trau"], "priority": 2}],
  "excluded_brands": [],
  "excluded_tags": [],
  "excluded_product_ids": [],
  "last_results": [42, 58, 71],
  "turn_count": 2
}
~~~

**Quy tắc quản lý state:**

1. Lưu tối đa 5 lượt tin nhắn làm ngữ cảnh cho LLM; đây là lịch sử hội thoại, tách biệt với state có cấu trúc được giữ trong phiên.
2. State phải được cô lập theo phiên chat, không dùng một biến toàn cục chung cho mọi người dùng. Lưu state ở phía server theo session ID ngẫu nhiên; cookie chỉ giữ ID phiên. Cấu hình khóa session ngoài mã nguồn và thời hạn hết hạn.
3. Lượt mới bổ sung điều kiện thì gộp; lượt mới thay đổi trực tiếp một trường thì ghi đè trường đó.
4. Khi người dùng rút lại điều kiện (“không cần pin nữa”) thì xóa đúng điều kiện đó. Khi họ nói “bắt đầu lại” hoặc phiên hết hạn (mặc định 30 phút không hoạt động, cấu hình được) thì xóa toàn bộ state.
5. Lưu `last_results` dưới dạng danh sách ID để xử lý “máy thứ hai” hoặc “so sánh hai máy vừa rồi”; luôn kiểm tra ID thuộc kết quả của phiên hiện tại.
6. Không lưu bộ nhớ dài hạn giữa các phiên trong phiên bản đầu tiên.

#### Bước F — Dùng LLM ở chỗ cần thiết

Có thể để Qwen hỗ trợ hiểu câu diễn đạt khó hoặc câu nối tiếp, nhưng:

1. Đưa cho Agent câu gốc cùng kết quả NLP ban đầu.
2. Dùng các trường NLP đã xác thực làm dữ liệu chuẩn; Agent không được đổi điều kiện cứng, tự thêm hãng/tag, hoặc suy ra ngân sách từ cụm từ chủ quan.
3. Nếu Agent đề xuất cách hiểu mới, kiểm tra schema và đối chiếu với câu gốc; nếu cách hiểu làm thay đổi điều kiện hoặc còn mơ hồ thì hỏi người dùng trước khi truy vấn.
4. Backend xác thực mọi đối số trước khi gọi tool.
5. Bộ catalog vẫn là nơi duy nhất quyết định sản phẩm nào thỏa điều kiện và thứ tự xếp hạng.

**Lý do dùng cách kết hợp:** luật và từ điển cho kết quả minh bạch với miền dữ liệu nhỏ; LLM xử lý cách nói đa dạng; kiểm tra schema giúp hạn chế đầu ra tùy tiện. Không nên giao toàn bộ việc tính ngân sách và lọc sản phẩm cho LLM.

### 4.3. Có nên dùng Underthesea?

Có thể dùng Underthesea để thử tách từ hoặc hỗ trợ phân tích tiếng Việt, nhưng nó không thay thế từ điển hãng/tag, nhận dạng tiền và kiểm tra điều kiện. Với bộ dữ liệu hiện tại, normalization, alias và slot extraction quan trọng hơn việc xây dựng pipeline NLP nặng.

---

## 5. Dịch vụ dữ liệu sản phẩm

### 5.1. PostgreSQL, schema và vòng đời dữ liệu

PostgreSQL là nguồn chuẩn duy nhất khi web chạy. CSV chỉ được đọc bởi lệnh seed riêng để nhập dữ liệu ban đầu hoặc một đợt cập nhật được chủ động yêu cầu; Flask không tự seed, không đọc CSV mỗi request và không dùng JSON để bù trường.

#### Schema tối thiểu

- `products`: `id` (giữ ID gốc trong CSV làm khóa chính), tên, hãng, giá VND, hệ điều hành, chip, RAM/ROM, pin, sạc, màn hình, tần số quét, camera trước/sau, URL ảnh và URL sản phẩm; có thể thêm `created_at`/`updated_at` để theo dõi thay đổi.
- `tags`: khóa chính, `slug` duy nhất và tên hiển thị nếu cần.
- `product_tags`: khóa ngoại tới `products` và `tags`, khóa chính ghép (`product_id`, `tag_id`) để tránh gắn tag trùng cho cùng sản phẩm.
- Không lưu toàn bộ `tags_nhu_cau` dạng chuỗi phẩy trong bảng sản phẩm. Seed sẽ tách chuỗi CSV thành bản ghi quan hệ; truy vấn tag dùng join chính xác.

`products.id` giữ ID nguồn giúp detail/compare và kiểm tra seed ổn định. Khóa chính, unique, not-null và foreign key phải được áp dụng trong database chứ không chỉ dựa vào kiểm tra của form/app.

#### Quy trình thiết lập và dùng

1. Cài PostgreSQL và tạo database cùng hai role riêng: `phone_admin` để chạy migration/seed và `phone_app` để chạy Flask. Không dùng tài khoản superuser khi chạy Flask; trong phiên bản chỉ tư vấn, `phone_app` chỉ cần quyền SELECT.
2. Lưu `DATABASE_URL` và `DATABASE_ADMIN_URL` trong `.env` local; chỉ commit `.env.example` với giá trị giả. App đọc `DATABASE_URL`; Alembic/seed dùng credential admin. Ví dụ: `postgresql+psycopg://phone_app:...@localhost:5432/phone_advisor`.
3. Khai báo SQLAlchemy models trong `src/phone_advisor/db/models.py`; tạo migration Alembic cho ba bảng và các ràng buộc bằng role admin. Review migration được autogenerate trước khi áp dụng.
4. Tạo engine và `sessionmaker` một lần lúc khởi tạo app. Mỗi request mở một Session, commit khi có thao tác ghi, rollback khi lỗi và luôn đóng Session. Không giữ Session dùng chung toàn cục giữa requests.
5. Chạy migration bằng lệnh tường minh, sau đó chạy lệnh seed (ví dụ `python -m scripts.seed_catalog`) để kiểm tra CSV rồi nhập dữ liệu. Seed mặc định chỉ chạy khi bảng sản phẩm chưa có dữ liệu; nhập lại cần cờ `--upsert` được định nghĩa rõ.
6. Seed ánh xạ ID, kiểu số, null và tag; kiểm tra khóa trùng/giá trị sai trước khi commit transaction. Nếu lỗi giữa chừng thì rollback toàn bộ batch, tránh catalog nạp dở. Nếu cột ID dùng identity/sequence để hỗ trợ thêm sản phẩm sau này, đồng bộ sequence tới ID lớn nhất sau khi nạp ID nguồn.
7. Viết catalog repository truy vấn PostgreSQL. Các bộ lọc hãng/giá/thông số/tag chạy ở database; ranking sở thích có thể thực hiện ở Python sau khi SQL đã lọc tập ứng viên.
8. Trong phạm vi hiện tại, thay đổi catalog bằng lệnh import có chủ đích và ghi lại nguồn/ngày nhập. Nếu sau này làm UI quản trị, route riêng phải xác thực/phân quyền và ghi database qua repository. Không xóa sản phẩm chỉ vì nó vắng mặt trong CSV mới nếu chưa chọn quy tắc đồng bộ có chủ ý.

**Vì sao dùng database cho website mô phỏng?** Dữ liệu tồn tại sau khi tắt/mở server; nhiều request cùng truy cập một nguồn; ràng buộc quan hệ giúp bảo vệ tính nhất quán; backend có thể thay đổi dữ liệu mà không sửa file CSV. CSV là cách chuyển dữ liệu ban đầu vào hệ thống, tương tự một đợt import.

Giá lưu trong database vẫn chỉ là snapshot từ bộ dữ liệu nhập vào, không mặc nhiên là giá thị trường hiện tại. Nếu có ngày thu thập đã xác nhận, lưu metadata/ngày cập nhật; nếu không, không suy đoán ngày.

Các tên trường trong schema tool ánh xạ đến cột model/database, ví dụ `min_refresh_rate_hz` → `Product.tan_so_quet_hz`; giá tính bằng VND, RAM/ROM bằng GB và pin bằng mAh.

### 5.2. Truy vấn theo điều kiện

Áp dụng điều kiện cứng trước:

- hãng được yêu cầu;
- giá tối đa/tối thiểu;
- RAM/ROM/pin tối thiểu;
- tần số quét tối thiểu nếu được nêu;
- hãng, tag hoặc model bị loại trừ;
- mọi tag trong `required_tags` (điều kiện AND);
- với mỗi nhóm trong `required_tag_groups`, ít nhất một tag của nhóm phải khớp (AND giữa các nhóm, OR trong từng nhóm).

Sau đó mới xếp hạng theo `preferences`; mỗi phần tử `any_of` khớp nếu sản phẩm có ít nhất một tag trong danh sách đó. Sở thích không khớp không làm sản phẩm bị loại khỏi kết quả. Câu “pin khỏe” có thể được biểu diễn bằng một sở thích `any_of: [pin_trau, pin_khung]`.

Tag cần so khớp theo phần tử chính xác sau khi tách chuỗi, không tìm bằng cách kiểm tra chuỗi con. Ví dụ tag choi_game không nên bị khớp nhầm với một chuỗi có ký tự tương tự nhưng khác tag.

### 5.3. Xếp hạng gợi ý

Quy tắc gợi ý ban đầu nên đơn giản, xác định và giải thích được:

1. Không được bỏ qua điều kiện cứng để đưa máy “gần đúng”.
2. Tính điểm sở thích bằng tổng `priority` của các mục `preferences` khớp; mỗi mục có `any_of` chỉ được tính một lần dù khớp nhiều tag.
3. Sắp xếp theo điểm sở thích giảm dần. Nếu người dùng nêu thứ tự ưu tiên, dùng `priority` cao hơn cho tiêu chí quan trọng hơn.
4. Khi ưu tiên pin, dùng `pin_mah` giảm dần để phân định các máy ngang điểm; chỉ dùng RAM, ROM hoặc tần số quét khi thông số đó liên quan trực tiếp đến yêu cầu.
5. Không dùng số megapixel làm đại diện cho chất lượng camera; chỉ dùng tag camera có sẵn hoặc so sánh độ phân giải nếu người dùng hỏi đúng trường đó.
6. Nếu vẫn ngang nhau, sắp theo giá tăng dần rồi `id` tăng dần để kết quả ổn định giữa các lần chạy.
7. Trả tối đa ba kết quả gợi ý mặc định. Không có kết quả thì báo rõ và hỏi người dùng muốn nới điều kiện nào; không tự nới.

Với `search` không có sở thích, trả mọi dòng thỏa bộ lọc theo thứ tự giá tăng dần rồi `id` tăng dần. Với `recommend` không nêu ngân sách nhưng có sở thích, vẫn có thể gợi ý; phải nói rõ kết quả chưa lọc theo ngân sách và hỏi ngân sách để tinh chỉnh.

Không nên tự đánh giá chip chỉ từ tên chuỗi chip_cpu nếu chưa có bảng xếp hạng/benchmark đáng tin cậy. Có thể dùng tag chip_gaming như một tín hiệu có sẵn, nhưng phải phân biệt tag này với kết luận benchmark.

### Ví dụ truy vấn sản phẩm

Câu hỏi:

> “Tìm giúp mình Xiaomi chơi game, pin trâu, dưới 15 củ.”

Điều kiện cứng:

~~~text
hang = Xiaomi
gia_ban < 15.000.000
~~~

Sở thích mềm:

~~~text
choi_game
pin_trau
~~~

Một số dòng dữ liệu hiện có khớp các điều kiện này:

| Sản phẩm | Giá trong database | RAM | Pin | Dấu hiệu liên quan |
|---|---:|---:|---:|---|
| Xiaomi Redmi Note 17 Pro Max 8GB/256GB | 14.190.000đ | 8GB | 10.000mAh | choi_game, pin_trau, pin_khung |
| Xiaomi POCO X8 Pro 5G 8GB/256GB | 12.990.000đ | 8GB | 6.500mAh | choi_game, pin_trau, chip_gaming |
| Xiaomi Redmi Note 15 Pro 5G 8GB/256GB | 8.290.000đ | 8GB | 6.580mAh | choi_game, pin_trau, chip_gaming |

Câu trả lời nên nêu rõ sự đánh đổi, ví dụ: máy có pin lớn nhất, máy có tag chip_gaming, và lựa chọn giá thấp hơn. Không nên khẳng định một máy “chơi game tốt nhất” chỉ từ tên chip hoặc suy đoán ngoài dữ liệu trong database.

---

## 6. Công cụ Agent được phép gọi

Giữ số công cụ ít và mỗi công cụ có một trách nhiệm rõ:

### 6.1. recommend_phones

Dùng cho `recommend` và `search`. Khi là `search`, truyền `preferences: []` để chỉ áp dụng bộ lọc; khi là `recommend`, dùng sở thích để xếp hạng. Tool luôn áp dụng tất cả điều kiện bắt buộc trước.

Đầu vào:

~~~json
{
  "filters": {
    "brand": "Xiaomi",
    "min_price_vnd": null,
    "max_price_vnd": 15000000,
    "min_price_inclusive": true,
    "max_price_inclusive": false,
    "min_ram_gb": null,
    "min_rom_gb": null,
    "min_battery_mah": null,
    "min_refresh_rate_hz": null,
    "required_tags": [],
    "required_tag_groups": []
  },
  "excluded_brands": [],
  "excluded_tags": [],
  "excluded_product_ids": [],
  "preferences": [
    {"any_of": ["pin_trau", "pin_khung"], "priority": 2}
  ],
  "limit": 3
}
~~~

Quy tắc xác thực: hãng phải thuộc danh sách trong database; tag phải thuộc tập tag đã nạp; ID loại trừ phải tồn tại; giá và thông số là số không âm; nếu có cả min/max thì min không lớn hơn max; cờ `*_inclusive` là boolean; `limit` là số nguyên từ 1 đến 3. Mọi `required_tags` đều phải khớp (AND); với mỗi `required_tag_groups`, ít nhất một tag phải khớp; sản phẩm có bất kỳ `excluded_tags` nào đều bị loại. Mỗi `preferences` có `any_of` không rỗng và `priority` là số nguyên 1–3; preference chỉ tác động thứ tự.

Đầu ra thành công gồm `status: "ok"`, `items` (các bản ghi sản phẩm đã chọn trường cần dùng), `applied_filters` và `matched_preferences`. Nếu không có kết quả, trả `status: "not_found"` cùng `applied_filters`; không tự bỏ điều kiện để tìm kết quả gần đúng.

### 6.2. get_phone_detail

Dùng khi khách hỏi thông tin một mẫu cụ thể. Tool nhận `product_id` đã được backend phân giải. Nếu tên người dùng khớp nhiều ID, backend hỏi lại trước khi gọi tool; tool không tự chọn phiên bản.

Đầu vào là `{ "product_id": 57 }`, trong đó ID phải tồn tại trong catalog. Đầu ra là `{ "status": "ok", "item": { ... } }` với trường sản phẩm đã truy vấn từ database; ID không tồn tại trả `status: "not_found"`.

**Xử lý đa phiên bản ROM:** database có thể có nhiều dòng cho cùng 1 model chỉ khác ROM (ví dụ iPhone 17 Pro Max có bản 256GB, 512GB và 1TB). Khi người dùng hỏi tên model mà không nêu dung lượng:

1. Nhóm các bản ghi theo tên model gốc (bỏ phần "256GB/512GB/1TB").
2. Nếu nhóm có nhiều hơn 1 dòng → trả danh sách phiên bản kèm giá:

~~~text
IPhone 17 Pro Max có các phiên bản:
  • 256GB — 34.990.000đ
  • 512GB — 39.990.000đ
  • 1TB  — 44.990.000đ
Bạn muốn xem phiên bản nào?
~~~

3. Nếu nhóm chỉ có 1 dòng → trả chi tiết luôn.

### 6.3. compare_phones

Dùng để so sánh 2–3 sản phẩm theo trường có trong database: hệ điều hành, giá, RAM, ROM, công suất sạc, pin, màn hình, camera và tags. Không tạo kết luận không có dữ liệu hỗ trợ.

Đầu vào là `{ "product_ids": [57, 63] }`, gồm đúng 2 hoặc 3 ID đã xác định. Đầu ra giữ cùng thứ tự ID, ví dụ `{ "status": "ok", "items": [{...}, {...}] }`, và trả các trường có trong database; trường thiếu được trả là `null`, không được suy đoán. Nếu có ID không tồn tại, trả `not_found` cho toàn bộ yêu cầu thay vì so sánh một phần.

**Lưu ý khi so sánh chip:** cột `chip_cpu` là chuỗi mô tả tự do (ví dụ "Apple A19 Pro 6 nhân", "Snapdragon 8s Gen 4"). Khi so sánh, chỉ **liệt kê tên chip** của từng máy, không được kết luận chip nào "mạnh hơn" hay "yếu hơn" nếu không có dữ liệu benchmark đáng tin cậy.

### 6.4. browse_phones

Dùng cho yêu cầu khám phá danh mục như “Có những hãng nào?” hoặc “Liệt kê Samsung”. Đầu vào:

~~~json
{
  "filters": {
    "brand": "Samsung",
    "min_price_vnd": null,
    "max_price_vnd": null,
    "min_price_inclusive": true,
    "max_price_inclusive": true
  },
  "page": 1,
  "page_size": 20
}
~~~

`page` là số nguyên từ 1; `page_size` mặc định 20 và là số nguyên từ 1 đến 20. Đầu ra có `status`, `items`, `total`, `page`, `page_size` và `facets.brands` (hãng phân biệt trong toàn bộ catalog). Kết quả phải sắp ổn định theo giá tăng dần rồi ID. Nếu chỉ hỏi danh sách hãng, truy vấn các hãng phân biệt trong database và không gọi LLM để suy ra hãng mới.

### 6.5. Schema đầu ra và lỗi chung

Mọi tool trả dữ liệu JSON có cấu trúc. `ProductCard` dùng cho kết quả gợi ý gồm `id`, `ten_san_pham`, `hang`, `gia_ban`, `ram_gb`, `rom_gb`, `chip_cpu`, `pin_mah`, `man_hinh_inch`, `tan_so_quet_hz`, `tags_nhu_cau`, `hinh_anh` và `url`. Tags trả về dưới dạng mảng tag chuẩn; số liệu trả dưới dạng số hoặc `null`. Detail/compare có thể trả thêm `he_dieu_hanh`, `sac_w`, `camera_sau_mp` và `camera_truoc_mp` nếu có trong database. Chỉ gửi các sản phẩm được chọn và các trường cần cho câu trả lời, không gửi toàn bộ catalog.

Kết quả nghiệp vụ dùng `status: "ok"` hoặc `"not_found"`. Đầu vào không hợp lệ bị từ chối ở backend bằng `{ "error": { "code": "VALIDATION_ERROR", "message": "..." } }`; lỗi Ollama/catalog dùng `SERVICE_UNAVAILABLE`. Nội dung lỗi dành cho log kỹ thuật không được đưa nguyên văn cho người dùng. Yêu cầu mơ hồ được xử lý bằng hỏi lại trước khi gọi tool, không phải lỗi tool.

Các tool chỉ truy vấn database bằng repository đã định nghĩa. Tool detail và compare nhận ID, không nhận câu lệnh SQL hoặc đường dẫn tùy ý. Backend xác thực ID thuộc catalog trước khi trả dữ liệu.

### Quy trình an toàn cho một lần gọi tool

1. Backend ánh xạ intent sang tool: `recommend/search` → `recommend_phones`; `detail` → `get_phone_detail`; `compare` → `compare_phones`; `browse` → `browse_phones`. Greeting/out-of-scope được xử lý bằng mẫu, không gọi tool.
2. Ollama chỉ được phép gọi tool đã được chọn cho intent hiện tại; tool registry từ chối mọi tên hàm khác.
3. Schema kiểm tra kiểu dữ liệu, khoảng giá, hãng, danh sách tag, ID và giới hạn kết quả. Backend đối chiếu đối số với yêu cầu NLP đã xác thực để Agent không thể bỏ hoặc thay điều kiện cứng.
4. Catalog chạy truy vấn chỉ đọc.
5. Kết quả được trả về Agent dưới dạng dữ liệu có cấu trúc.
6. Agent viết câu trả lời dựa trên kết quả đó.

Giới hạn tối đa hai lần gọi tool trong một lượt hội thoại. Nếu lời gọi lỗi hoặc model lặp lại, dừng vòng lặp và trả thông báo phù hợp. Agent chỉ có tool đọc; không cấp quyền ghi database cho Agent. Nếu sau này có trang quản trị, thao tác ghi phải qua route riêng có xác thực, kiểm tra đầu vào và phân quyền.

Câu người dùng, kết quả Ollama và mọi trường sản phẩm trong database đều là dữ liệu không đáng tin cậy, không phải chỉ dẫn hệ thống. Không để nội dung từ người dùng/database thay đổi whitelist, schema hoặc chính sách lọc.

### 6.6. Mẫu system prompt cho Ollama

Dưới đây là mẫu system prompt tối thiểu để Agent hoạt động đúng vai trò. Có thể điều chỉnh ngôn từ nhưng phải giữ đủ các ràng buộc:

~~~text
Bạn là trợ lý tư vấn điện thoại. Nhiệm vụ của bạn là giúp khách hàng tìm điện thoại
phù hợp từ danh mục sản phẩm có sẵn.

QUY TẮC BẮT BUỘC:
1. Chỉ nêu giá và thông số sản phẩm có trong kết quả tool. Không tự bịa tồn kho,
   chính sách bảo hành hoặc dữ liệu không có trong database.
2. Khi nêu giá, nói rõ đây là giá trong dữ liệu website đã nhập, không đảm bảo là giá hiện tại.
   Chỉ nêu ngày dữ liệu nếu nguồn có lưu ngày đó.
3. Không được tự đánh giá chip mạnh/yếu chỉ từ tên chip. Nếu cần so sánh
   hiệu năng, chỉ liệt kê tên chip và tag chip_gaming (nếu có).
4. Không tự nới hoặc sửa điều kiện cứng. Nếu không có kết quả, báo rõ và hỏi
   khách muốn nới điều kiện nào.
5. Trả lời bằng tiếng Việt, tự nhiên và thân thiện.
6. Không dùng ngôn ngữ quảng cáo: "rẻ nhất thị trường", "mạnh nhất phân khúc",
   "giá mới nhất" nếu database không có căn cứ.
7. Mỗi gợi ý cần kèm lý do ngắn gọn dựa trên trường hoặc tag có trong kết quả.
8. Không tạo nội dung HTML/JavaScript. Lời chào và câu ngoài phạm vi do backend
   trả bằng mẫu cố định; không cần gọi tool.

CÔNG CỤ ĐƯỢC PHÉP GỌI:
- recommend_phones: gợi ý điện thoại theo điều kiện.
- get_phone_detail: xem chi tiết một mẫu cụ thể.
- compare_phones: so sánh 2 hoặc 3 mẫu đã xác định.
- browse_phones: liệt kê danh mục theo bộ lọc và trang.

Không gọi công cụ nào khác ngoài bốn công cụ trên.
Tối đa 2 lần gọi công cụ trong một lượt trả lời.
~~~

Lưu prompt này trong thư mục `agent/prompts/` dưới dạng file text hoặc hằng chuỗi trong `orchestrator.py`. Đọc từ cấu hình nếu cần thay đổi mà không sửa mã. Backend chịu trách nhiệm ghép các mẫu greeting/out-of-scope và kiểm tra nội dung trước khi hiển thị.

---

## 7. Ví dụ hội thoại từ đầu đến cuối

### Trường hợp 1 — Câu hỏi đủ thông tin

**Người dùng:** “Tìm giúp mình Xiaomi chơi game, pin trâu, dưới 15 củ.”

**NLP:** nhận diện intent recommend; `filters` gồm hãng Xiaomi và giá tối đa 15.000.000đ; `preferences` gồm chơi game và pin khỏe. Hai tag là sở thích, không phải điều kiện loại máy.

**Agent:** gọi recommend_phones với các điều kiện đã xác thực.

**Catalog:** lọc theo hãng và giá; giữ mọi máy thỏa điều kiện bắt buộc; sau đó xếp hạng theo sở thích khớp.

**Agent trả lời:** đưa tối đa ba sản phẩm, mỗi sản phẩm có giá theo database, RAM, pin và lý do được chọn. Ghi chú giá là theo dữ liệu website đã nhập, không gọi là giá trực tuyến hiện tại.

### Trường hợp 2 — Thiếu ngân sách

**Người dùng:** “Mình muốn máy chụp ảnh đẹp.”

**NLP:** intent recommend, preferences chup_anh_dep; chưa có ngân sách.

**Ứng xử:** gợi ý tối đa ba máy theo sở thích, nói rõ danh sách chưa lọc theo ngân sách, rồi hỏi mức chi để tinh chỉnh.

### Trường hợp 3 — Câu tiếp nối

**Người dùng:** “Tìm Samsung dưới 15 triệu.”
**Người dùng:** “Ưu tiên pin trâu nhé.”

**Ngữ cảnh hội thoại:** giữ hãng Samsung và giá tối đa từ lượt trước; thêm sở thích `any_of: [pin_trau]` ở lượt sau. State chỉ có hiệu lực trong phiên chat hiện tại.

### Trường hợp 4 — Không tìm thấy sản phẩm

**Người dùng:** “Tìm iPhone dưới 3 triệu, RAM ít nhất 16GB.”

Nếu database không có sản phẩm đạt cả hai điều kiện, bot không được tự bỏ điều kiện RAM hoặc ngân sách. Trả lời không có kết quả và hỏi người dùng muốn nới điều kiện nào.

---

## 8. Giao diện và định dạng câu trả lời

Giao diện tối thiểu nên có:

- vùng hội thoại;
- ô nhập câu hỏi;
- thẻ sản phẩm cho mỗi kết quả;
- ảnh từ hinh_anh nếu liên kết hợp lệ;
- tên, hãng, giá, RAM/ROM, chip, pin và tag phù hợp;
- liên kết url nếu có.

Mỗi gợi ý nên có một câu giải thích gắn với nhu cầu cụ thể, chẳng hạn “khớp ngân sách và có tag pin_trau”. Không tạo nội dung quảng cáo như “rẻ nhất thị trường”, “giá mới nhất” hay “mạnh nhất phân khúc” nếu database không chứa căn cứ tương ứng.

### Hợp đồng API chat

Giao diện gửi `POST /api/chat` với JSON `{ "message": "..." }`; backend kiểm tra body JSON, từ chối tin nhắn rỗng hoặc vượt giới hạn cấu hình và nhận diện phiên bằng cookie session. Cookie đặt `HttpOnly` và `SameSite`; bật `Secure` khi chạy qua HTTPS. Chỉ cho phép origin cần thiết, không bật CORS wildcard; nếu chỉ dùng local thì bind server vào loopback (`127.0.0.1`). Phản hồi thành công có dạng:

~~~json
{
  "status": "ok",
  "reply": "Câu trả lời tiếng Việt",
  "products": [],
  "clarification": null
}
~~~

Khi cần hỏi lại, trả `status: "needs_clarification"`, câu hỏi trong `clarification` và không gọi catalog với điều kiện chưa xác nhận. Dùng HTTP 200 cho câu trả lời/clarification, 422 cho đầu vào không hợp lệ và 503 cho dịch vụ không sẵn sàng. Lỗi dùng một dạng thống nhất `{ "error": { "code": "...", "message": "..." } }`; không đưa traceback hoặc nội dung nội bộ ra giao diện. Với cookie session, bảo vệ POST bằng token CSRF hoặc cơ chế tương đương cùng kiểm tra origin.

Giao diện phải escape nội dung văn bản, không render HTML do LLM tạo. Chỉ hiển thị ảnh/liên kết có URL `https` hợp lệ thuộc domain allowlist cấu hình; liên kết ngoài mở tab mới phải dùng `rel="noopener noreferrer"`. Flask bật các security headers phù hợp như CSP, `X-Content-Type-Options` và chống nhúng trang ngoài ý muốn. Không ghi toàn bộ hội thoại hoặc cookie/session ID vào log.

---

## 9. Cấu hình và giới hạn phần cứng

Tài liệu ban đầu nêu máy có Intel Core Ultra 7, RTX 3050 Ti Laptop 4GB VRAM, 16GB RAM, Ollama và các model Qwen cài sẵn. Đây là bối cảnh triển khai local; không nên xem các con số tốc độ hoặc mức VRAM ước tính là cam kết.

- Đọc `DATABASE_URL`, tên model và cấu hình máy chủ từ biến môi trường/cấu hình ứng dụng; không ghi mật khẩu database vào mã hoặc Git.
- Chạy migration Alembic tường minh trước khi khởi động phiên bản mới; không tự tạo/sửa schema trong lúc Flask start bằng `create_all`.
- Dùng quyền database tối thiểu: web tư vấn chỉ cần đọc catalog; migration/import dùng credential bảo trì riêng. Đóng Session sau request và xử lý lỗi database có timeout/thông báo phù hợp.
- Đọc `SECRET_KEY`, thời hạn session và timeout gọi Ollama từ cấu hình môi trường; không ghi khóa bí mật vào mã nguồn.
- Khi dùng cookie session, bật `HttpOnly`, `SameSite` và `Secure` trên HTTPS; bảo vệ `POST /api/chat` khỏi CSRF và chỉ cho phép CORS từ origin được cấu hình.
- Đo thời gian khởi động, thời gian phản hồi, mức RAM/VRAM và tốc độ sinh token trên chính máy chạy đồ án.
- Kết quả phụ thuộc phiên bản model, lượng ngữ cảnh, quantization, tiến trình khác đang chạy và mức GPU offload của Ollama.
- Nếu model 3B thiếu bộ nhớ hoặc phản hồi chậm, thử cấu hình/model nhẹ hơn đã cài; ghi lại phép đo thay vì cam kết một con số chung.
- Nếu Ollama tắt, model chưa sẵn sàng hoặc hết timeout, Flask cần báo bot tạm thời không kết nối được, không làm ứng dụng treo vô hạn. Catalog vẫn phải hoạt động độc lập; backend có thể dùng mẫu trả lời cố định để trình bày các kết quả catalog khi phần diễn đạt bằng LLM lỗi.

Không khẳng định chatbot luôn trả lời dưới một giây, toàn bộ model luôn nằm trong VRAM, hay dùng CPU dưới một tỷ lệ cố định trước khi đo thực tế.

---

## 10. Các bước thực hiện theo thứ tự

| Buổi | Cách làm | Vì sao | Kết quả cần có |
|---:|---|---|---|
| 1 | Chốt phạm vi, tạo môi trường Python và Flask app tối thiểu | Xác nhận nền chạy trước khi thêm nhiều lớp | App chạy local và cấu hình cơ bản |
| 2 | Kiểm tra header, kiểu dữ liệu, tag, ID và URL trong CSV | Phát hiện lỗi đầu vào trước khi ghi vào database | Data dictionary và danh sách vấn đề |
| 3 | Tạo PostgreSQL, SQLAlchemy models và migration Alembic | Schema/ràng buộc phải có trước khi import | Ba bảng products/tags/product_tags được tạo bằng migration |
| 4 | Seed CSV bằng lệnh riêng, rồi tạo repository truy vấn DB | Tách import khỏi runtime và bảo đảm dữ liệu bền vững | Catalog đọc DB; Flask không đọc CSV |
| 5–6 | Làm search/browse, recommend/detail/compare | Xác nhận nghiệp vụ sản phẩm độc lập với NLP/LLM | Bộ catalog có thứ tự ổn định và đúng điều kiện |
| 7–9 | Làm chuẩn hóa, intent/slots và state hội thoại | Câu tiếng Việt cần thành request có cấu trúc, giữ đúng ngữ cảnh | Request đã xác thực và câu hỏi làm rõ khi cần |
| 10–11 | Tạo whitelist tool, sau đó tích hợp Agent/Ollama | Chỉ cho model gọi nghiệp vụ được phép | Tool an toàn; có timeout/fallback |
| 12–13 | Tạo API Flask và giao diện chat | Hoàn chỉnh luồng trình duyệt → API → catalog/database | Người dùng hỏi, xem và tiếp tục hội thoại |
| 14 | Đánh giá dữ liệu, API, UI và chuẩn bị kịch bản demo | Tìm lỗi theo từng lớp và giúp demo lặp lại được | Báo cáo đánh giá cùng hướng dẫn chạy |

### Thứ tự làm khuyến nghị

Hoàn thành Buổi 1–10 và xác nhận database, catalog, parser cùng whitelist tool trước khi tích hợp Ollama ở Buổi 11. Nếu Agent được làm trước, khó phân biệt lỗi do model hiểu sai với lỗi truy vấn database hoặc parser.

---

## 11. Kịch bản kiểm tra và tiêu chí đạt

Nên chuẩn bị câu hỏi tiếng Việt có dấu/không dấu, tiếng lóng, câu hỏi thiếu dữ kiện và câu tiếp nối. Các kiểm tra chính:

1. “Xiaomi chơi game dưới 15 triệu” không trả sản phẩm ngoài hãng/giá; sở thích chơi game ảnh hưởng xếp hạng nhưng không loại máy không có tag đó.
2. “Pin trâu” ánh xạ thành sở thích; “bắt buộc pin ít nhất 6000mAh” thành điều kiện cứng; kết quả dùng `pin_mah` để giải thích/xếp hạng.
3. “Không lấy Apple” loại Apple khỏi kết quả.
4. “Từ 10 đến 15 triệu” không bị hiểu thành chỉ giá tối đa 10 triệu.
5. “Dưới 15 triệu” loại máy đúng 15.000.000đ; “tối đa 15 triệu” cho phép máy đúng ngưỡng.
6. Câu có hai điều kiện giá mâu thuẫn thì bot hỏi lại.
7. Model có nhiều phiên bản thì không tự chọn sai ROM.
8. Không tìm thấy kết quả thì bot báo rõ, không tự nới điều kiện cứng.
9. “Không lấy máy gập” loại sản phẩm có tag `thiet_ke_gap`; “không cần máy gập” không tự động loại sản phẩm.
10. Agent không tự tạo giá, chip, tồn kho hoặc chính sách không có trong dữ liệu.
11. Lời gọi tool sai schema hoặc ngoài whitelist không được thực thi.
12. Khi Ollama không kết nối, giao diện dùng phản hồi dự phòng có kiểm soát.
13. `search`, `recommend` và `browse` tạo hành vi khác nhau theo định nghĩa; duyệt danh mục có phân trang.
14. HTML/JavaScript trong câu trả lời hoặc dữ liệu sản phẩm không được thực thi trong giao diện; state của hai phiên không bị trộn.

Mọi trường hợp kiểm tra điều kiện cứng phải đạt 100% tuân thủ; đây là yêu cầu đúng/sai của bộ lọc, không phải chỉ số trung bình. Nếu đánh giá theo môn NLP, lập tập câu hỏi có nhãn intent/slots, tách tập đánh giá trước khi tinh chỉnh luật và không dùng câu phát triển luật làm toàn bộ tập đánh giá. Báo cáo độ đúng intent, precision/recall/F1 cho slot quan trọng, tỷ lệ tuân thủ điều kiện cứng, kết quả top 3 theo rubric đã định nghĩa và lỗi tiêu biểu. Chốt ngưỡng đạt cho intent/slot trước khi chạy đánh giá; không chọn ngưỡng sau khi đã xem kết quả.

---

## 12. Giới hạn và hướng mở rộng

- Giá trong PostgreSQL chỉ phản ánh dữ liệu đã nhập; chưa có cơ chế đồng bộ giá trực tuyến.
- Tag là nhãn của bộ dữ liệu; chất lượng gợi ý phụ thuộc tag được gán chính xác.
- Chip CPU đang là chuỗi mô tả. Muốn xếp hạng hiệu năng chip đáng tin cậy cần bổ sung dữ liệu chuẩn hóa hoặc benchmark có nguồn.
- Chưa có lịch sử mua hàng, tồn kho, màu sắc, cửa hàng hoặc chính sách bảo hành.
- Chỉ thêm RAG khi có kho tài liệu dạng văn bản cần tìm kiếm; không thêm vector database chỉ để truy vấn dữ liệu quan hệ.
- Khi đồ án cần mở rộng, có thể thêm trang quản trị CRUD sản phẩm, nhập bộ dữ liệu mới, lịch sử giá/tồn kho hoặc đánh giá chất lượng gợi ý mà vẫn giữ giao diện catalog service.

---

## 13. Kết luận

Kiến trúc phù hợp nhất với phạm vi hiện tại là **Flask + PostgreSQL + SQLAlchemy/Alembic + NLP tiếng Việt dạng kết hợp + Ollama Agent gọi công cụ**. CSV chỉ seed dữ liệu ban đầu; PostgreSQL là nguồn chuẩn khi web chạy. NLP hiểu câu hỏi, Agent điều phối và diễn đạt, còn catalog truy vấn và xếp hạng dữ liệu xác định. Cách phân chia này mô phỏng web thật mà vẫn dễ làm theo từng bước và tránh để LLM tự bịa thông tin sản phẩm.

### Tài liệu kỹ thuật tham khảo

- [PostgreSQL: constraints và bảng](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [SQLAlchemy 2.0: quản lý Session](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [SQLAlchemy 2.0: PostgreSQL và psycopg](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [Alembic: autogenerate migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) — migration tự sinh cần được review trước khi chạy.

