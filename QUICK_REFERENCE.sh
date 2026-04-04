#!/bin/bash
# Quick Reference: Copy-paste commands for manual testing

# ===== TERMINAL 1: START BACKEND =====
# Copy and paste this entire line into Terminal 1:

/home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


# ===== TERMINAL 2: TEST ENDPOINTS (After backend starts) =====

# Test 1: Health Check
curl -i http://localhost:8000/health

# Test 2: Get Tasks
curl -i http://localhost:8000/tasks | python3 -m json.tool | head -50

# Test 3: Reset Environment
curl -i -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1}'

# Test 4: Grade Trajectory
curl -i -X POST http://localhost:8000/grader \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "trajectory": [{"action": "move", "observation": {}}]}'


# ===== TERMINAL 3: START FRONTEND =====
# Copy and paste this entire line into Terminal 3:

/home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv/.venv/bin/python -m streamlit run frontend/dashboard.py --server.port=8501

# Then open browser to: http://localhost:8501


# ===== TROUBLESHOOTING COMMANDS =====

# Check what's using port 8000:
lsof -i :8000

# Kill process using port 8000 (replace PID with actual number):
kill -9 <PID>

# Check if ports are free:
lsof -i :8000 && lsof -i :8501

# View backend logs:
# (Look in Terminal 1 where backend is running)

# Validate JSON in curl commands:
# Use https://jsonlint.com/ or: python3 -m json.tool <<< '{"key": "value"}'
