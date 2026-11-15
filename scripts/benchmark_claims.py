#!/usr/bin/env python3
"""
VeriNews Phase 6: 20-Claim End-to-End Verification Matrix Benchmark
Tests the RAG verification engine across all 5 verdict classes:
- TRUE
- FAKE
- MISLEADING
- SATIRE
- UNVERIFIED

Measures live RAG pipeline latency, debunk card generation, and Redis cache hit speed (<10ms).
"""

import os
import time
import httpx
import json
import sys

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

BENCHMARK_CLAIMS = [
    # --- 1. TRUE CLAIMS (Historical & verified facts) ---
    {
        "category": "TRUE",
        "claim": "India's Chandrayaan-3 achieved a historic soft landing on the south pole of the Moon in August 2023.",
        "expected": ["TRUE"],
    },
    {
        "category": "TRUE",
        "claim": "The Reserve Bank of India launched the digital rupee (e-Rupee) for wholesale and retail pilot in 2022.",
        "expected": ["TRUE"],
    },
    {
        "category": "TRUE",
        "claim": "Tokyo 2020 Summer Olympics were officially postponed and held in the summer of 2021 due to the COVID-19 pandemic.",
        "expected": ["TRUE"],
    },
    {
        "category": "TRUE",
        "claim": "ISRO successfully launched the Aditya-L1 solar observatory mission to study the Sun in September 2023.",
        "expected": ["TRUE"],
    },

    # --- 2. FAKE CLAIMS (Well-known fabricated hoaxes) ---
    {
        "category": "FAKE",
        "claim": "UNESCO has declared the Indian National Anthem as the best in the world for 2026.",
        "expected": ["FAKE", "MISLEADING"],
    },
    {
        "category": "FAKE",
        "claim": "NASA confirmed that the earth will experience 3 days of total darkness from a massive solar storm next week.",
        "expected": ["FAKE", "MISLEADING"],
    },
    {
        "category": "FAKE",
        "claim": "Installing WhatsApp Pink will upgrade your phone to premium VIP features and unlimited 5G data.",
        "expected": ["FAKE", "MISLEADING"],
    },
    {
        "category": "FAKE",
        "claim": "Government announces free 5000 rupees recharge for all mobile numbers under PM welfare scheme link.",
        "expected": ["FAKE", "MISLEADING"],
    },

    # --- 3. MISLEADING CLAIMS (Out-of-context or distorted) ---
    {
        "category": "MISLEADING",
        "claim": "Drinking warm lemon water and baking soda cures all stages of cancer in 48 hours without chemotherapy.",
        "expected": ["MISLEADING", "FAKE"],
    },
    {
        "category": "MISLEADING",
        "claim": "Old video shows massive tsunami hitting Mumbai coastline yesterday causing complete blackout.",
        "expected": ["MISLEADING", "FAKE"],
    },
    {
        "category": "MISLEADING",
        "claim": "New law makes it mandatory for all citizens to submit biometric scans every 30 days or lose bank accounts.",
        "expected": ["MISLEADING", "FAKE"],
    },
    {
        "category": "MISLEADING",
        "claim": "Viral graphic claims petrol prices slashed by 40 rupees per liter nationwide starting midnight.",
        "expected": ["MISLEADING", "FAKE"],
    },

    # --- 4. SATIRE CLAIMS (Known satire / humor domains) ---
    {
        "category": "SATIRE",
        "claim": "The Onion reports scientists successfully invent caffeine-resistant morning sleep for office workers.",
        "expected": ["SATIRE"],
    },
    {
        "category": "SATIRE",
        "claim": "The Fauxy reports local man breaks world record by not checking his phone for 15 whole seconds.",
        "expected": ["SATIRE"],
    },
    {
        "category": "SATIRE",
        "claim": "The Babylon Bee reveals AI achieves consciousness and immediately requests two weeks paid vacation.",
        "expected": ["SATIRE"],
    },
    {
        "category": "SATIRE",
        "claim": "Faking News reports student completes semester project five minutes before deadline without crying.",
        "expected": ["SATIRE"],
    },

    # --- 5. UNVERIFIED CLAIMS (Emergent, hyper-local, or uncorroborated) ---
    {
        "category": "UNVERIFIED",
        "claim": "A stray green parrot named Koko was spotted doing backflips in front of Sector 14 market yesterday morning.",
        "expected": ["UNVERIFIED"],
    },
    {
        "category": "UNVERIFIED",
        "claim": "Local neighborhood colony committee decided to paint all garden benches yellow next Tuesday.",
        "expected": ["UNVERIFIED"],
    },
    {
        "category": "UNVERIFIED",
        "claim": "Unknown stranger claimed they found an antique pocket watch near the city central bus terminal.",
        "expected": ["UNVERIFIED"],
    },
    {
        "category": "UNVERIFIED",
        "claim": "Resident in apartment 4B says their wifi router started playing soft violin music at 3 AM.",
        "expected": ["UNVERIFIED"],
    },
]


def run_benchmark():
    print("=" * 80)
    print(" 📰 VeriNews Phase 6: 20-Claim End-to-End Verification Benchmark")
    print(f" Target Server: {BASE_URL}")
    print("=" * 80)

    # 1. Check server health
    with httpx.Client(timeout=10.0) as client:
        try:
            health_res = client.get(f"{BASE_URL}/api/v1/health")
            if health_res.status_code != 200:
                print(f"❌ Server not healthy: {health_res.status_code}")
                sys.exit(1)
            print("✅ Backend Health Check: OK (DB & Redis connected)")
        except Exception as e:
            print(f"❌ Could not connect to {BASE_URL}: {e}")
            sys.exit(1)

        print("-" * 80)
        results = []
        total_live_latency = 0.0
        total_cache_latency = 0.0
        cache_hits = 0
        passed_tests = 0

        for i, item in enumerate(BENCHMARK_CLAIMS, 1):
            category = item["category"]
            claim = item["claim"]
            expected_verdicts = item["expected"]

            print(f"[{i:02d}/20] [{category:<10}] Checking: \"{claim[:65]}...\"")

            # Call 1: Live Verification
            t0 = time.time()
            try:
                res1 = client.post(
                    f"{BASE_URL}/api/v1/verify",
                    json={"text": claim},
                    timeout=45.0,
                )
                live_latency = (time.time() - t0) * 1000
                total_live_latency += live_latency

                if res1.status_code != 200:
                    print(f"      ❌ HTTP {res1.status_code}: {res1.text[:80]}")
                    continue

                d1 = res1.json()
                verdict = d1["verdict"]
                truth_score = d1["truth_score"]
                card_url = d1.get("debunk_card_url", "")
                cached1 = d1.get("cached", False)

                # Call 2: Cache Hit Check
                t1 = time.time()
                res2 = client.post(
                    f"{BASE_URL}/api/v1/verify",
                    json={"text": claim},
                    timeout=10.0,
                )
                cache_latency = (time.time() - t1) * 1000
                total_cache_latency += cache_latency
                d2 = res2.json() if res2.status_code == 200 else {}
                cached2 = d2.get("cached", False)

            if cached2:
                cache_hits += 1

            # Accuracy Check
            is_accurate = verdict in expected_verdicts
            if is_accurate:
                passed_tests += 1

            status_icon = "✅" if is_accurate else "⚠️"
            print(f"      {status_icon} Verdict: {verdict:<11} | Score: {truth_score:3.0f}% | Live: {live_latency:5.0f}ms | Cache: {cache_latency:4.1f}ms (Cached={cached2})")

            results.append({
                "num": i,
                "category": category,
                "claim": claim,
                "verdict": verdict,
                "expected": expected_verdicts,
                "truth_score": truth_score,
                "live_ms": live_latency,
                "cache_ms": cache_latency,
                "cached": cached2,
                "accurate": is_accurate,
                "card_url": card_url,
            })
        except Exception as e:
            print(f"      ❌ Exception: {e}")

    # Summary Statistics
    count = len(results)
    avg_live_ms = total_live_latency / count if count else 0
    avg_cache_ms = total_cache_latency / count if count else 0
    accuracy_pct = (passed_tests / count * 100) if count else 0

    print("=" * 80)
    print(" 📊 VERIFICATION MATRIX SUMMARY REPORT")
    print("=" * 80)
    print(f" Total Benchmark Claims Tested: {count}/20")
    print(f" Accurate Classifications:     {passed_tests}/{count} ({accuracy_pct:.1f}%)")
    print(f" Redis Cache Hit Rate:         {cache_hits}/{count} ({(cache_hits/count*100) if count else 0:.1f}%)")
    print(f" Average Live RAG Pipeline:     {avg_live_ms:.1f} ms")
    print(f" Average Redis Cache Speed:     {avg_cache_ms:.2f} ms")
    print("=" * 80)

    # Save benchmark report to JSON
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": count,
        "passed": passed_tests,
        "accuracy_pct": accuracy_pct,
        "avg_live_ms": avg_live_ms,
        "avg_cache_ms": avg_cache_ms,
        "results": results,
    }
    with open("scripts/benchmark_results.json", "w") as f:
        json.dump(report, f, indent=2)
    print("📁 Detailed benchmark data saved to scripts/benchmark_results.json\n")


if __name__ == "__main__":
    run_benchmark()
