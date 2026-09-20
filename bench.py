#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bench.py — Công cụ đo lường và đánh giá chất lượng truy xuất (Benchmark Tool)
Dành cho: Đinh Kim Thái (2A202602417) — Nhóm G34
Chiến lược thử nghiệm: Fixed-size Chunker (chunk_size=450, overlap=80)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import yaml

from src.chunking import FixedSizeChunker
from src.models import Document
from src.store import EmbeddingStore

# Cấu hình UTF-8 cho Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DATA_DIR = Path("data/ecommerce")
OUTPUT_FILE = Path("ket_qua_benchmark.txt")

QUERIES = [
    {
        "id": "Q1",
        "query": "Các lý do liên quan đến sản phẩm gồm hư hỏng, bể vỡ, sai sản phẩm hoặc thiếu phụ kiện là gì?",
        "gold_doc": "return-eligibility",
        "filter": None,
    },
    {
        "id": "Q2",
        "query": "Thực phẩm tươi sống hoặc đông lạnh có thời hạn ngắn hơn bao lâu?",
        "gold_doc": "return-window",
        "filter": None,
    },
    {
        "id": "Q3",
        "query": "Khi nghi ngờ hàng giả, cần bằng chứng kỹ thuật nào?",
        "gold_doc": "return-evidence",
        "filter": None,
    },
    {
        "id": "Q4",
        "query": "Hoàn tiền về thẻ tín dụng hoặc ghi nợ mất bao lâu?",
        "gold_doc": "refund-methods-and-time",
        "filter": None,
    },
    {
        "id": "Q5",
        "query": "Nếu người bán hoàn dưới 50% giá trị sản phẩm thì sao?",
        "gold_doc": "seller-return-refund-obligations",
        "filter": {"audience": "seller"},
    },
]


def load_and_chunk_corpus(chunker: FixedSizeChunker) -> list[Document]:
    documents: list[Document] = []
    md_files = sorted(DATA_DIR.glob("*.md"))

    for path in md_files:
        text = path.read_text(encoding="utf-8")
        if text.startswith("---"):
            parts = text.split("---", 2)
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip() if len(parts) > 2 else ""
        else:
            meta = {}
            body = text.strip()

        chunks = chunker.chunk(body)
        for i, chunk in enumerate(chunks):
            doc_meta = dict(meta)
            doc_meta["doc_id"] = path.stem
            doc_meta["chunk_index"] = i
            documents.append(
                Document(
                    id=f"{path.stem}#{i}",
                    content=chunk,
                    metadata=doc_meta,
                )
            )

    return documents


def run_benchmark() -> str:
    lines: list[str] = []

    def log(msg: str = ""):
        print(msg)
        lines.append(msg)

    log("=" * 70)
    log("KẾT QUẢ BENCHMARK TRUY XUẤT RAG — LAB 07")
    log("Sinh viên: Đinh Kim Thái — MSSV: 2A202602417 — Nhóm: G34")
    log("Chiến lược: FixedSizeChunker (chunk_size=450, overlap=80)")
    log("=" * 70)

    chunker = FixedSizeChunker(chunk_size=450, overlap=80)
    docs = load_and_chunk_corpus(chunker)
    log(f"\n[1] Đã nạp và phân đoạn corpus: {len(docs)} chunks từ {DATA_DIR}")

    store = EmbeddingStore(collection_name="benchmark_store")
    store.add_documents(docs)
    log(f"[2] Đã nhúng và lưu trữ vào EmbeddingStore (Size: {store.get_collection_size()})\n")

    log("=" * 70)
    log("CHẠY 5 BENCHMARK QUERIES CỦA NHÓM:")
    log("=" * 70)

    score_total = 0
    for q in QUERIES:
        qid = q["id"]
        query_text = q["query"]
        gold = q["gold_doc"]
        meta_filter = q["filter"]

        log(f"\n--- {qid}: {query_text} ---")
        log(f"Tài liệu chuẩn (Gold): {gold}")
        if meta_filter:
            log(f"Bộ lọc (Metadata Filter): {meta_filter}")

        results = store.search_with_filter(query_text, top_k=3, metadata_filter=meta_filter)

        log("Top-3 Kết quả truy xuất:")
        found_in_top3 = False
        top1_correct = False

        for rank, r in enumerate(results, start=1):
            r_doc = r["metadata"].get("doc_id", "unknown")
            r_score = r["score"]
            preview = r["content"][:100].replace("\n", " ")
            is_match = (r_doc == gold)
            tag = " [CHÍNH XÁC]" if is_match else ""
            log(f"  Rank {rank}: doc_id={r_doc} (score={r_score:.4f}){tag}")
            log(f"         Preview: \"{preview}...\"")

            if is_match:
                found_in_top3 = True
                if rank == 1:
                    top1_correct = True

        pts = 2 if top1_correct else (1 if found_in_top3 else 0)
        score_total += pts
        log(f"-> Điểm đánh giá câu {qid}: {pts}/2 điểm")

    log("\n" + "=" * 70)
    log(f"TỔNG ĐIỂM TRUY XUẤT: {score_total}/10 ĐIỂM")
    log("=" * 70)

    # A/B Testing bắt buộc đối với Q5 (Thử nghiệm metadata filter)
    log("\n[3] THỬ NGHIỆM A/B METADATA FILTER (Q5):")
    q5_text = QUERIES[4]["query"]
    log(f"Câu hỏi: {q5_text}")

    res_no_filter = store.search(q5_text, top_k=3)
    log("  A) Không có filter (audience=both/all):")
    for rank, r in enumerate(res_no_filter, start=1):
        log(f"     Rank {rank}: {r['metadata'].get('doc_id')} (audience: {r['metadata'].get('audience')}, score: {r['score']:.4f})")

    res_with_filter = store.search_with_filter(q5_text, top_k=3, metadata_filter={"audience": "seller"})
    log("  B) Có filter (audience=seller):")
    for rank, r in enumerate(res_with_filter, start=1):
        log(f"     Rank {rank}: {r['metadata'].get('doc_id')} (audience: {r['metadata'].get('audience')}, score: {r['score']:.4f})")

    log("\nKết luận A/B: Khi lọc audience=seller, toàn bộ các chunk của buyer bị loại bỏ trước khi ranking,")
    log("đảm bảo context nạp vào LLM tập trung 100% vào nghĩa vụ người bán.")
    log("=" * 70)

    return "\n".join(lines)


if __name__ == "__main__":
    output_text = run_benchmark()
    OUTPUT_FILE.write_text(output_text, encoding="utf-8")
    print(f"\n Đã lưu toàn bộ kết quả vào: {OUTPUT_FILE.resolve()}")
