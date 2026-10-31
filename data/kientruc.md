# KIẾN TRÚC VÀ HƯỚNG DẪN THỰC HIỆN CHATBOT TƯ VẤN ĐIỆN THOẠI

> **Phạm vi:** chatbot tiếng Việt giúp người dùng tìm và gợi ý điện thoại từ CSV bằng Flask, NLP và AI Agent chạy qua Ollama.
>
> **Không nằm trong phiên bản này:** chính sách bảo hành, kiểm tra tồn kho, cập nhật giá trực tuyến, đặt hàng/thanh toán và tư vấn dựa trên tài liệu dài.

---

## 1. Tóm tắt quyết định kiến trúc

Đề xuất làm một **ứng dụng Flask dạng modular monolith**: một ứng dụng chạy trên máy, bên trong chia thành các module có trách nhiệm riêng.

- Dùng **CSV làm nguồn dữ liệu sản phẩm**. Tìm kiếm, lọc và xếp hạng được thực hiện bằng Python/Pandas theo điều kiện xác định.
- Dùng **NLP** để chuẩn hóa tiếng Việt, nhận diện ý định, hãng, ngân sách và nhu cầu.
- Dùng **AI Agent qua Ollama** để xử lý hội thoại, chọn công cụ được phép và diễn đạt kết quả.
- Chỉ cho Agent gọi một danh sách công cụ đọc dữ liệu đã định nghĩa trước.
- Chưa dùng RAG, embedding hoặc vector database: dữ liệu hiện tại là bảng thuộc tính, không phải kho tài liệu văn bản dài.
- Giao diện nhận câu hỏi và hiển thị tối đa ba gợi ý kèm thông số, lý do gợi ý, ảnh và liên kết sản phẩm nếu các trường đó có dữ liệu.

### Vì sao chọn cách này?

Danh mục hiện có 162 dòng và 17 cột như hãng, giá, RAM, ROM, pin, màn hình, camera và tags nhu cầu. Các câu hỏi thường cần lọc chính xác, ví dụ “Xiaomi dưới 15 triệu”, nên truy vấn cấu trúc dễ kiểm soát và dễ giải thích hơn tìm kiếm vector. LLM phù hợp để hiểu cách diễn đạt và trình bày câu trả lời; các phép lọc và dữ liệu thực tế nên do chương trình xử lý.

---

## 2. Sơ đồ thành phần và luồng dữ liệu

~~~mermaid
flowchart TD
    User[Người dùng] <--> UI[Giao diện chat]
    UI <--> Flask[Flask Web/API]
    Flask --> State[Ngữ cảnh hội thoại]
    Flask --> NLP[NLP tiếng Việt]
    NLP --> Parsed[Yêu cầu đã chuẩn hóa]
    Parsed --> Agent[Agent điều phối Ollama]
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
| Agent | Điều phối hội thoại, chọn công cụ, tóm tắt kết quả | LLM diễn giải yêu cầu tự nhiên nhưng không làm nguồn dữ liệu |
| Công cụ | Xác thực tham số và gọi chức năng nghiệp vụ | Chặn gọi hàm ngoài phạm vi, giữ hợp đồng đầu vào rõ ràng |
| Dịch vụ danh mục | Lọc, so sánh và xếp hạng điện thoại | Kết quả cần ổn định, đúng theo CSV và có thể kiểm thử độc lập |
| CSV | Nguồn thông tin sản phẩm tại thời điểm chuẩn bị dữ liệu | Đơn giản, phù hợp quy mô hiện tại, dễ trình bày và kiểm tra |

---

## 3. Cấu trúc thư mục đề xuất

Đây là cấu trúc mục tiêu cho đồ án; có thể tạo dần theo các bước ở mục 10, không cần tạo tất cả thư mục trống từ đầu.

~~~text
E:\NLP/
├── data/
│   └── dien_thoai_chuan_hoa.csv
├── docs/
│   └── kientruc.md
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
- **docs/**: tài liệu kiến trúc và hướng dẫn đồ án.

Không cần tách thành nhiều dịch vụ/microservice. Với một CSV nhỏ và một máy chạy local, cách đó tăng cấu hình phải quản lý mà chưa đem lại lợi ích thiết thực.

---

## 4. Thiết kế phần NLP tiếng Việt

### 4.1. NLP cần tạo ra gì?

Đầu vào là câu nói tự nhiên. Đầu ra là một yêu cầu có cấu trúc để Agent và bộ tìm kiếm cùng hiểu.

Ví dụ đầu vào:

> “Tìm giúp mình Xiaomi chơi game, pin trâu, dưới 15 củ.”

Kết quả NLP mong muốn:

~~~json
{
  "intent": "recommend",
  "constraints": {
    "brand": "Xiaomi",
    "max_price_vnd": 15000000
  },
  "preferences": ["choi_game", "pin_trau"],
  "excluded_brands": []
}
~~~

Câu hỏi khác nhau nhưng cùng ý nghĩa nên tạo ra yêu cầu gần tương đương. Ví dụ “15 củ”, “15tr” và “15 triệu” đều được chuẩn hóa về 15.000.000 đồng.

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

| Ý định | Ví dụ |
|---|---|
| recommend | “Gợi ý điện thoại chụp ảnh đẹp dưới 20 triệu” |
| search | “Có máy Samsung RAM 8GB không?” |
| detail | “Cho mình thông tin Xiaomi POCO X8 Pro” |
| compare | “So sánh iPhone 17 với Samsung Galaxy S25” |
| greeting/other | “Xin chào”, câu hỏi ngoài phạm vi |

Bắt đầu bằng luật và từ khóa rõ ràng vì dễ giải thích, không cần dữ liệu huấn luyện ban đầu. Nếu muốn thử mô hình phân loại trong môn học, có thể tạo tập câu hỏi riêng, gán nhãn ý định rồi so sánh với baseline luật. **CSV sản phẩm không phải tập dữ liệu câu hỏi đã gán nhãn**, nên không thể dùng trực tiếp CSV để huấn luyện intent classifier.

#### Bước C — Trích xuất thực thể và điều kiện

Các trường nên nhận diện:

- **Hãng**: Apple, Samsung, Xiaomi, OPPO, vivo, realme, HONOR, Tecno, Motorola, Nothing Phone, Nubia.
- **Model**: đối chiếu tên máy trong CSV, hỗ trợ tên gọi rút gọn nếu xác định được duy nhất.
- **Ngân sách**: giá tối đa, giá tối thiểu hoặc khoảng giá.
- **Thông số tối thiểu**: RAM, ROM, pin, tần số quét nếu người dùng nêu rõ.
- **Nhu cầu**: chơi game, pin trâu, chụp ảnh đẹp, selfie, sạc nhanh, màn hình mượt, 5G...
- **Điều kiện loại trừ**: “không lấy Samsung”, “không cần máy gập”.
- **Mức ưu tiên**: “ưu tiên pin”, “quan trọng nhất là camera”.

Ví dụ:

~~~text
“Máy khoảng 10 đến 15 triệu, không phải iPhone, ưu tiên pin”
→ intent: recommend
→ min_price_vnd: 10000000
→ max_price_vnd: 15000000
→ excluded_brands: [Apple]
→ preferences: [pin_trau]
→ priority: [pin_trau]
~~~

Với giá tiền, cần nhận biết quan hệ:

- “dưới 15 triệu”, “tối đa 15 triệu” → giá tối đa.
- “trên 10 triệu” → giá tối thiểu.
- “từ 10 đến 15 triệu” → khoảng giá.
- “khoảng 15 triệu” → khoảng giá mềm; nên hỏi lại nếu chưa thống nhất độ rộng khoảng hoặc dùng mức mặc định được ghi rõ trong tài liệu.

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
| máy gập | thiet_ke_gap |

Một câu có thể tạo ra nhiều tag. Không nên coi “pin trâu” và “pin khủng” là hai từ giống hệt nhau nếu dữ liệu phân biệt chúng; có thể ánh xạ cả hai, hoặc dùng một tag làm ưu tiên và một tiêu chí xếp hạng theo pin_mah.

#### Bước E — Xử lý phủ định và câu mơ hồ

- “Không muốn Apple” phải đưa Apple vào danh sách loại trừ.
- “Không cần chơi game” không được hiểu thành nhu cầu chơi game.
- Nếu người dùng vừa nói “dưới 10 triệu” vừa nói “tối thiểu 15 triệu”, điều kiện mâu thuẫn; hỏi lại thay vì trả kết quả sai.
- Nếu tên model khớp nhiều sản phẩm, hỏi thêm phiên bản dung lượng hoặc đưa các lựa chọn để người dùng chọn.
- Nếu không có ngân sách hay nhu cầu nào, hỏi một câu ngắn như “Bạn dự kiến chi khoảng bao nhiêu?” hoặc đề nghị người dùng chọn ưu tiên.

#### Bước F — Dùng LLM ở chỗ cần thiết

Có thể để Qwen hỗ trợ hiểu câu diễn đạt khó hoặc câu nối tiếp, nhưng:

1. Đưa cho Agent câu gốc cùng kết quả NLP ban đầu.
2. Yêu cầu Agent chỉ dùng các trường đã định nghĩa, không tự thêm hãng/tag lạ.
3. Kiểm tra kết quả bằng schema trước khi truy vấn.
4. Nếu Agent không chắc hoặc điều kiện mâu thuẫn, hỏi người dùng.
5. Bộ catalog vẫn là nơi quyết định sản phẩm nào phù hợp.

**Lý do dùng cách kết hợp:** luật và từ điển cho kết quả minh bạch với miền dữ liệu nhỏ; LLM xử lý cách nói đa dạng; kiểm tra schema giúp hạn chế đầu ra tùy tiện. Không nên giao toàn bộ việc tính ngân sách và lọc sản phẩm cho LLM.

### 4.3. Có nên dùng Underthesea?

Có thể dùng Underthesea để thử tách từ hoặc hỗ trợ phân tích tiếng Việt, nhưng nó không thay thế từ điển hãng/tag, nhận dạng tiền và kiểm tra điều kiện. Với bộ dữ liệu hiện tại, normalization, alias và slot extraction quan trọng hơn việc xây dựng pipeline NLP nặng.

---

## 5. Dịch vụ dữ liệu sản phẩm

### 5.1. Nạp và kiểm tra CSV

Khi ứng dụng khởi động:

1. Đọc CSV từ cấu hình đường dẫn.
2. Kiểm tra các cột bắt buộc như id, ten_san_pham, hang, gia_ban, ram_gb, pin_mah và tags_nhu_cau.
3. Chuyển trường số sang kiểu số; báo lỗi rõ nếu giá hoặc thông số không thể chuyển đổi.
4. Tách tags_nhu_cau theo dấu phẩy thành tập tag, sau khi bỏ khoảng trắng.
5. Chuẩn hóa hãng để so khớp không phân biệt hoa thường.
6. Giữ id làm khóa sản phẩm; giữ hinh_anh và url cho thẻ kết quả.
7. Nạp dữ liệu một lần và dùng lại trong các truy vấn.

**Vì sao không đọc CSV lại ở mỗi câu hỏi?** Danh mục nhỏ có thể giữ trong bộ nhớ của ứng dụng. Nạp một lần giảm thao tác I/O, tránh lặp mã và giúp hiệu năng ổn định hơn. Khi CSV được cập nhật trong lúc phát triển, có thể khởi động lại ứng dụng để nạp lại.

### 5.2. Truy vấn theo điều kiện

Áp dụng điều kiện cứng trước:

- hãng được yêu cầu;
- giá tối đa/tối thiểu;
- RAM/ROM/pin tối thiểu;
- hãng hoặc model bị loại trừ.

Sau đó mới xếp hạng theo sở thích mềm như tag chơi game, pin trâu hoặc chụp ảnh đẹp.

Tag cần so khớp theo phần tử chính xác sau khi tách chuỗi, không tìm bằng cách kiểm tra chuỗi con. Ví dụ tag choi_game không nên bị khớp nhầm với một chuỗi có ký tự tương tự nhưng khác tag.

### 5.3. Xếp hạng gợi ý

Quy tắc gợi ý ban đầu nên đơn giản và giải thích được:

1. Không được bỏ qua điều kiện cứng để đưa máy “gần đúng”.
2. Ưu tiên máy khớp nhiều nhu cầu mềm người dùng đã nói.
3. Khi người dùng nói rõ ưu tiên, xếp tiêu chí đó trước. Ví dụ ưu tiên pin thì trong nhóm phù hợp, so pin_mah.
4. Nếu các máy ngang nhau, dùng thông số có sẵn liên quan đến nhu cầu để phân định: pin_mah cho pin, ram_gb cho đa nhiệm/game, tan_so_quet_hz cho màn hình mượt, camera MP/tag camera cho nhu cầu chụp ảnh.
5. Nếu vẫn ngang nhau, ưu tiên giá thấp hơn để đưa lựa chọn dễ tiếp cận lên trước.
6. Trả tối đa ba kết quả mặc định; không có kết quả thì nói rõ và hỏi người dùng có muốn nới điều kiện nào không.

Không nên tự đánh giá chip chỉ từ tên chuỗi chip_cpu nếu chưa có bảng xếp hạng/benchmark đáng tin cậy. Có thể dùng tag chip_gaming như một tín hiệu có sẵn, nhưng phải phân biệt tag này với kết luận benchmark.

### Ví dụ truy vấn sản phẩm

Câu hỏi:

> “Tìm giúp mình Xiaomi chơi game, pin trâu, dưới 15 củ.”

Điều kiện cứng:

~~~text
hang = Xiaomi
gia_ban <= 15.000.000
~~~

Nhu cầu mềm:

~~~text
choi_game
pin_trau
~~~

Một số dòng trong CSV khớp các điều kiện này:

| Sản phẩm | Giá trong CSV | RAM | Pin | Dấu hiệu liên quan |
|---|---:|---:|---:|---|
| Xiaomi Redmi Note 17 Pro Max 8GB/256GB | 14.190.000đ | 8GB | 10.000mAh | choi_game, pin_trau |
| Xiaomi POCO X8 Pro 5G 8GB/256GB | 12.990.000đ | 8GB | 6.500mAh | choi_game, pin_trau, chip_gaming |
| Xiaomi Redmi Note 15 Pro 5G 8GB/256GB | 8.290.000đ | 8GB | 6.580mAh | choi_game, pin_trau, chip_gaming |

Câu trả lời nên nêu rõ sự đánh đổi, ví dụ: máy có pin lớn nhất, máy có tag chip_gaming, và lựa chọn giá thấp hơn. Không nên khẳng định một máy “chơi game tốt nhất” chỉ từ tên chip hoặc suy đoán ngoài CSV.

---

## 6. Công cụ Agent được phép gọi

Giữ số công cụ ít và mỗi công cụ có một trách nhiệm rõ:

### 6.1. recommend_phones

Dùng khi khách cần gợi ý theo hãng, ngân sách, cấu hình hoặc nhu cầu.

Đầu vào dự kiến:

~~~text
brand, min_price_vnd, max_price_vnd, min_ram_gb,
min_rom_gb, min_battery_mah, needs, excluded_brands, limit
~~~

Đầu ra: danh sách sản phẩm phù hợp, lý do khớp, những tiêu chí chưa khớp và các trường dùng để tạo thẻ sản phẩm.

### 6.2. get_phone_detail

Dùng khi khách hỏi thông tin một mẫu cụ thể. Ưu tiên tìm theo id hoặc tên khớp rõ ràng. Nếu có nhiều phiên bản tên gần giống nhau, trả các lựa chọn hoặc hỏi lại, không tự chọn phiên bản.

### 6.3. compare_phones

Dùng để so sánh hai hoặc một số ít sản phẩm theo trường có trong CSV. Chỉ so sánh giá, RAM, ROM, pin, màn hình, camera và tags hiện có; không tạo kết luận không có dữ liệu hỗ trợ.

### Quy trình an toàn cho một lần gọi tool

1. Ollama đề nghị tên tool và đối số.
2. Tool registry kiểm tra tên hàm có trong danh sách cho phép hay không.
3. Schema kiểm tra kiểu dữ liệu, khoảng giá, danh sách tag và số lượng sản phẩm yêu cầu.
4. Catalog chạy truy vấn chỉ đọc.
5. Kết quả được trả về Agent dưới dạng dữ liệu có cấu trúc.
6. Agent viết câu trả lời dựa trên kết quả đó.

Giới hạn tối đa hai lần gọi tool trong một lượt hội thoại. Nếu lời gọi lỗi hoặc model lặp lại, dừng vòng lặp và trả thông báo phù hợp. CSV chỉ được đọc; không cung cấp tool sửa, xóa hoặc ghi đè dữ liệu.

---

## 7. Ví dụ hội thoại từ đầu đến cuối

### Trường hợp 1 — Câu hỏi đủ thông tin

**Người dùng:** “Tìm giúp mình Xiaomi chơi game, pin trâu, dưới 15 củ.”

**NLP:** nhận diện intent recommend, hãng Xiaomi, giá tối đa 15.000.000đ và hai tag choi_game/pin_trau.

**Agent:** gọi recommend_phones với các điều kiện đã xác thực.

**Catalog:** lọc theo hãng và giá; giữ sản phẩm khớp tag; xếp hạng theo nhu cầu.

**Agent trả lời:** đưa tối đa ba sản phẩm, mỗi sản phẩm có giá theo CSV, RAM, pin và lý do được chọn. Ghi chú giá là theo dữ liệu trong bộ CSV, không gọi là giá trực tuyến hiện tại.

### Trường hợp 2 — Thiếu ngân sách

**Người dùng:** “Mình muốn máy chụp ảnh đẹp.”

**NLP:** intent recommend, preferences chup_anh_dep; chưa có ngân sách.

**Ứng xử:** nếu có nhiều sản phẩm, hỏi “Bạn muốn chi tối đa khoảng bao nhiêu?” Nếu đồ án chọn chế độ gợi ý ngay, cần ghi rõ đây là danh sách chưa lọc theo ngân sách.

### Trường hợp 3 — Câu tiếp nối

**Người dùng:** “Tìm Samsung dưới 15 triệu.”
**Người dùng:** “Ưu tiên pin trâu nhé.”

**Ngữ cảnh hội thoại:** giữ hãng Samsung và giá tối đa từ lượt trước; thêm tag pin_trau ở lượt sau. Chỉ lưu các điều kiện cần cho phiên chat, không cần xây dựng bộ nhớ dài hạn cho phiên bản đồ án đầu tiên.

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

---

## 9. Cấu hình và giới hạn phần cứng

Tài liệu ban đầu nêu máy có Intel Core Ultra 7, RTX 3050 Ti Laptop 4GB VRAM, 16GB RAM, Ollama và các model Qwen cài sẵn. Đây là bối cảnh triển khai local; không nên xem các con số tốc độ hoặc mức VRAM ước tính là cam kết.

- Đọc tên model, đường dẫn dữ liệu và cấu hình máy chủ từ cấu hình ứng dụng thay vì rải giá trị cố định trong mã.
- Đo thời gian khởi động, thời gian phản hồi, mức RAM/VRAM và tốc độ sinh token trên chính máy chạy đồ án.
- Kết quả phụ thuộc phiên bản model, lượng ngữ cảnh, quantization, tiến trình khác đang chạy và mức GPU offload của Ollama.
- Nếu model 3B thiếu bộ nhớ hoặc phản hồi chậm, thử cấu hình/model nhẹ hơn đã cài; ghi lại phép đo thay vì cam kết một con số chung.
- Nếu Ollama tắt hoặc model chưa sẵn sàng, Flask cần báo bot tạm thời không kết nối được, không làm ứng dụng treo vô hạn.

Không khẳng định chatbot luôn trả lời dưới một giây, toàn bộ model luôn nằm trong VRAM, hay dùng CPU dưới một tỷ lệ cố định trước khi đo thực tế.

---

## 10. Các bước thực hiện theo thứ tự

| Bước | Cách làm | Vì sao | Kết quả cần có |
|---|---|---|---|
| 1. Chốt phạm vi | Chỉ hỗ trợ gợi ý, tìm, xem chi tiết và so sánh điện thoại từ CSV | Tránh đề tài lan sang bán hàng, bảo hành hoặc tồn kho khi dữ liệu chưa có | Danh sách intent và chức năng được thống nhất |
| 2. Kiểm tra dữ liệu | Đọc header, kiểu dữ liệu, tag, dòng trống, id trùng và liên kết ảnh/URL | Công cụ không thể tư vấn đúng nếu dữ liệu đầu vào sai | Bảng mô tả cột và các vấn đề dữ liệu |
| 3. Tạo khung ứng dụng | Tạo Flask entry point, cấu hình và module web/NLP/agent/catalog | Phân tách trách nhiệm giúp debug và trình bày đồ án rõ hơn | Ứng dụng chạy được với route cơ bản |
| 4. Làm catalog trước | Nạp CSV một lần, xác thực cột, viết lọc hãng/giá/thông số/tag | Có thể kiểm tra độ đúng của tìm kiếm độc lập với LLM | Truy vấn cho kết quả xác định |
| 5. Làm NLP baseline | Viết normalize, từ điển alias, intent và slot extraction theo ví dụ | Tạo thành phần NLP có thể giải thích, không phụ thuộc hoàn toàn vào prompt | Câu tự nhiên được chuyển thành cấu trúc chuẩn |
| 6. Làm ranking | Lọc điều kiện cứng rồi xếp hạng nhu cầu mềm, tạo lý do khớp | Tránh trả kết quả vi phạm ngân sách và giúp giải thích gợi ý | Top sản phẩm ổn định cho cùng đầu vào |
| 7. Thêm Agent | Gửi câu hỏi và cấu trúc NLP cho Ollama; giới hạn tool bằng registry/schema | Agent tạo hội thoại tự nhiên nhưng chỉ thao tác trong miền nghiệp vụ | Agent gọi đúng công cụ và tổng hợp dựa trên dữ liệu |
| 8. Làm giao diện chat | Kết nối route Flask, hiển thị lịch sử và product cards | Giúp người dùng xem, so sánh kết quả thuận tiện | Demo được toàn bộ luồng từ câu hỏi đến gợi ý |
| 9. Xử lý lỗi | Bao phủ CSV sai, không có kết quả, tham số tool sai, Ollama mất kết nối | Đồ án cần phản hồi rõ thay vì lỗi traceback cho người dùng | Mỗi lỗi có thông báo dễ hiểu |
| 10. Đánh giá NLP và tư vấn | Tạo câu hỏi mẫu có nhãn intent/slots; đánh giá slot, điều kiện lọc và chất lượng top 3 | Phân biệt lỗi NLP, lỗi dữ liệu và lỗi diễn đạt của LLM | Có bảng kết quả và ví dụ lỗi được sửa |

### Thứ tự làm khuyến nghị

Hoàn thành bước 1–6 và xác nhận kết quả catalog/NLP trước khi tích hợp Ollama. Nếu bắt đầu bằng prompt/Agent trước, rất khó phân biệt lỗi do model hiểu sai hay do truy vấn dữ liệu sai.

---

## 11. Kịch bản kiểm tra và tiêu chí đạt

Nên chuẩn bị câu hỏi tiếng Việt có dấu/không dấu, tiếng lóng, câu hỏi thiếu dữ kiện và câu tiếp nối. Các kiểm tra chính:

1. “Xiaomi chơi game dưới 15 triệu” chỉ trả Xiaomi có giá không vượt ngân sách và khớp nhu cầu.
2. “Pin trâu” được ánh xạ đúng tag; kết quả dùng pin_mah để giải thích/xếp hạng khi thích hợp.
3. “Không lấy Apple” loại Apple khỏi kết quả.
4. “Từ 10 đến 15 triệu” không bị hiểu thành chỉ giá tối đa 10 triệu.
5. Câu có hai điều kiện giá mâu thuẫn thì bot hỏi lại.
6. Model có nhiều phiên bản thì không tự chọn sai ROM.
7. Không tìm thấy kết quả thì bot báo rõ, không tự nới điều kiện cứng.
8. Agent không tự tạo giá, chip, tồn kho hoặc chính sách không có trong dữ liệu.
9. Lời gọi tool sai schema hoặc ngoài whitelist không được thực thi.
10. Khi Ollama không kết nối, giao diện nhận thông báo có kiểm soát.

Nếu đánh giá theo môn NLP, có thể lập tập câu hỏi gán nhãn intent và slots, tách một phần để đánh giá riêng. Báo cáo tối thiểu: độ đúng intent, độ đúng các slot quan trọng (hãng/giá/nhu cầu), tỷ lệ kết quả đáp ứng điều kiện cứng và một số lỗi tiêu biểu. Không dùng câu đã phát triển luật làm toàn bộ tập đánh giá.

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

