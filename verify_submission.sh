#!/bin/bash
# Manual Project Verification Checklist for IntermodalFreightEnv
# Run this script to verify all critical components before submission
# Usage: bash verify_submission.sh

set -e

echo "=================================================="
echo "IntermodalFreightEnv - SUBMISSION VERIFICATION"
echo "=================================================="
echo "Date: $(date)"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Test function
test_check() {
    local test_name=$1
    local command=$2
    
    echo -n "🔍 $test_name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
    fi
}

# ============================================================================
# SECTION 1: Project Structure Verification
# ============================================================================
echo ""
echo "📦 SECTION 1: PROJECT STRUCTURE"
echo "================================="

test_check "README.md exists" "[ -f README.md ]"
test_check "Dockerfile exists" "[ -f Dockerfile ]"
test_check "docker-compose.yml exists" "[ -f docker-compose.yml ]"
test_check "requirements.txt exists" "[ -f requirements.txt ]"
test_check "openenv.yaml exists" "[ -f openenv.yaml ]"
test_check "app/ directory exists" "[ -d app ]"
test_check "baseline/ directory exists" "[ -d baseline ]"
test_check "tests/ directory exists" "[ -d tests ]"

# ============================================================================
# SECTION 2: Code Quality Verification
# ============================================================================
echo ""
echo "🧹 SECTION 2: CODE QUALITY"
echo "==========================="

test_check "app/constants.py exists" "[ -f app/constants.py ]"
test_check "app/exceptions.py exists" "[ -f app/exceptions.py ]"
test_check "app/utils/helpers.py exists" "[ -f app/utils/helpers.py ]"
test_check "No Python syntax errors" "python3 -m py_compile app/main.py 2>/dev/null"

# ============================================================================
# SECTION 3: Docker Build Verification
# ============================================================================
echo ""
echo "🐳 SECTION 3: DOCKER BUILD"
echo "==========================="

if command -v docker &> /dev/null; then
    echo -n "🔍 Docker is installed... "
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
    
    test_check "Docker image builds" "docker build -q -t openenv-test . >/dev/null 2>&1"
    
    if [ $? -eq 0 ]; then
        test_check "Docker image size < 2GB" "[ $(docker images | grep openenv-test | awk '{print $7}' | grep -o '^[0-9]*' | head -1) -lt 2000 ]"
    fi
else
    echo -e "${YELLOW}⚠️  Docker not installed - skipping Docker tests${NC}"
fi

# ============================================================================
# SECTION 4: Configuration Verification
# ============================================================================
echo ""
echo "⚙️  SECTION 4: CONFIGURATION"
echo "=============================="

test_check "README.md has YAML frontmatter" "grep -q 'title:' README.md"
test_check "Dockerfile specifies port 7860" "grep -q 'EXPOSE 7860' Dockerfile"
test_check "README.md has app_file configured" "grep -q 'app_file:' README.md"

# ============================================================================
# SECTION 5: Git Status
# ============================================================================
echo ""
echo "📝 SECTION 5: GIT STATUS"
echo "========================"

if command -v git &> /dev/null; then
    echo -n "🔍 Git repository... "
    if git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
    fi
    
    test_check "Git has commits" "[ $(git rev-list --count HEAD) -gt 0 ]"
    test_check "No uncommitted changes" "[ -z \"$(git status --porcelain)\" ]"
else
    echo -e "${YELLOW}⚠️  Git not installed${NC}"
fi

# ============================================================================
# SECTION 6: Summary
# ============================================================================
echo ""
echo "=================================================="
echo "📊 VERIFICATION SUMMARY"
echo "=================================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED - PROJECT READY FOR SUBMISSION!${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME CHECKS FAILED - FIX ISSUES BEFORE SUBMISSION${NC}"
    exit 1
fi
