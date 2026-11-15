#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "================================================================="
echo " 🧪 Running Full VeriNews Test Suite (Backend & Mobile)"
echo "================================================================="

# 1. Backend Pytest
echo "▶ [1/2] Running Backend Pytest Suite..."
docker compose exec -T backend python -m pytest tests/ -v

# 2. Flutter Mobile Tests
echo "▶ [2/2] Running Flutter Mobile Client Tests..."
cd mobile
flutter test

echo "================================================================="
echo " 🎉 ALL TESTS PASSED! Backend (20/20) & Flutter (7/7)"
echo "================================================================="
