#!/usr/bin/env python3
"""
Test script for NLM Retriever module.

Usage:
    # Test all retrievers
    uv run python -m src.app.services.nlm_retriever.test_pipeline

    # Quick test (keyword only)
    uv run python -m src.app.services.nlm_retriever.test_pipeline --quick
"""

import argparse
import time
from typing import List

from .examples import get_default_examples
from .pipeline import RetrievalPipeline, PipelineConfig


# Test queries with expected intents
TEST_QUERIES = [
    # 현장작업자
    ("라인 살아있어?", "daily_status"),
    ("이거 망가졌어", "equipment_error"),
    ("다음 뭐야?", "work_orders_pending"),
    ("몇 개 더 해야 해?", "production_count"),
    ("빨간불 들어왔어", "equipment_error"),
    # 공장관리자
    ("병목 설비 어디야?", "equipment_status"),
    ("전체 라인 상태", "daily_status"),
    ("목표 달성률", "production_count"),
    ("이번주 뭘 했어?", "trend"),
    # 사장님
    ("오늘 잘 돌아가?", "daily_status"),
    ("납기 지킬 수 있어?", "schedule"),
    ("클레임 들어온 거 있어?", "defect_analysis"),
    ("저번 달보다 나아?", "compare_status"),
    ("숫자로 보여줘", "kpi"),
    # 기타
    ("안녕", "greeting"),
    ("도움말", "help"),
]


def test_pipeline(
    pipeline: RetrievalPipeline,
    queries: List[tuple],
    verbose: bool = True,
) -> dict:
    """Test a pipeline with queries."""
    correct = 0
    total = len(queries)
    results = []

    for query, expected in queries:
        start = time.time()
        retrieved = pipeline.retrieve(query, top_k=3)
        elapsed = (time.time() - start) * 1000

        top_intent = retrieved[0].intent if retrieved else "unknown"
        top_score = retrieved[0].score if retrieved else 0.0
        is_correct = top_intent == expected

        if is_correct:
            correct += 1

        results.append(
            {
                "query": query,
                "expected": expected,
                "predicted": top_intent,
                "score": top_score,
                "correct": is_correct,
                "time_ms": elapsed,
            }
        )

        if verbose:
            status = "✅" if is_correct else "❌"
            print(f"{status} {query}")
            print(f"   Expected: {expected}, Got: {top_intent} ({top_score:.3f})")
            if len(retrieved) > 1:
                print(f"   Alternatives: {[(r.intent, f'{r.score:.3f}') for r in retrieved[1:3]]}")
            print(f"   Time: {elapsed:.1f}ms")
            print()

    accuracy = correct / total if total > 0 else 0
    avg_time = sum(r["time_ms"] for r in results) / total if total > 0 else 0

    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "avg_time_ms": avg_time,
        "results": results,
    }


def run_tests(quick: bool = False, device: str = "cpu"):
    """Run all tests."""
    examples = get_default_examples()
    print(f"Loaded {len(examples)} training examples")
    print(f"Testing {len(TEST_QUERIES)} queries\n")
    print("=" * 60)

    # Test 1: Keyword Retriever (always run)
    print("\n🔤 Testing KeywordRetriever...")
    print("-" * 40)

    config = PipelineConfig.default_keyword()
    pipeline = RetrievalPipeline.from_config(config)
    pipeline.initialize(examples)

    keyword_results = test_pipeline(pipeline, TEST_QUERIES)
    print(
        f"\nKeyword Accuracy: {keyword_results['accuracy']:.1%} ({keyword_results['correct']}/{keyword_results['total']})"
    )
    print(f"Avg Time: {keyword_results['avg_time_ms']:.1f}ms")

    if quick:
        print("\n(Quick mode - skipping ML models)")
        return

    # Test 2: Embedding Retriever
    print("\n" + "=" * 60)
    print("\n🧠 Testing EmbeddingRetriever...")
    print("-" * 40)

    try:
        config = PipelineConfig.default_semantic(device=device)
        pipeline = RetrievalPipeline.from_config(config)
        pipeline.initialize(examples)

        embedding_results = test_pipeline(pipeline, TEST_QUERIES)
        print(
            f"\nEmbedding Accuracy: {embedding_results['accuracy']:.1%} ({embedding_results['correct']}/{embedding_results['total']})"
        )
        print(f"Avg Time: {embedding_results['avg_time_ms']:.1f}ms")
    except ImportError as e:
        print(f"Skipped (missing dependency): {e}")
        embedding_results = None

    # Test 3: Hybrid + Cross-encoder
    print("\n" + "=" * 60)
    print("\n🚀 Testing Hybrid + CrossEncoder...")
    print("-" * 40)

    try:
        config = PipelineConfig.default_hybrid_rerank(device=device)
        pipeline = RetrievalPipeline.from_config(config)
        pipeline.initialize(examples)

        hybrid_results = test_pipeline(pipeline, TEST_QUERIES)
        print(
            f"\nHybrid+Rerank Accuracy: {hybrid_results['accuracy']:.1%} ({hybrid_results['correct']}/{hybrid_results['total']})"
        )
        print(f"Avg Time: {hybrid_results['avg_time_ms']:.1f}ms")
    except ImportError as e:
        print(f"Skipped (missing dependency): {e}")
        hybrid_results = None

    # Summary
    print("\n" + "=" * 60)
    print("\n📊 Summary")
    print("-" * 40)
    print(
        f"Keyword:        {keyword_results['accuracy']:.1%} ({keyword_results['avg_time_ms']:.1f}ms avg)"
    )
    if embedding_results:
        print(
            f"Embedding:      {embedding_results['accuracy']:.1%} ({embedding_results['avg_time_ms']:.1f}ms avg)"
        )
    if hybrid_results:
        print(
            f"Hybrid+Rerank:  {hybrid_results['accuracy']:.1%} ({hybrid_results['avg_time_ms']:.1f}ms avg)"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test NLM Retriever")
    parser.add_argument("--quick", action="store_true", help="Quick test (keyword only)")
    parser.add_argument("--device", default="cpu", help="Device for ML models (cpu/cuda)")
    args = parser.parse_args()

    run_tests(quick=args.quick, device=args.device)
