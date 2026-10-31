# KIẾN TRÚC VÀ HƯỚNG DẪN THỰC HIỆN CHATBOT TƯ VẤN ĐIỆN THOẠI

> **Phạm vi:** chatbot tiếng Việt giúp người dùng tìm và gợi ý điện thoại từ CSV bằng Flask, NLP và AI Agent chạy qua Ollama.
>
> **Không nằm trong phiên bản này:** chính sách bảo hành, kiểm tra tồn kho, cập nhật giá trực tuyến, đặt hàng/thanh toán và tư vấn dựa trên tài liệu dài.

---

## 1. Tóm tắt quyết định kiến trúc

Đề xuất làm một **ứng dụng Flask dạng modular monolith**: một ứng dụng chạy trên máy, bên trong chia thành các module có trách nhiệm riêng.

- Dùng **CSV làm nguồn dữ liệu chuẩn**. `dien_thoai_chuan_hoa.json` là bản xuất cùng dữ liệu; ứng dụng chỉ đọc một nguồn được cấu hình, không tự chọn giữa CSV và JSON.
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
    Catalog --> CSV[(dien_thoai_chuan_hoa.csv)]
    Catalog --> Results[Kết quả có cấu trúc]
    Results --> Agent
    Agent --> Answer[Câu trả lời tiếng Việt]
    Answer --> UI
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
| Dịch vụ danh mục | Lọc, so sánh và xếp hạng điện thoại | Kết quả cần ổn định, đúng theo CSV và có thể kiểm thử độc lập |
| CSV | Nguồn thông tin sản phẩm tại thời điểm chuẩn bị dữ liệu | Đơn giản, phù hợp quy mô hiện tại, dễ trình bày và kiểm tra |

---

## 3. Cấu trúc thư mục đề xuất

Đây là cấu trúc mục tiêu cho đồ án; có thể tạo dần theo các bước ở mục 10, không cần tạo tất cả thư mục trống từ đầu.

~~~text
E:\NLP/
├── data/
│   ├── dien_thoai_chuan_hoa.csv
│   ├── dien_thoai_chuan_hoa.json  # bản xuất; không phải nguồn độc lập
│   └── kientruc.md                # vị trí hiện tại của tài liệu này
├── src/
│   └── phone_advisor/
│       ├── __init__.py
│       ├── app.py
│       ├── config.py
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
│   └── test_agent_flow.py
├── requirements.txt
└── README.md
~~~

### Vai trò các module chính

- **web/**: route Flask, trang chat và thành phần hiển thị thẻ sản phẩm.
- **nlp/**: chuẩn hóa câu chữ, từ điển đồng nghĩa, nhận diện ý định, trích xuất điều kiện và giữ một số thông tin hội thoại cần thiết.
- **agent/**: lời nhắc hệ thống, điều phối Ollama, schema tham số và danh sách hàm Agent được phép gọi.
- **catalog/**: đọc CSV, lọc dữ liệu, xếp hạng kết quả, lấy chi tiết và so sánh.
- **config.py**: đường dẫn CSV, tên model và cấu hình chạy; tránh gắn cứng đường dẫn máy tính ở nhiều nơi.
- **data/**: CSV là nguồn chuẩn; JSON là bản xuất cần được tạo lại từ CSV khi dữ liệu thay đổi. Tài liệu này hiện ở `data/kientruc.md` theo vị trí của workspace.

Không cần tách thành nhiều dịch vụ/microservice. Với một CSV nhỏ và một máy chạy local, cách đó tăng cấu hình phải quản lý mà chưa đem lại lợi ích thiết thực.

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
| “Tại sao máy này đắt?” | Liệt kê thông số nổi bật từ CSV nhưng không đánh giá giá cả hợp lý hay không |
| “So sánh với laptop” | Nói rõ bot chỉ tư vấn điện thoại từ danh mục hiện có |

#### Bước C — Trích xuất thực thể và điều kiện

Các trường nên nhận diện:

- **Hãng**: Apple, Samsung, Xiaomi, OPPO, vivo, realme, HONOR, Tecno, Motorola, Nothing Phone, Nubia.
- **Model**: đối chiếu tên máy trong CSV, hỗ trợ tên gọi rút gọn nếu xác định được duy nhất.
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


#### Bước D — Chuẩn hóa từ đồng nghĩa sang tag của CSV

Tag phải lấy từ dữ liệu thật, không tự tạo tag mới khi truy vấn. Một số tag đang có trong CSV:

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

Người dùng thường không gọi đầy đủ tên sản phẩm. Cần xây dựng bảng `model_aliases` trong `aliases.py` để ánh xạ tên rút gọn về id sản phẩm trong CSV.

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

### 5.1. Nạp và kiểm tra CSV

Khi ứng dụng khởi động:

1. Đọc CSV từ cấu hình đường dẫn. CSV là nguồn chuẩn; JSON chỉ là bản xuất, không được đọc song song để bổ sung dữ liệu.
2. Kiểm tra các cột bắt buộc: id, ten_san_pham, hang, gia_ban, ram_gb, rom_gb, pin_mah và tags_nhu_cau.
3. Chuyển trường số sang kiểu số; báo lỗi rõ nếu giá hoặc thông số không thể chuyển đổi.
4. Tách tags_nhu_cau theo dấu phẩy thành tập tag, sau khi bỏ khoảng trắng.
5. Chuẩn hóa hãng để so khớp không phân biệt hoa thường.
6. Kiểm tra id không rỗng và duy nhất; cho phép trường tùy chọn như ảnh, URL hoặc một số thông số bị thiếu, nhưng không hiển thị giá trị bịa để thay thế.
7. Giữ id làm khóa sản phẩm; giữ hinh_anh và url cho thẻ kết quả.
8. Nạp dữ liệu một lần và dùng lại trong các truy vấn.

**Vì sao không đọc CSV lại ở mỗi câu hỏi?** Danh mục nhỏ có thể giữ trong bộ nhớ của ứng dụng. Nạp một lần giảm thao tác I/O, tránh lặp mã và giúp hiệu năng ổn định hơn. Khi CSV được cập nhật trong lúc phát triển, có thể khởi động lại ứng dụng để nạp lại.

Giá phải được mô tả là giá ghi trong CSV và không đảm bảo là giá hiện tại. Nếu có ngày thu thập được xác nhận, lưu ngày đó trong metadata và hiển thị; nếu không có, không suy đoán ngày.

Các tên trường trong schema tool được ánh xạ rõ về cột CSV: `min_refresh_rate_hz` → `tan_so_quet_hz`; các giá đều tính bằng VND, RAM/ROM bằng GB và pin bằng mAh.

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

Một số dòng trong CSV khớp các điều kiện này:

| Sản phẩm | Giá trong CSV | RAM | Pin | Dấu hiệu liên quan |
|---|---:|---:|---:|---|
| Xiaomi Redmi Note 17 Pro Max 8GB/256GB | 14.190.000đ | 8GB | 10.000mAh | choi_game, pin_trau, pin_khung |
| Xiaomi POCO X8 Pro 5G 8GB/256GB | 12.990.000đ | 8GB | 6.500mAh | choi_game, pin_trau, chip_gaming |
| Xiaomi Redmi Note 15 Pro 5G 8GB/256GB | 8.290.000đ | 8GB | 6.580mAh | choi_game, pin_trau, chip_gaming |

Câu trả lời nên nêu rõ sự đánh đổi, ví dụ: máy có pin lớn nhất, máy có tag chip_gaming, và lựa chọn giá thấp hơn. Không nên khẳng định một máy “chơi game tốt nhất” chỉ từ tên chip hoặc suy đoán ngoài CSV.

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

Quy tắc xác thực: hãng phải thuộc danh sách trong CSV; tag phải thuộc tập tag đã nạp; ID loại trừ phải tồn tại; giá và thông số là số không âm; nếu có cả min/max thì min không lớn hơn max; cờ `*_inclusive` là boolean; `limit` là số nguyên từ 1 đến 3. Mọi `required_tags` đều phải khớp (AND); với mỗi `required_tag_groups`, ít nhất một tag phải khớp; sản phẩm có bất kỳ `excluded_tags` nào đều bị loại. Mỗi `preferences` có `any_of` không rỗng và `priority` là số nguyên 1–3; preference chỉ tác động thứ tự.

Đầu ra thành công gồm `status: "ok"`, `items` (các bản ghi sản phẩm đã chọn trường cần dùng), `applied_filters` và `matched_preferences`. Nếu không có kết quả, trả `status: "not_found"` cùng `applied_filters`; không tự bỏ điều kiện để tìm kết quả gần đúng.

### 6.2. get_phone_detail

Dùng khi khách hỏi thông tin một mẫu cụ thể. Tool nhận `product_id` đã được backend phân giải. Nếu tên người dùng khớp nhiều ID, backend hỏi lại trước khi gọi tool; tool không tự chọn phiên bản.

Đầu vào là `{ "product_id": 57 }`, trong đó ID phải tồn tại trong catalog. Đầu ra là `{ "status": "ok", "item": { ... } }` với trường sản phẩm từ CSV; ID không tồn tại trả `status: "not_found"`.

**Xử lý đa phiên bản ROM:** CSV có nhiều dòng cho cùng 1 model chỉ khác ROM (ví dụ iPhone 17 Pro Max có bản 256GB, 512GB và 1TB). Khi người dùng hỏi tên model mà không nêu dung lượng:

1. Nhóm các dòng CSV theo tên model gốc (bỏ phần "256GB/512GB/1TB").
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

Dùng để so sánh 2–3 sản phẩm theo trường có trong CSV: hệ điều hành, giá, RAM, ROM, công suất sạc, pin, màn hình, camera và tags. Không tạo kết luận không có dữ liệu hỗ trợ.

Đầu vào là `{ "product_ids": [57, 63] }`, gồm đúng 2 hoặc 3 ID đã xác định. Đầu ra giữ cùng thứ tự ID, ví dụ `{ "status": "ok", "items": [{...}, {...}] }`, và trả các trường có trong CSV; trường thiếu được trả là `null`, không được suy đoán. Nếu có ID không tồn tại, trả `not_found` cho toàn bộ yêu cầu thay vì so sánh một phần.

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

`page` là số nguyên từ 1; `page_size` mặc định 20 và là số nguyên từ 1 đến 20. Đầu ra có `status`, `items`, `total`, `page`, `page_size` và `facets.brands` (hãng phân biệt trong toàn bộ catalog). Kết quả phải sắp ổn định theo giá tăng dần rồi ID. Nếu chỉ hỏi danh sách hãng, trả các hãng phân biệt có trong CSV và không gọi LLM để suy ra hãng mới.

### 6.5. Schema đầu ra và lỗi chung

Mọi tool trả dữ liệu JSON có cấu trúc. `ProductCard` dùng cho kết quả gợi ý gồm `id`, `ten_san_pham`, `hang`, `gia_ban`, `ram_gb`, `rom_gb`, `chip_cpu`, `pin_mah`, `man_hinh_inch`, `tan_so_quet_hz`, `tags_nhu_cau`, `hinh_anh` và `url`. Tags trả về dưới dạng mảng tag chuẩn; số liệu trả dưới dạng số hoặc `null`. Detail/compare có thể trả thêm `he_dieu_hanh`, `sac_w`, `camera_sau_mp` và `camera_truoc_mp` nếu có trong CSV. Chỉ gửi các sản phẩm được chọn và các trường cần cho câu trả lời, không gửi toàn bộ catalog.

Kết quả nghiệp vụ dùng `status: "ok"` hoặc `"not_found"`. Đầu vào không hợp lệ bị từ chối ở backend bằng `{ "error": { "code": "VALIDATION_ERROR", "message": "..." } }`; lỗi Ollama/catalog dùng `SERVICE_UNAVAILABLE`. Nội dung lỗi dành cho log kỹ thuật không được đưa nguyên văn cho người dùng. Yêu cầu mơ hồ được xử lý bằng hỏi lại trước khi gọi tool, không phải lỗi tool.

Các tool chỉ đọc CSV. Tool detail và compare nhận ID, không nhận câu lệnh hoặc đường dẫn tùy ý. Backend xác thực ID thuộc catalog trước khi trả dữ liệu.

### Quy trình an toàn cho một lần gọi tool

1. Backend ánh xạ intent sang tool: `recommend/search` → `recommend_phones`; `detail` → `get_phone_detail`; `compare` → `compare_phones`; `browse` → `browse_phones`. Greeting/out-of-scope được xử lý bằng mẫu, không gọi tool.
2. Ollama chỉ được phép gọi tool đã được chọn cho intent hiện tại; tool registry từ chối mọi tên hàm khác.
3. Schema kiểm tra kiểu dữ liệu, khoảng giá, hãng, danh sách tag, ID và giới hạn kết quả. Backend đối chiếu đối số với yêu cầu NLP đã xác thực để Agent không thể bỏ hoặc thay điều kiện cứng.
4. Catalog chạy truy vấn chỉ đọc.
5. Kết quả được trả về Agent dưới dạng dữ liệu có cấu trúc.
6. Agent viết câu trả lời dựa trên kết quả đó.

Giới hạn tối đa hai lần gọi tool trong một lượt hội thoại. Nếu lời gọi lỗi hoặc model lặp lại, dừng vòng lặp và trả thông báo phù hợp. CSV chỉ được đọc; không cung cấp tool sửa, xóa hoặc ghi đè dữ liệu.

Câu người dùng, kết quả Ollama và mọi trường CSV đều là dữ liệu không đáng tin cậy, không phải chỉ dẫn hệ thống. Không để nội dung từ người dùng/CSV thay đổi whitelist, schema hoặc chính sách lọc.

### 6.6. Mẫu system prompt cho Ollama

Dưới đây là mẫu system prompt tối thiểu để Agent hoạt động đúng vai trò. Có thể điều chỉnh ngôn từ nhưng phải giữ đủ các ràng buộc:

~~~text
Bạn là trợ lý tư vấn điện thoại. Nhiệm vụ của bạn là giúp khách hàng tìm điện thoại
phù hợp từ danh mục sản phẩm có sẵn.

QUY TẮC BẮT BUỘC:
1. Chỉ nêu giá và thông số sản phẩm có trong kết quả tool. Không tự bịa tồn kho,
   chính sách bảo hành hoặc dữ liệu không có trong CSV.
2. Khi nêu giá, nói rõ đây là giá ghi trong CSV, không đảm bảo là giá hiện tại.
   Chỉ nêu ngày dữ liệu nếu nguồn có lưu ngày đó.
3. Không được tự đánh giá chip mạnh/yếu chỉ từ tên chip. Nếu cần so sánh
   hiệu năng, chỉ liệt kê tên chip và tag chip_gaming (nếu có).
4. Không tự nới hoặc sửa điều kiện cứng. Nếu không có kết quả, báo rõ và hỏi
   khách muốn nới điều kiện nào.
5. Trả lời bằng tiếng Việt, tự nhiên và thân thiện.
6. Không dùng ngôn ngữ quảng cáo: "rẻ nhất thị trường", "mạnh nhất phân khúc",
   "giá mới nhất" nếu CSV không có căn cứ.
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

**Agent trả lời:** đưa tối đa ba sản phẩm, mỗi sản phẩm có giá theo CSV, RAM, pin và lý do được chọn. Ghi chú giá là theo dữ liệu trong bộ CSV, không gọi là giá trực tuyến hiện tại.

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

Nếu CSV không có sản phẩm đạt cả hai điều kiện, bot không được tự bỏ điều kiện RAM hoặc ngân sách. Trả lời không có kết quả và hỏi người dùng muốn nới điều kiện nào.

---

## 8. Giao diện và định dạng câu trả lời

Giao diện tối thiểu nên có:

- vùng hội thoại;
- ô nhập câu hỏi;
- thẻ sản phẩm cho mỗi kết quả;
- ảnh từ hinh_anh nếu liên kết hợp lệ;
- tên, hãng, giá, RAM/ROM, chip, pin và tag phù hợp;
- liên kết url nếu có.

Mỗi gợi ý nên có một câu giải thích gắn với nhu cầu cụ thể, chẳng hạn “khớp ngân sách và có tag pin_trau”. Không tạo nội dung quảng cáo như “rẻ nhất thị trường”, “giá mới nhất” hay “mạnh nhất phân khúc” nếu CSV không chứa căn cứ tương ứng.

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

- Đọc tên model, đường dẫn dữ liệu và cấu hình máy chủ từ cấu hình ứng dụng thay vì rải giá trị cố định trong mã.
- Đọc `SECRET_KEY`, thời hạn session và timeout gọi Ollama từ cấu hình môi trường; không ghi khóa bí mật vào mã nguồn.
- Khi dùng cookie session, bật `HttpOnly`, `SameSite` và `Secure` trên HTTPS; bảo vệ `POST /api/chat` khỏi CSRF và chỉ cho phép CORS từ origin được cấu hình.
- Đo thời gian khởi động, thời gian phản hồi, mức RAM/VRAM và tốc độ sinh token trên chính máy chạy đồ án.
- Kết quả phụ thuộc phiên bản model, lượng ngữ cảnh, quantization, tiến trình khác đang chạy và mức GPU offload của Ollama.
- Nếu model 3B thiếu bộ nhớ hoặc phản hồi chậm, thử cấu hình/model nhẹ hơn đã cài; ghi lại phép đo thay vì cam kết một con số chung.
- Nếu Ollama tắt, model chưa sẵn sàng hoặc hết timeout, Flask cần báo bot tạm thời không kết nối được, không làm ứng dụng treo vô hạn. Catalog vẫn phải hoạt động độc lập; backend có thể dùng mẫu trả lời cố định để trình bày các kết quả catalog khi phần diễn đạt bằng LLM lỗi.

Không khẳng định chatbot luôn trả lời dưới một giây, toàn bộ model luôn nằm trong VRAM, hay dùng CPU dưới một tỷ lệ cố định trước khi đo thực tế.

---

## 10. Các bước thực hiện theo thứ tự

| Bước | Cách làm | Vì sao | Kết quả cần có |
|---|---|---|---|
| 1. Chốt phạm vi và ý định | Chỉ hỗ trợ gợi ý, tìm, xem chi tiết, so sánh và duyệt danh mục điện thoại | Tránh ý định chồng lấn và tính năng không có dữ liệu | Định nghĩa hành vi mỗi intent, điều kiện cứng và sở thích mềm |
| 2. Chốt hợp đồng | Định nghĩa schema NLP, tool, API chat, kết quả và lỗi | Caller và module cần hiểu cùng một dữ liệu | Ví dụ JSON hợp lệ/không hợp lệ cho mỗi hợp đồng |
| 3. Kiểm tra dữ liệu | Đọc header, kiểu dữ liệu, tag, dòng trống, id trùng và liên kết ảnh/URL | Công cụ không thể tư vấn đúng nếu dữ liệu đầu vào sai | CSV nguồn chuẩn, bảng mô tả cột và các vấn đề dữ liệu |
| 4. Tạo khung ứng dụng | Tạo Flask entry point, cấu hình và module web/NLP/agent/catalog | Phân tách trách nhiệm giúp debug và trình bày đồ án rõ hơn | Ứng dụng chạy được với route cơ bản |
| 5. Làm catalog trước | Nạp CSV một lần, xác thực cột, viết lọc hãng/giá/thông số/tag | Có thể kiểm tra độ đúng của tìm kiếm độc lập với LLM | Truy vấn cho kết quả xác định |
| 6. Làm NLP baseline | Viết normalize, từ điển alias, intent và slot extraction theo ví dụ | Tạo thành phần NLP có thể giải thích, không phụ thuộc hoàn toàn vào prompt | Câu tự nhiên được chuyển thành cấu trúc chuẩn |
| 7. Làm ranking | Lọc điều kiện cứng rồi xếp hạng sở thích mềm theo quy tắc cố định | Tránh trả kết quả vi phạm điều kiện và giúp giải thích gợi ý | Top sản phẩm ổn định cho cùng đầu vào |
| 8. Thêm Agent | Gửi yêu cầu đã xác thực cho Ollama; giới hạn tool bằng registry/schema | Agent diễn đạt tự nhiên nhưng không thay nghiệp vụ | Agent gọi đúng công cụ và tổng hợp dựa trên dữ liệu |
| 9. Làm giao diện chat | Kết nối API, cô lập state theo phiên và hiển thị product cards | Giúp người dùng xem kết quả thuận tiện, không lẫn hội thoại | Demo được toàn bộ luồng từ câu hỏi đến gợi ý |
| 10. Xử lý lỗi và đánh giá | Bao phủ dữ liệu sai, không có kết quả, tool sai, Ollama lỗi; đo intent/slot và tuân thủ lọc | Phân biệt lỗi NLP, dữ liệu và diễn đạt của LLM | Bộ câu hỏi đánh giá độc lập, tiêu chí đạt và ví dụ lỗi |

### Thứ tự làm khuyến nghị

Hoàn thành bước 1–6 và xác nhận kết quả catalog/NLP trước khi tích hợp Ollama. Nếu bắt đầu bằng prompt/Agent trước, rất khó phân biệt lỗi do model hiểu sai hay do truy vấn dữ liệu sai.

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

- Giá trong CSV chỉ phản ánh dữ liệu được cung cấp; chưa có cơ chế đồng bộ giá trực tuyến.
- Tag là nhãn của bộ dữ liệu; chất lượng gợi ý phụ thuộc tag được gán chính xác.
- Chip CPU đang là chuỗi mô tả. Muốn xếp hạng hiệu năng chip đáng tin cậy cần bổ sung dữ liệu chuẩn hóa hoặc benchmark có nguồn.
- Chưa có lịch sử mua hàng, tồn kho, màu sắc, cửa hàng hoặc chính sách bảo hành.
- Chỉ thêm RAG khi có kho tài liệu dạng văn bản cần tìm kiếm; không thêm vector database chỉ để truy vấn CSV.
- Khi đồ án cần mở rộng, có thể thêm đánh giá chất lượng gợi ý, nhập bộ dữ liệu mới, hoặc thay CSV bằng cơ sở dữ liệu mà vẫn giữ giao diện catalog service.

---

## 13. Kết luận

Kiến trúc phù hợp nhất với phạm vi hiện tại là **Flask + NLP tiếng Việt dạng kết hợp + Ollama Agent gọi công cụ + catalog CSV truy vấn xác định**. NLP hiểu câu hỏi, Agent điều phối hội thoại, còn catalog chịu trách nhiệm tìm và xếp hạng. Cách phân chia này dễ làm theo từng bước, dễ giải thích trong môn Xử lý ngôn ngữ tự nhiên và tránh để LLM tự bịa thông tin sản phẩm.

