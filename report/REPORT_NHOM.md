# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** K4-DAY07-3B
**Thành viên:** Đinh Kim Thái, Nguyễn Lê Phước Tiến, Phạm Văn Kiên, Vũ Huy Đô
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách đổi trả, hoàn tiền và bảo hành trên sàn Thương mại Điện tử.

**Tại sao nhóm chọn chủ đề này?**
> Đây là mảng quy định phức tạp và quan trọng nhất, liên quan trực tiếp đến quyền lợi người mua, nghĩa vụ người bán và chi phí hoàn cước vận chuyển.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Phương thức và thời gian nhận tiền hoàn | https://help.shopee.vn/portal/4/article/189473 | 2026-09-20 / not-stated | 1242 | `doc_id`: refund-methods-and-time, `audience`: buyer, `category`: refund-timing, `language`: vi |
| 2 | Điều kiện yêu cầu trả hàng hoặc hoàn tiền trên Shopee | https://help.shopee.vn/portal/4/article/188931 | 2026-09-20 / not-stated | 1275 | `doc_id`: return-eligibility, `audience`: buyer, `category`: eligibility, `language`: vi |
| 3 | Bằng chứng cho yêu cầu trả hàng hoàn tiền | https://help.shopee.vn/portal/4/article/79467 | 2026-09-20 / not-stated | 1150 | `doc_id`: return-evidence, `audience`: buyer, `category`: evidence, `language`: vi |
| 4 | Đóng gói và gửi trả sản phẩm | https://help.shopee.vn/portal/4/article/79508 | 2026-09-20 / not-stated | 1060 | `doc_id`: return-shipping-and-packaging, `audience`: buyer, `category`: return-shipping, `language`: vi |
| 5 | Nghĩa vụ của người bán trong trả hàng hoàn tiền | https://help.shopee.vn/portal/4/article/77251 | 2026-09-20 / not-stated | 1281 | `doc_id`: seller-return-refund-obligations, `audience`: seller, `category`: seller-obligations, `language`: vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | `str` | `return-eligibility` | Định danh duy nhất để xóa hoặc truy vết chính xác tài liệu nguồn. |
| `audience` | `str` | `buyer` / `seller` | Lọc (pre-filter) tài liệu dành riêng cho Người mua hoặc Người bán trước khi tìm kiếm vector. |
| `category` | `str` | `refund-timing` / `eligibility` | Gom nhóm chủ đề giúp thu hẹp không gian tìm kiếm, tránh nhiễu dữ liệu giữa các loại chính sách. |
| `source_url` | `str` | `https://help.shopee.vn/portal/4/article/...` | Đảm bảo minh bạch nguồn gốc dữ liệu (provenance) và trích dẫn câu trả lời. |
| `retrieved_at` | `str` | `2026-09-20` | Kiểm soát tính mới và hiệu lực thời gian của dữ liệu chính sách. |
| `document_version` | `str` | `not-stated` | Theo dõi phiên bản chính sách, tránh sử dụng quy định cũ đã hết hiệu lực. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên tài liệu mẫu `return-eligibility.md` (`chunk_size=200`):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `return-eligibility.md` | FixedSizeChunker (`fixed_size`) | 10 | 198.9 ký tự | Trung bình (bị cắt ngang câu ở ranh giới window) |
| `return-eligibility.md` | SentenceChunker (`by_sentences`) | 3 | 511.0 ký tự | Khá (giữ trọn câu nhưng gộp nhiều câu khiến chunk dài vượt mốc 200 ký tự) |
| `return-eligibility.md` | RecursiveChunker (`recursive`) | 14 | 108.1 ký tự | Rất tốt (ưu tiên tách theo phân cấp `#`, `##`, `\n\n`, giữ trọn vẹn ngữ nghĩa từng ý) |

### Chiến lược của từng thành viên

**Thành viên 1 — Đinh Kim Thái (Nhiệm vụ: Data — Clean documents and complete metadata)**
- **Loại chiến lược:** `RecursiveChunker` (`recursive`, `chunk_size=300`)
- **Mô tả & lý do chọn cho chủ đề này:** Phụ trách thu thập, làm sạch dữ liệu và gán metadata. Thử nghiệm chiến lược đệ quy cắt theo phân cấp tiêu đề Markdown (`#`, `##`, `\n\n`) nhằm bảo toàn trọn vẹn từng điều khoản quy định.

**Thành viên 2 — Nguyễn Lê Phước Tiến (Nhiệm vụ: Code — Implement chunking and vector store)**
- **Loại chiến lược:** `FixedSizeChunker` (`fixed_size`, `chunk_size=200`, `overlap=50`)
- **Mô tả & lý do chọn:** Phụ trách lập trình bộ mã nguồn `src/`. Thử nghiệm chiến lược cắt cố định độ dài ký tự kèm cửa sổ trượt overlap 50 ký tự để so sánh đường cơ sở.

**Thành viên 3 — Phạm Văn Kiên (Nhiệm vụ: Strategy — Draft 5 queries and gold answers)**
- **Loại chiến lược:** `SentenceChunker` (`by_sentences`, `max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Phụ trách soạn thảo bộ 5 câu hỏi benchmark kèm đáp án chuẩn. Thử nghiệm chiến lược cắt theo câu để đảm bảo ngữ cảnh nguyên vẹn cho từng câu trả lời.

**Thành viên 4 — Vũ Huy Đô (Nhiệm vụ: Benchmark — Run comparison and note failure case)**
- **Loại chiến lược:** `RecursiveChunker` tùy chỉnh phân đoạn theo Tiêu đề (`heading_chunker`)
- **Mô tả & lý do chọn:** Phụ trách chạy đánh giá so sánh giữa các chiến lược và phân tích các trường hợp thất bại (failure cases) khi truy xuất không có metadata filter.

### So Sánh Giữa Các Thành Viên

| Thành viên | Nhiệm vụ | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|---|----------|----------------------|-----------|----------|
| Đinh Kim Thái | Data | RecursiveChunker | 10 / 10 | Giữ nguyên cấu trúc điều khoản chính sách xuất sắc | Tốn thêm bước đệ quy tính toán |
| Nguyễn Lê Phước Tiến | Code | FixedSizeChunker | 8 / 10 | Tốc độ xử lý vector cực nhanh, kích thước đều | Dễ bị cắt ngang câu/từ ở ranh giới window |
| Phạm Văn Kiên | Strategy | SentenceChunker | 9 / 10 | Đảm bảo mỗi chunk là các câu văn trọn vẹn | Đứt đoạn liên kết giữa các mục lớn |
| Vũ Huy Đô | Benchmark | Custom Heading Chunker | 10 / 10 | Độ chính xác truy xuất tiêu đề rất cao | Cần định dạng Markdown chuẩn |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> `RecursiveChunker` là chiến lược tốt nhất cho chủ đề văn bản chính sách. Bởi vì các tài liệu điều khoản được trình bày theo cấu trúc phân mục (`#`, `##`, dòng trống `\n\n`), `RecursiveChunker` ưu tiên tách theo đoạn văn giúp giữ trọn vẹn từng điều khoản quy định nằm gọn trong một chunk duy nhất mà không bị xé lẻ.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn nhận tiền hoàn về ví ShopeePay và thẻ tín dụng/ghi nợ quy định bao lâu? *(Lọc `audience: buyer`)* | Ví ShopeePay thường trong **24 giờ** (khi ví hoạt động bình thường). Thẻ tín dụng/ghi nợ (gồm Apple Pay/Google Pay) mất **7–14 ngày làm việc** tùy ngân hàng phát hành. | `refund-methods-and-time.md` |
| 2 | Shopee có hỗ trợ đổi trực tiếp sang sản phẩm khác không và xử lý thế nào khi hàng nhận có vấn đề? *(Lọc `audience: buyer`)* | Shopee **không hỗ trợ** đổi trực tiếp sang sản phẩm khác mà chỉ xử lý **Trả hàng/Hoàn tiền**. Người mua có thể từ chối nhận tại bước đồng kiểm hoặc tạo yêu cầu sau khi nhận. | `return-eligibility.md` |
| 3 | Khi nghi ngờ hàng không chính hãng (hàng giả/nhái), người mua cần cung cấp bằng chứng gì? *(Lọc `audience: buyer`)* | Quá trình quét mã QR, kiểm tra số seri trên kênh của hãng, sự khác biệt giữa bao bì thực nhận và chính hãng, cùng video mở hộp liên tục từ trước khi mở đến khi kiểm tra sản phẩm. | `return-evidence.md` |
| 4 | Người mua có được viết hoặc dán trực tiếp thông tin vận chuyển lên hộp của nhà sản xuất khi gửi trả không? *(Lọc `audience: buyer`)* | **Không được** viết hoặc dán trực tiếp lên hộp nguyên bản của nhà sản xuất. Phải bọc kiện bằng hộp carton/bao bì ngoài và dán phiếu gửi hàng hoặc mã vận đơn lên lớp bao bì ngoài đó. | `return-shipping-and-packaging.md` |
| 5 | Nếu người mua khiếu nại người bán hoàn dưới 50% giá trị sản phẩm hoàn trả thì Shopee xử lý thế nào? *(Lọc `audience: seller`)* | Shopee có thể **cấn trừ phần chênh lệch trực tiếp từ Số dư Tài khoản Shopee của người bán** để thanh toán cho người mua mà **không cần thêm chấp thuận**. | `seller-return-refund-obligations.md` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn hoàn tiền ví ShopeePay/thẻ | RecursiveChunker | Có (Top-1) | Đạt 2/2 điểm khi dùng `metadata_filter={"audience": "buyer"}` |
| 2 | Đổi hàng trực tiếp & từ chối nhận | RecursiveChunker | Có (Top-1) | Đạt 2/2 điểm khi dùng `metadata_filter={"audience": "buyer"}` |
| 3 | Bằng chứng nghi ngờ hàng giả/nhái | SentenceChunker | Có (Top-1) | Đạt 2/2 điểm |
| 4 | Quy định đóng gói gửi trả hàng | RecursiveChunker | Có (Top-1) | Đạt 2/2 điểm |
| 5 | Xử lý người bán hoàn dưới 50% | RecursiveChunker | Có (Top-1) | Đạt 2/2 điểm khi dùng `metadata_filter={"audience": "seller"}` |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata cực kỳ hữu ích ở Câu 1, Câu 2 và Câu 5. Nếu không lọc theo `audience` (`buyer` vs `seller`), câu hỏi về nghĩa vụ hoàn tiền của người bán (Câu 5) có thể trả về các văn bản hướng dẫn nhận tiền hoàn của người mua (Câu 1) do cùng chứa các từ khóa "hoàn tiền", "sản phẩm". Nhờ pre-filtering theo `audience`, độ chính xác (Precision) của top-1 đạt 100%.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. **Cấu trúc dữ liệu quyết định chiến lược Chunking**: Với dữ liệu dạng chính sách/luật có định dạng Markdown, `RecursiveChunker` là lựa chọn tối ưu vượt trội so với `FixedSizeChunker`.
2. **Metadata Filtering là chìa khóa chống nhiễu RAG**: Lọc trước theo `audience` giúp loại bỏ triệt để việc nhầm lẫn giữa quy định cho Người mua và Người bán.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một tập dữ liệu nhưng các chiến lược chunking khác nhau tạo ra sự chênh lệch rõ rệt về ngữ cảnh. Cắt quá nhỏ làm mất mối liên hệ giữa các câu, cắt quá to gây nhiễu embedding. Chiến lược cắt đệ quy theo phân cấp Markdown mang lại sự cân bằng hoàn hảo nhất.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ bổ sung thêm các trường metadata chi tiết hơn như `product_type` (điện tử, thời trang) và áp dụng kỹ thuật Hybrid Search (kết hợp BM25 từ khóa + Vector Search) để tối ưu kết quả cho các câu hỏi chứa con số mốc thời gian cụ thể.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |

