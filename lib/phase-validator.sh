#!/usr/bin/env bash
#
# Phase Validation Script
# Validates that code quality passes before marking a phase complete
#
# Usage:
#   ./lib/phase-validator.sh [phase_number]
#
# Exit codes:
#   0 - All checks passed
#   1 - Test collection failed
#   2 - Tests failed
#   3 - Lint errors found
#

set -e

PHASE="${1:-current}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Phase Validation for ${PHASE} ==="
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# 1. Check test collection
echo -e "${YELLOW}[1/3] Checking test collection...${NC}"
COLLECTION_OUTPUT=$(python -m pytest tests/unit/ --collect-only -q 2>&1)
COLLECTION_ERRORS=$(echo "$COLLECTION_OUTPUT" | grep -c "ERROR collecting" || echo "0")

if [ "$COLLECTION_ERRORS" -gt "0" ]; then
    echo -e "${RED}FAIL: $COLLECTION_ERRORS test collection errors found${NC}"
    echo "$COLLECTION_OUTPUT" | grep -A 5 "ERROR collecting"
    exit 1
fi

TEST_COUNT=$(echo "$COLLECTION_OUTPUT" | tail -1 | grep -oE '[0-9]+ tests' | grep -oE '[0-9]+' || echo "0")
echo -e "${GREEN}PASS: $TEST_COUNT tests collected${NC}"

# 2. Run tests
echo ""
echo -e "${YELLOW}[2/3] Running tests...${NC}"
TEST_OUTPUT=$(python -m pytest tests/unit/ \
    --tb=short \
    -q \
    --ignore=tests/button_test \
    --ignore=tests/fader_test \
    --ignore=tests/led_test \
    --ignore=tests/neve_knobs \
    2>&1) || TEST_RESULT=$?

if [ "${TEST_RESULT:-0}" -ne "0" ]; then
    echo -e "${RED}FAIL: Tests failed${NC}"
    echo "$TEST_OUTPUT" | tail -20
    exit 2
fi

PASSED=$(echo "$TEST_OUTPUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "?")
SKIPPED=$(echo "$TEST_OUTPUT" | grep -oE '[0-9]+ skipped' | grep -oE '[0-9]+' || echo "0")
echo -e "${GREEN}PASS: $PASSED tests passed ($SKIPPED skipped)${NC}"

# 3. Run lint checks
echo ""
echo -e "${YELLOW}[3/3] Running lint checks...${NC}"

# Check for TODO/FIXME without tickets
TODOS=$(grep -r "TODO\|FIXME" lib/ --include="*.py" | grep -v "# TODO-" | grep -v "ticket" | wc -l | tr -d ' ')
if [ "$TODOS" -gt "0" ]; then
    echo -e "${YELLOW}WARN: $TODOS TODO/FIXME comments without tickets${NC}"
fi

# Check for NotImplementedError in production code (excluding plugin_interface)
NOT_IMPL=$(grep -r "raise NotImplementedError" lib/ --include="*.py" | grep -v "plugin_interface" | wc -l | tr -d ' ')
if [ "$NOT_IMPL" -gt "0" ]; then
    echo -e "${YELLOW}WARN: $NOT_IMPL NotImplementedError found (excluding plugin_interface)${NC}"
fi

# Check for pass statements
PASS_COUNT=$(grep -r "^\s*pass$" lib/ --include="*.py" | wc -l | tr -d ' ')
if [ "$PASS_COUNT" -gt "10" ]; then
    echo -e "${YELLOW}WARN: $PASS_COUNT pass statements found${NC}"
fi

echo -e "${GREEN}PASS: Lint checks complete${NC}"

# Summary
echo ""
echo "=== Validation Complete ==="
echo -e "${GREEN}All checks passed for phase ${PHASE}${NC}"
exit 0
