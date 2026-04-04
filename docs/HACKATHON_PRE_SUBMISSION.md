# IntermodalFreightEnv - Hackathon Pre-Submission Checklist

**Hackathon Deadline**: April 7, 2026, 11:59 PM IST  
**Status**: About to submit  
**Last Updated**: Just now

---

## 🚨 CRITICAL DISQUALIFICATION CRITERIA

These checks MUST pass or the project will be automatically rejected:

- [ ] **Docker builds successfully** (`docker build -t openenv-intermodalfreightenv .`)
- [ ] **Docker container runs** (`docker run -p 8000:8000 openenv-intermodalfreightenv`)
- [ ] **HuggingFace Space deployment works** (Automated ping returns HTTP 200)
- [ ] **Baseline script runs without errors** (`python baseline/run_baseline.py --base-url http://localhost:8000`)
- [ ] **OpenEnv spec validation passes** (`openenv validate --verbose`)
- [ ] **Grader returns varying scores** (Not always the same value)
- [ ] **No plagiarism detected**

---

## ✅ QUICK VERIFICATION CHECKLIST

### 1. Docker Build Test
```bash
cd /home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv
docker build -t openenv-intermodalfreightenv .
```
**Expected**: Image builds successfully without errors  
**Status**: ✅ VERIFIED (324MB image created)

### 2. API Endpoints Verification
```bash
# Start the API server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, test these endpoints:
curl http://localhost:8000/health
curl http://localhost:8000/tasks
curl -X POST http://localhost:8000/reset
curl -X POST http://localhost:8000/grader -H "Content-Type: application/json" -d '{"trajectory":[]}'
curl -X POST http://localhost:8000/baseline
```

**Expected Endpoints**:
- ✅ `/health` - GET - Health check
- ✅ `/tasks` - GET - Returns 3 distinct tasks with different action schemas
- ✅ `/reset` - POST - Reset environment
- ✅ `/grader` - POST - Returns `{"score": X.XX}` format
- ✅ `/baseline` - POST - Returns baseline scores for all 3 tasks

### 3. Task Distinctness Verification
```bash
# The /tasks endpoint should return 3 distinct tasks:
# 1. Task 1: Time Minimization (minimize hours)
# 2. Task 2: Cost Minimization (minimize cost)  
# 3. Task 3: Multimodal Optimization (balance time/cost/carbon)

# Action schemas should be different:
# - Task 1 & 2: cargo_id, path
# - Task 3: cargo_id, cargo_type, path, split_at (has extra fields for multimodal)
```

### 4. Baseline Script Test
```bash
# Make sure the API is running first
python baseline/run_baseline.py --base-url http://localhost:8000

# Expected:
# - Runs for multiple agents (random, greedy, dijkstra)
# - Returns evaluation report
# - Exits with code 0
```

### 5. OpenEnv Validation Test
```bash
# Install openenv if not already installed
pip install openenv

# Validate the spec
openenv validate --verbose

# Expected: All checks pass
```

---

## 📋 STEP-BY-STEP PRE-SUBMISSION SEQUENCE

Follow this exact sequence before submitting the HuggingFace Space URL:

### Step 1: Prepare Environment
```bash
cd /home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv
source .venv/bin/activate  # Or your Python environment
pip install -r requirements.txt --upgrade
```

### Step 2: Build Docker Image
```bash
docker build -t openenv-intermodalfreightenv .
# Expected: Image successfully built
# Check: docker images | grep intermodalfreightenv
```

### Step 3: Start API Server
```bash
# Terminal 1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Wait until: "Uvicorn running on http://0.0.0.0:8000"
```

### Step 4: Verify All Endpoints (Terminal 2)
```bash
# Health check
curl http://localhost:8000/health
# Expected: {"success": true, "message": "API is healthy"}

# Tasks endpoint
curl http://localhost:8000/tasks | python -m json.tool
# Expected: 3 tasks with different action schemas

# Grader endpoint
curl -X POST http://localhost:8000/grader \
  -H "Content-Type: application/json" \
  -d '{"trajectory": []}'
# Expected: {"score": 0.0} (or similar)

# Baseline endpoint
curl -X POST http://localhost:8000/baseline
# Expected: {"task_1_score": X.XX, "task_2_score": Y.YY, "task_3_score": Z.ZZ}
```

### Step 5: Test Baseline Script
```bash
python baseline/run_baseline.py --base-url http://localhost:8000

# Expected:
# - Script runs without errors
# - Prints results for random, greedy, and dijkstra agents
# - Exits with code 0: echo $?  (should print 0)
```

### Step 6: Validate OpenEnv Spec
```bash
openenv validate --verbose

# Expected: All validations pass
```

### Step 7: Docker Container Test
```bash
# In a new terminal
docker run -p 8001:8000 openenv-intermodalfreightenv

# In another terminal, test endpoints
curl http://localhost:8001/health
curl http://localhost:8001/tasks

# Stop the container: Ctrl+C in the docker terminal
```

### Step 8: Deploy to HuggingFace Spaces
```bash
# Make sure you've set up your HF token
huggingface-cli login

# Create or update your Space
openenv push

# Expected: Space is created/updated and accessible online
```

### Step 9: Test Live Space
```bash
# Get your Space URL (e.g., https://huggingface.co/spaces/YOUR_USERNAME/your-space)
# Test the health endpoint
curl https://your-huggingface-space-url/health

# Expected: HTTP 200 response
```

---

## 🔍 VERIFICATION MATRIX

| Requirement | Command | Status | Notes |
|---|---|---|---|
| Docker builds | `docker build -t openenv-intermodalfreightenv .` | ✅ | 324MB image |
| /health endpoint | `curl http://localhost:8000/health` | ✅ | Returns success |
| /tasks endpoint | `curl http://localhost:8000/tasks` | ✅ | 3 distinct tasks |
| /reset endpoint | `curl -X POST http://localhost:8000/reset` | ✅ | Resets environment |
| /grader endpoint | `curl -X POST http://localhost:8000/grader` | ✅ | Returns score |
| /baseline endpoint | `curl -X POST http://localhost:8000/baseline` | ✅ | NEW - Returns 3 scores |
| Baseline script | `python baseline/run_baseline.py` | ⏳ | Needs testing |
| OpenEnv spec | `openenv validate --verbose` | ⏳ | Needs openenv package |
| HF Space | Deploy and test | ⏳ | Not started |

---

## 🎯 ABSOLUTE MUST-HAVES FOR HACKATHON

### Functional Requirements
- ✅ 3 Distinct Tasks with different objectives
  - Task 1: Minimize time (accumulated_hours)
  - Task 2: Minimize cost (accumulated_cost)
  - Task 3: Optimize multimodal routing (balance all metrics)
  
- ✅ Action Schemas are Distinct
  - Task 1 & 2: `{cargo_id, path}`
  - Task 3: `{cargo_id, cargo_type, path, split_at}` (extra fields)
  
- ✅ Grader Implementation
  - Formula: `Score = 0.5×time + 0.3×cost + 0.2×carbon`
  - Normalized to [0.0, 1.0]
  - Returns varying scores for different trajectories
  
- ✅ OpenEnv Specification Compliance
  - Proper task definitions in openenv.yaml
  - Pydantic models for Observation, Action, Reward
  - Deterministic scoring

### Non-Functional Requirements
- ✅ Docker Containerization
  - Dockerfile must build successfully
  - docker-compose.yml for orchestration
  
- ✅ HuggingFace Spaces Deployment
  - Automated health check must pass
  - Live URL must be responsive
  - Must be tagged with `openenv` label
  
- ✅ Code Quality
  - No plagiarism
  - Clean error handling
  - Proper logging

---

## 🚀 FINAL SUBMISSION CHECKLIST

Before clicking "Submit":

- [ ] Docker image builds: `docker build -t openenv-intermodalfreightenv .`
- [ ] All API endpoints responding: `/health`, `/tasks`, `/grader`, `/baseline`
- [ ] Baseline script runs: `python baseline/run_baseline.py --base-url http://localhost:8000`
- [ ] OpenEnv validation passes: `openenv validate --verbose`
- [ ] Docker container runs: `docker run -p 8000:8000 openenv-intermodalfreightenv`
- [ ] HuggingFace Space is deployed and live
- [ ] Health check on live Space returns HTTP 200
- [ ] No hardcoded credentials or secrets in code
- [ ] README.md is clear and comprehensive
- [ ] All required endpoints are working

---

## ⚠️ COMMON ISSUES & FIXES

### Issue: Docker build fails
**Solution**: Check that all files are present (app/, baseline/, config/, openenv.yaml)

### Issue: /baseline endpoint returns empty scores
**Solution**: Make sure the API is running on localhost:8000 and baseline agents can access it

### Issue: OpenEnv validation fails
**Solution**: Ensure openenv.yaml is properly formatted YAML and matches Python types

### Issue: HF Space deployment fails
**Solution**: Check your HuggingFace token, make sure you've run `huggingface-cli login`

### Issue: Baseline script times out
**Solution**: Increase max_steps or check if API is responding: `curl http://localhost:8000/health`

---

## 📞 SUPPORT

If you encounter any issues:

1. Check the logs: Check the API server terminal for error messages
2. Verify connectivity: `curl http://localhost:8000/health`
3. Check Docker: `docker ps` to see running containers
4. Review OpenEnv spec: Check openenv.yaml syntax

---

**Created**: From conversation with GitHub Copilot  
**Purpose**: Pre-submission validation for Scaler School of Technology Hackathon  
**Target State**: Ready for HuggingFace Space deployment
