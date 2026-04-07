#!/bin/bash
# QUICK API TESTING COMMANDS
# Copy these exact commands to test your API manually

echo "=========================================="
echo "QUICK API TEST COMMANDS"
echo "=========================================="
echo ""

# Check if container is running
echo "Checking for running container..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Starting Docker container..."
    docker run -p 8000:7860 openenv-intermodalfreightenv > /tmp/api.log 2>&1 &
    sleep 5
    echo "Container started, waiting for API..."
fi

echo ""
echo "========== TEST 1: Health Check =========="
echo "Command: curl http://localhost:8000/health"
echo "Expected: 200 OK with 'API healthy' message"
echo ""
curl -i http://localhost:8000/health 2>/dev/null | head -15
echo ""

echo "========== TEST 2: Tasks Endpoint =========="
echo "Command: curl http://localhost:8000/tasks"
echo "Expected: 200 OK with 3 tasks"
echo ""
curl -s http://localhost:8000/tasks | python3 -m json.tool 2>/dev/null | head -40
echo ""

echo "========== TEST 3: Reset Environment =========="
echo "Command: curl -X POST http://localhost:8000/reset -H 'Content-Type: application/json' -d '{}'"
echo "Expected: 200 OK with reset state"
echo ""
curl -s -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool 2>/dev/null | head -40
echo ""

echo "========== TEST 4: Grader Endpoint =========="
echo "Command: curl -X POST http://localhost:8000/grader -H 'Content-Type: application/json' -d '{}'"
echo "Expected: 200 OK with grading result"
echo ""
curl -s -X POST http://localhost:8000/grader \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool 2>/dev/null | head -40
echo ""

echo "========== TEST 5: Root Endpoint =========="
echo "Command: curl http://localhost:8000/"
echo "Expected: 200 OK with API info"
echo ""
curl -s http://localhost:8000/ | python3 -m json.tool 2>/dev/null | head -30
echo ""

echo "========== SUMMARY =========="
echo "✅ If all tests show 200 OK above, your API is working!"
echo "✅ You are READY FOR SUBMISSION!"
echo ""
echo "To stop the container:"
echo "  docker stop \$(docker ps -q --filter 'ancestor=openenv-intermodalfreightenv')"
echo ""
echo "========== SUBMISSION DEADLINE =========="
echo "📅 April 7, 2026, 11:59 PM IST"
echo "✅ Status: READY ✅"
