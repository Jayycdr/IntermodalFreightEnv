# Manual Testing Guide

## Overview

This guide walks you through manually testing the IntermodalFreightEnv backend and frontend. You'll need 3 terminal windows/tabs.

---

## Step-by-Step Setup

### Step 1: Start Backend (Terminal 1)

Open a new terminal and run:

```bash
cd "/home/harsh/CodeWithHarsh/ML Projects/IntermodalFreightEnv"

/home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process [12345]
INFO:     Application startup complete
```

✅ **Keep this terminal open and running**. You'll see logs as requests come in.

---

### Step 2: Test API Endpoints (Terminal 2)

Once the backend is running, open a NEW terminal and test the endpoints:

#### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

**Expected:** 
```json
{"success": true, "message": "API healthy", "data": null}
```

✅ If you see this, the backend is responding!

#### Test 2: Get Tasks
```bash
curl http://localhost:8000/tasks | python3 -m json.tool | head -50
```

**Expected:** JSON with 3 tasks (Time, Cost, Multimodal)

✅ Verify 3 distinct task names appear

#### Test 3: Reset Environment
```bash
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1}'
```

**Expected:**
```json
{
  "state": {"step": 0, "active_cargos": 0, ...},
  "message": "Environment reset successfully"
}
```

✅ Verify `step: 0` (reset position)

#### Test 4: Grade a Trajectory
```bash
curl -X POST http://localhost:8000/grader \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "trajectory": [{"action": "move", "observation": {}}]}'
```

**Expected:**
```json
{
  "success": true,
  "data": {
    "score": 0.0,
    "metrics": {
      "accumulated_hours": 0.0,
      "accumulated_cost": 0.0,
      "accumulated_carbon": 0.0
    }
  }
}
```

✅ Verify score is between 0 and 1

---

### Step 3: Start Frontend Dashboard (Terminal 3)

Once backend is confirmed working, open ANOTHER NEW terminal and run:

```bash
cd "/home/harsh/CodeWithHarsh/ML Projects/IntermodalFreightEnv"

/home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv/.venv/bin/python -m streamlit run frontend/dashboard.py --server.port=8501
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

✅ **Open your browser to http://localhost:8501**

---

## Frontend Testing Checklist

Once the dashboard loads, verify these features:

### ✅ Sidebar Configuration
- [ ] API URL field shows `http://localhost:8000`
- [ ] Health status shows ✅ **green checkmark** (not ❌ red X)
- [ ] Task selector has 3 options
- [ ] Can toggle "Use fixed seed" checkbox
- [ ] Reset button is clickable

### ✅ Task Selection & Reset
- [ ] Select **Task 1: Time Minimization**
- [ ] Click **🔄 Reset Environment**
- [ ] Dashboard refreshes with state
- [ ] See 4 metric cards appear:
  - ⏱️ Time (hours) = 0.00
  - 💰 Cost ($1000s) = 0.00
  - 🌍 Carbon (tons CO2) = 0.00
  - 📦 Weight (tons) = some value

### ✅ Task Details
- [ ] Expand "Task Details" section
- [ ] See task name shown
- [ ] See task description
- [ ] See "Action Schema" JSON

### ✅ Trajectory Submission
In the "Trajectory Builder" section:
- [ ] Copy this into the text area:
```json
[{"action": "test_action", "observation": {}}]
```
- [ ] Click **📊 Grade Trajectory** button
- [ ] Wait 1-2 seconds

### ✅ Grading Results
After submission, verify:
- [ ] A new "✅ Grading Results" section appears
- [ ] See **🎯 Score** card with a number between 0 and 1
- [ ] See **⏱️ Time** metric
- [ ] See **💰 Cost** metric
- [ ] See **🌍 Carbon** metric

### ✅ Multi-Task Testing
- [ ] Switch task selector to **Task 2: Cost Minimization**
- [ ] Click **Reset Environment**
- [ ] Verify metrics reset to 0
- [ ] Submit a trajectory
- [ ] See score appear in results

- [ ] Switch to **Task 3: Multimodal Balancing**
- [ ] Click **Reset Environment**
- [ ] Submit a trajectory
- [ ] See score appear

### ✅ Reproducibility (Optional)
- [ ] Check "Use fixed seed" checkbox
- [ ] Enter seed value: `42`
- [ ] Click Reset
- [ ] Note the state values
- [ ] Click Reset again (same seed)
- [ ] Verify same state values appear
- [ ] ✅ This proves deterministic behavior

---

## Troubleshooting

### Problem: "API Disconnected" in Dashboard

**Cause:** Backend isn't running or wrong URL

**Solution:**
1. Check Terminal 1 where backend should be running
2. Verify it shows `Application startup complete`
3. In dashboard sidebar, verify URL is `http://localhost:8000`
4. Manually test: `curl http://localhost:8000/health`

### Problem: Port 8000 Already in Use

**Cause:** Another process is using port 8000

**Solution:**
```bash
# See what's using it
lsof -i :8000

# Kill it (replace PID with actual number)
kill -9 <PID>

# Try backend again
/home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Problem: Frontend Won't Start

**Cause:** Port 8501 in use or streamlit not found

**Solution:**
```bash
# Check if port is free
lsof -i :8501

# If it is, try running with explicit python:
/home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv/.venv/bin/python -m streamlit run frontend/dashboard.py --server.port=8501
```

### Problem: "Invalid JSON" Error in Dashboard

**Cause:** Malformed trajectory JSON

**Solution:**
- Use valid JSON: `[{"action": "test", "observation": {}}]`
- Not valid: `[{action: test}]` (missing quotes)
- Validate at: https://jsonlint.com/

### Problem: Trajectory Submission Doesn't Work

**Cause:** Backend error or malformed data

**Solution:**
1. Check Terminal 1 (backend) for error messages
2. Verify trajectory is valid JSON
3. Manually test with curl from Terminal 2:
```bash
curl -X POST http://localhost:8000/grader \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "trajectory": [{"action": "test", "observation": {}}]}'
```

---

## What to Verify

| Feature | Test | Expected | ✅ |
|---------|------|----------|-----|
| Backend Started | Terminal 1 shows uvicorn running | "Application startup complete" | |
| Health Endpoint | `curl .../health` | Returns {"success": true} | |
| Tasks Endpoint | `curl .../tasks` | Returns 3 tasks | |
| Reset Endpoint | `curl -X POST .../reset` | Returns step=0 | |
| Grader Endpoint | `curl -X POST .../grader` | Returns score [0-1] | |
| Dashboard Loads | Visit http://localhost:8501 | Page loads | |
| Health Status | Look at sidebar | Shows ✅ (green) | |
| Reset Button | Click it | Metrics update | |
| Task Selection | Switch tasks | Dashboard updates | |
| Trajectory Submit | Click Grade button | Score appears | |
| Metrics Display | After grading | See time/cost/carbon | |

---

## Success Indicators

You'll know everything is working when:

✅ **Terminal 1 (Backend)**
- No error messages
- Uvicorn shows "Application startup complete"
- New log entries appear when you interact with dashboard

✅ **Terminal 2 (Curl Tests)**
- All 4 curl commands return successful JSON responses
- No connection errors

✅ **Terminal 3 & Browser (Frontend)**
- Page loads without errors
- Health status shows green ✅
- Can reset and see state update
- Can submit trajectory and see score
- All 3 tasks can be tested

---

## Next Steps After Testing

### If Everything Works ✅
1. Take screenshots of dashboard
2. Test with different trajectories
3. Try the Agent Analytics page
4. Prepare for judge presentation

### If Something Fails ❌
1. Check the troubleshooting section above
2. Verify all 3 terminals are running
3. Check for port conflicts
4. Review error messages in Terminal 1

---

## Terminal Quick Reference

Save this for copy-pasting:

**Backend (Terminal 1):**
```bash
/home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend (Terminal 3):**
```bash
/home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv/.venv/bin/python -m streamlit run frontend/dashboard.py --server.port=8501
```

**Health Test (Terminal 2):**
```bash
curl http://localhost:8000/health
```

---

## Documentation Files

For more details, see:
- [QUICK_REFERENCE.sh](QUICK_REFERENCE.sh) - Copy-paste commands
- [TESTING_RESULTS.md](TESTING_RESULTS.md) - Previous test results
- [frontend/README.md](frontend/README.md) - Dashboard documentation
- [FRONTEND_SETUP.md](FRONTEND_SETUP.md) - Deployment guide

---

**Happy Testing!** 🚀
