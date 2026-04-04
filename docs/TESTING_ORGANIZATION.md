# 📁 Testing & Scripts Organization Guide

## New Directory Structure

```
IntermodalFreightEnv/
├── tests/                           # ✅ ALL TEST FILES (7 tests)
│   ├── __init__.py
│   ├── test_api_layer.py           # API endpoint testing
│   ├── test_core_systems.py        # Core systems testing
│   ├── test_environment_logic.py   # Environment logic testing
│   ├── test_mathematics.py         # Mathematical formula testing (29 tests)
│   ├── test_regressions.py         # Regression testing (12 tests)
│   ├── validate_math.py            # Math validation (38 tests)
│   └── verify_checklist.py         # Checklist verification
│
├── scripts/                         # ✅ UTILITY SCRIPTS (3 scripts)
│   ├── __init__.py
│   ├── debug_agent_learning.py     # Debug learning behavior
│   ├── run_all_math_tests.py       # Master test runner
│   └── view_value_results.py       # View and analyze results
│
├── docs/                            # Documentation (22 markdown files)
├── app/                             # Main application code
└── baseline/                        # Baseline agents
```

---

## 🧪 Running Tests

### Run All Tests
```bash
# From project root
cd /path/to/IntermodalFreightEnv

# Run all tests with Python unittest discovery
python3 -m pytest tests/ -v

# Or run specific test suite
python3 tests/test_mathematics.py
python3 tests/test_api_layer.py
python3 tests/test_environment_logic.py
```

### Run Mathematical Tests
```bash
# Quick validation (38 tests, ~2 seconds)
python3 tests/validate_math.py

# Comprehensive unit tests (29 tests, ~0.1 seconds)
python3 tests/test_mathematics.py

# Regression tests (12 tests, ~1 second)
python3 tests/test_regressions.py

# Master runner (all math tests, ~3 seconds)
python3 scripts/run_all_math_tests.py
```

### Run Verification
```bash
# Verify all checklist items
python3 tests/verify_checklist.py

# Verify API layer
python3 tests/test_api_layer.py
```

---

## 🛠️ Running Utility Scripts

### Debug Agent Learning
```bash
python3 scripts/debug_agent_learning.py

# Shows:
# - Task definitions
# - Empty trajectory metrics
# - Scoring formula
# - Expected trajectories
```

### View Results Analysis
```bash
python3 scripts/view_value_results.py

# Shows:
# - Task definitions
# - Empty trajectory analysis
# - Scoring sensitivity
# - Trilemma weights explanation
```

### Master Test Runner
```bash
python3 scripts/run_all_math_tests.py

# Runs all math test suites:
# 1. Validation Suite (38 tests)
# 2. Unit Test Suite (29 tests)
# 3. Regression Test Suite (12 tests)
# Shows comprehensive summary
```

---

## 📊 Test Files Summary

| File | Purpose | Tests | Runtime |
|------|---------|-------|---------|
| `test_api_layer.py` | API endpoint testing | Multiple | ~5s |
| `test_core_systems.py` | Core algorithm testing | Multiple | ~5s |
| `test_environment_logic.py` | Environment logic | 41+ | ~10s |
| `test_mathematics.py` | Math formulas | 29 | ~0.1s |
| `test_regressions.py` | Regression detection | 12 | ~1s |
| `validate_math.py` | Quick validation | 38 | ~2s |
| `verify_checklist.py` | Checklist verification | Multiple | ~5s |

**Total Tests:** 150+ tests  
**Total Runtime:** ~30 seconds

---

## 🔧 Utility Scripts

| File | Purpose |
|------|---------|
| `debug_agent_learning.py` | Debug agent learning patterns and trajectories |
| `view_value_results.py` | Analyze and visualize environment results |
| `run_all_math_tests.py` | Master runner for all mathematical tests |

---

## 🚀 CI/CD Integration

### GitHub Actions
```yaml
- name: Run Tests
  run: |
    python3 -m unittest discover tests/ -p "test_*.py" -v
    python3 scripts/run_all_math_tests.py
```

### Pre-commit Hook
```bash
#!/bin/bash
python3 tests/validate_math.py || exit 1
python3 tests/verify_checklist.py || exit 1
```

### Jenkins Pipeline
```groovy
stage('Tests') {
    steps {
        sh 'python3 -m unittest discover tests/'
        sh 'python3 scripts/run_all_math_tests.py'
    }
}
```

---

## 🎯 Running Tests by Category

### Mathematical Tests Only
```bash
cd /path/to/IntermodalFreightEnv
python3 tests/validate_math.py        # Quick validation
python3 tests/test_mathematics.py     # Comprehensive
python3 tests/test_regressions.py     # Regression
```

### Integration Tests
```bash
python3 tests/test_api_layer.py
python3 tests/test_environment_logic.py
python3 tests/test_core_systems.py
```

### All Tests
```bash
python3 -m unittest discover tests/ -p "*.py" -v
```

---

## 📝 Import Notes

All tests and scripts maintain root-relative imports:

```python
# ✅ Works correctly from any location
from app.api.grader import Grader
from app.engine.graph import FreightNetwork
from app.engine.core_env import FreightEnvironment

# ✅ When running from scripts/ or tests/ folders:
python3 test_mathematics.py  # Imports still work!
```

**Why?** All imports use `from app.*` which references the root-level `app/` folder. Python's path resolution handles this correctly regardless of script location.

---

## 📂 Benefits of This Organization

✅ **Clear Separation**
- Tests grouped by type
- Utility scripts separated
- Easy to find what you need

✅ **Better Discoverability**
- All tests in one place
- Easy unittest discovery
- Better IDE integration

✅ **Cleaner Root**
- Only essential files in root
- App code and configs at top level
- Documentation separate

✅ **Easier Maintenance**
- Tests organized logically
- Scripts easy to find
- Clear purpose for each file

✅ **CI/CD Ready**
- `python3 -m unittest discover tests/`works perfectly
- Scripts run from any location
- Standard project structure

---

## 🔍 Quick Reference

```bash
# From project root:

# Run everything
python3 -m unittest discover tests/

# Run math tests
python3 tests/validate_math.py
python3 scripts/run_all_math_tests.py

# Run verification
python3 tests/verify_checklist.py

# Debug/analyze
python3 scripts/debug_agent_learning.py
python3 scripts/view_value_results.py

# Run specific test
python3 tests/test_api_layer.py
python3 tests/test_environment_logic.py
python3 tests/test_core_systems.py
```

---

## ✨ Migration Notes

**Changed:** Test and script files moved to `tests/` and `scripts/` folders  
**Unchanged:** All imports remain the same (use root-relative paths)  
**Impact:** Zero - Tests work exactly the same way  
**Benefit:** Much cleaner project structure!

---

**Status:** ✅ Organization complete  
**Test Compatibility:** ✅ All tests work  
**Import Compatibility:** ✅ All imports work  
**Ready to Use:** ✅ YES
