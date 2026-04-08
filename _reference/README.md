# Reference Materials

This folder contains verification scripts and testing utilities used during development. These are NOT required for running the production environment.

## Contents

### Verification Scripts
- **verify_math_logic.py** - Comprehensive mathematical formula verification (trilemma, rewards, modes)
- **verify_env_learning.py** - Environment initialization and learning capability verification
- **verify_permanent_solution.py** - Network connectivity permanent solution verification
- **verify_submission.py** - Pre-submission checklist verification (5/5 items)
- **FINAL_MATH_VERIFICATION.py** - Final mathematical logic and cargo delivery verification

### Testing Scripts
- **test_endpoints.sh** - Test all API endpoints via curl
- **verify_submission.sh** - Pre-submission verification shell script
- **MANUAL_TESTING.sh** - Manual testing procedures
- **QUICK_REFERENCE.sh** - Quick reference commands for development

## Usage

These scripts are primarily for developers to verify system behavior during development:

```bash
# Verify mathematical logic
python _reference/verify_math_logic.py

# Verify environment learning capability
python _reference/verify_env_learning.py

# Verify permanent network solution
python _reference/verify_permanent_solution.py

# Run all pre-submission checks
python _reference/verify_submission.py
```

## For Production

These scripts are NOT needed for production deployment. Run:

```bash
python inference.py  # Main inference agent
python -m pytest tests/  # Run unit tests
```

## For Judges/Submission

Judges should focus on:
1. `README.md` - Main documentation
2. `inference.py` - Main agent implementation
3. `app/` - Backend implementation
4. `tests/` - Test suite
5. HuggingFace Space - Live deployment

These reference materials are provided for transparency and development verification only.
