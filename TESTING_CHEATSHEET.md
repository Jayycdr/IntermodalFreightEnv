# 🧪 MANUAL TESTING - CHEAT SHEET

## 3-Terminal Setup

### Terminal 1: BACKEND (KEEP RUNNING)
```bash
/home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Wait for:** `Application startup complete`

---

### Terminal 2: TEST ENDPOINTS
```bash
# Test 1: Health
curl http://localhost:8000/health

# Test 2: Tasks
curl http://localhost:8000/tasks | python3 -m json.tool | head -50

# Test 3: Reset
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1}'

# Test 4: Grade
curl -X POST http://localhost:8000/grader \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "trajectory": [{"action": "test", "observation": {}}]}'
```

**Expected:** JSON responses with no errors

---

### Terminal 3: FRONTEND
```bash
/home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv/.venv/bin/python -m streamlit run frontend/dashboard.py --server.port=8501
```

**Then:** Open browser to **http://localhost:8501**

---

## Dashboard Testing Checklist

- [ ] Health shows ✅ (green)
- [ ] Select Task 1 → Reset → See metrics
- [ ] Submit trajectory → See score
- [ ] Try Task 2 and Task 3
- [ ] Test seed reproducibility (optional)

---

## Success = All Tests Pass ✅

See [MANUAL_TESTING.md](MANUAL_TESTING.md) for detailed guide
