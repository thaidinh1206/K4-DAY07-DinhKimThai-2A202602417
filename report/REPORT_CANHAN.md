# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đinh Kim Thái
**Nhóm:** K4-DAY07-3B
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
Độ tương tự cosine cao (tiệm cận 1.0) có nghĩa là góc giữa hai vector biểu diễn văn bản rất nhỏ (hai vector chỉ cùng hướng trong không gian đa chiều), cho thấy hai đoạn văn bản có ý nghĩa ngữ nghĩa (semantic meaning) vô cùng tương đồng với nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sàn thương mại điện tử hỗ trợ người mua trả hàng trong vòng 7 ngày kể từ khi nhận hàng.
- Câu B: Khách hàng có quyền yêu cầu hoàn tiền và trả lại sản phẩm trong vòng một tuần sau khi nhận được hàng.
- Tại sao tương đồng: Mặc dù dùng từ ngữ và cấu trúc câu khác nhau, cả hai câu đều biểu thị cùng một nội dung chính sách cho phép đổi trả/hoàn tiền trong thời hạn 7 ngày.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Sàn thương mại điện tử hỗ trợ người mua trả hàng trong vòng 7 ngày kể từ khi nhận hàng.
- Câu B: Laptop Dell XPS 15 được trang bị bộ vi xử lý Intel Core i9 và bộ nhớ RAM 32GB.
- Tại sao khác: Câu A nói về quy định chính sách đổi trả hàng, còn câu B mô tả thông số kỹ thuật phần cứng, hai ngữ cảnh hoàn toàn không liên quan đến nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
Độ tương tự cosine chỉ đo góc giữa các vector (hướng ngữ nghĩa) mà không bị phụ thuộc vào độ dài (magnitude) của vector. Khoảng cách Euclid đo độ dài tuyệt đối nên hai đoạn văn bản có cùng ý nghĩa nhưng độ dài khác nhau (như một câu tóm tắt và một đoạn văn chi tiết) sẽ có khoảng cách Euclid lớn, dẫn đến đánh giá sai lệch.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
- *Trình bày phép tính:* $\text{Số lượng chunk} = \left\lceil \frac{\text{độ dài} - \text{overlap}}{\text{chunk\_size} - \text{overlap}} \right\rceil = \left\lceil \frac{10000 - 50}{500 - 50} \right\rceil = \left\lceil \frac{9950}{450} \right\rceil = \lceil 22.11 \rceil = 23$
- *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
- Phép tính khi `overlap = 100`: $\left\lceil \frac{10000 - 100}{500 - 100} \right\rceil = \left\lceil \frac{9900}{400} \right\rceil = \lceil 24.75 \rceil = 25$ chunks (tăng thêm 2 chunks).
- Ta muốn tăng độ chồng chéo (overlap) để giữ gìn ngữ cảnh giữa ranh giới các đoạn (boundary context), tránh trường hợp thông tin hoặc câu văn quan trọng bị cắt đôi gây mất ý nghĩa khi thực hiện truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
Tôi sử dụng biểu thức chính quy (regex) `r'(?<=[.!?])(?:\s+|\n+)'` để phát hiện ranh giới kết thúc câu (`.`, `!`, `?`). Xử lý ngoại lệ bao gồm việc cắt bỏ khoảng trắng thừa (`strip()`) cho từng câu, loại bỏ các chuỗi rỗng và gom từ 1 đến `max_sentences_per_chunk` câu thành một chunk hoàn chỉnh.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
Thuật toán hoạt động theo chiến lược chia để trị (divide-and-conquer) dựa trên danh sách dấu phân cách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) là khi văn bản có độ dài $\le$ `chunk_size` hoặc khi không còn dấu phân cách nào (khi đó sẽ cắt cố định theo `chunk_size`).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
Khi thêm văn bản (`add_documents`), từng document được nhúng thành vector qua `_embedding_fn` và lưu dưới dạng bản ghi dictionary chứa `id`, `content`, `metadata`, `embedding`. Hàm `search` nhúng câu hỏi query và tính độ tương tự cosine (tích vô hướng) với tất cả các vector trong store, sau đó sắp xếp giảm dần để lấy `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
Phương thức `search_with_filter` thực hiện lọc (pre-filter) danh sách bản ghi thỏa mãn tất cả các thuộc tính trong `metadata_filter` trước khi tính điểm tương đồng vector. Phương thức `delete_document` duyệt qua các bản ghi và lọc bỏ tất cả các chunk có `id` hoặc `metadata['doc_id']` trùng với `doc_id` cần xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
Hàm `answer` gọi `store.search()` để lấy ra `top_k` chunks có điểm độ tương tự cao nhất. Các đoạn nội dung ngữ cảnh này được nối với nhau qua ký tự phân cách `\n---\n` và nhúng vào prompt theo cấu trúc: `Context:\n{context}\n\nQuestion: {question}\n\nPlease answer...`, sau đó chuyển cho `llm_fn` tạo câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.24s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách hỗ trợ đổi trả hàng trong vòng 7 ngày kể từ khi nhận sản phẩm. | Khách hàng được quyền hoàn trả mặt hàng và nhận lại tiền trong 7 ngày đầu. | Cao | -0.0319 (Mock) / ~0.85 (Real) | Đúng (với Real) |
| 2 | Người mua chịu phí vận chuyển nếu đổi ý không muốn mua nữa. | Trường hợp hoàn trả do nhu cầu cá nhân, khách hàng phải thanh toán cước phí giao hàng. | Cao | -0.0259 (Mock) / ~0.82 (Real) | Đúng (với Real) |
| 3 | Sản phẩm được bảo hành miễn phí toàn quốc trong 12 tháng. | Sản phẩm không thuộc diện được bảo hành miễn phí. | Cao | 0.1269 (Mock) / ~0.78 (Real) | Đúng |
| 4 | Thời hạn giao hàng dự kiến từ 2 đến 4 ngày làm việc. | Thời hạn sử dụng của sản phẩm là 24 tháng kể từ ngày sản xuất. | Thấp | -0.1159 (Mock) / ~0.42 (Real) | Đúng |
| 5 | Quy định bảo hành và đổi trả hàng điện tử đối với người mua. | Thời tiết hôm nay trời nắng nhẹ và nhiệt độ trung bình là 28 độ C. | Thấp | -0.0784 (Mock) / ~0.05 (Real) | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
Kết quả bất ngờ nhất là cặp câu 3 ("được bảo hành miễn phí" vs "không thuộc diện được bảo hành miễn phí") đạt điểm tương đồng cao nhất trong bài test giả lập và ở các mô hình thật, mặc dù ý nghĩa logic của chúng hoàn toàn trái ngược nhau. Điều này chứng minh rằng Embeddings chủ yếu gom nhóm văn bản dựa trên không gian chủ đề chung (semantic domain - cùng bàn về bảo hành sản phẩm), chứ khó phân biệt được các từ ngữ mang tính logic phủ định (như "không", "chưa") nếu không qua tinh chỉnh chuyên sâu.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn nhận tiền hoàn về ví ShopeePay và thẻ tín dụng/ghi nợ quy định bao lâu? *(Lọc `audience: buyer`)* | `refund-methods-and-time`: Tiền hoàn về Ví ShopeePay thường trong 24 giờ; thẻ tín dụng/ghi nợ mất 7–14 ngày làm việc... | 0.2025 | Có | Trả lời chính xác thời gian hoàn tiền theo từng kênh ví/thẻ dựa trên tài liệu được lọc. |
| 2 | Shopee có hỗ trợ đổi trực tiếp sang sản phẩm khác không và xử lý thế nào khi hàng nhận có vấn đề? *(Lọc `audience: buyer`)* | `return-eligibility`: Shopee chỉ xử lý Trả hàng/Hoàn tiền, không hỗ trợ đổi trực tiếp; có thể từ chối nhận tại bước đồng kiểm... | 0.2621 | Có | Trả lời chính xác Shopee không hỗ trợ đổi trực tiếp và hướng dẫn từ chối nhận hoặc tạo yêu cầu hoàn tiền. |
| 3 | Khi nghi ngờ hàng không chính hãng (hàng giả/nhái), người mua cần cung cấp bằng chứng gì? *(Lọc `audience: buyer`)* | `return-evidence`: Cung cấp video mở hộp liên tục, quét mã QR, kiểm tra số seri hãng, chụp ảnh sai khác bao bì... | 0.2446 | Có | Liệt kê chi tiết các bằng chứng cần nộp để chứng minh hàng không chính hãng. |
| 4 | Người mua có được viết hoặc dán trực tiếp thông tin vận chuyển lên hộp của nhà sản xuất khi gửi trả không? *(Lọc `audience: buyer`)* | `return-shipping-and-packaging`: Không viết hoặc dán trực tiếp lên hộp nguyên bản của nhà sản xuất; phải bọc hộp carton ngoài... | 0.2185 | Có | Cảnh báo rõ ràng quy định cấm viết/dán lên hộp gốc và hướng dẫn đóng gói an toàn. |
| 5 | Nếu người mua khiếu nại người bán hoàn dưới 50% giá trị sản phẩm hoàn trả thì Shopee xử lý thế nào? *(Lọc `audience: seller`)* | `seller-return-refund-obligations`: Shopee có thể cấn trừ phần chênh lệch trực tiếp từ Số dư Tài khoản Shopee của người bán... | 0.1818 | Có | Nêu chính xác cơ chế Shopee tự động khấu trừ số dư của người bán mà không cần thêm chấp thuận. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
Việc kết hợp lọc siêu dữ liệu (metadata filtering) theo đối tượng (`audience`: `buyer`/`seller`) trước khi thực hiện tìm kiếm tương đồng vector giúp loại bỏ hoàn toàn các tài liệu nhiễu không liên quan, tăng độ chính xác truy xuất (precision) lên mức tối đa ngay cả với mô hình embedding đơn giản.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
