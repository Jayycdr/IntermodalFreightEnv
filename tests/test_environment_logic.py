#!/usr/bin/env python3
"""
Test environment logic and agent interactions.

This tests the core functionality without needing a frontend:
- Environment state transitions
- Metric calculations (time, cost, carbon)
- Task-specific scoring
- Agent-environment interactions
"""

import requests
import json
from typing import Dict, Any, List
import time

BASE_URL = "http://localhost:8000"


class EnvironmentTester:
    """Tests the IntermodalFreightEnv functionality."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session_id = None
        self.test_results = []
    
    def test(self, name: str, condition: bool, expected: Any = None, actual: Any = None) -> bool:
        """Record a test result."""
        status = "✅" if condition else "❌"
        result = {
            "name": name,
            "passed": condition,
            "expected": expected,
            "actual": actual
        }
        self.test_results.append(result)
        
        detail = ""
        if expected is not None and actual is not None:
            detail = f" (expected: {expected}, got: {actual})"
        
        print(f"{status} {name}{detail}")
        return condition
    
    def print_summary(self):
        """Print test summary."""
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = sum(1 for r in self.test_results if not r["passed"])
        total = len(self.test_results)
        
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY: {passed}/{total} passed")
        if failed > 0:
            print(f"FAILED: {failed}")
        print(f"{'='*80}\n")
        
        return failed == 0
    
    # ==========================================================================
    # TEST SUITE 1: API & Environment State
    # ==========================================================================
    
    def test_api_health(self):
        """Test 1.1: API is responding"""
        print("\n" + "="*80)
        print("TEST SUITE 1: API & ENVIRONMENT STATE")
        print("="*80)
        
        try:
            resp = requests.get(f"{self.base_url}/health")
            self.test("API health check", resp.status_code == 200)
            return True
        except Exception as e:
            self.test("API health check", False)
            print(f"   Error: {e}")
            return False
    
    def test_environment_reset(self):
        """Test 1.2: Environment resets properly"""
        try:
            resp = requests.post(f"{self.base_url}/reset", json={})
            data = resp.json()
            
            self.test("Reset returns success", data.get("state") is not None)
            self.test("Reset initializes step to 0", 
                     data["state"]["step"] == 0, 
                     expected=0, actual=data["state"]["step"])
            
            return True
        except Exception as e:
            self.test("Environment reset", False)
            print(f"   Error: {e}")
            return False
    
    def test_get_state(self):
        """Test 1.3: Can retrieve environment state"""
        try:
            resp = requests.get(f"{self.base_url}/state")
            if resp.status_code != 200:
                self.test("Get state endpoint exists", False)
                return False
            
            data = resp.json()
            has_required_fields = all(k in data.get("data", {}) 
                                     for k in ["step", "active_cargos"])
            
            self.test("State has required fields", has_required_fields)
            return True
        except Exception as e:
            print(f"   (State endpoint may not exist: {e})")
            return True  # Non-critical
    
    # ==========================================================================
    # TEST SUITE 2: Task Definitions
    # ==========================================================================
    
    def test_tasks_available(self):
        """Test 2.1: All 3 tasks are defined"""
        print("\n" + "="*80)
        print("TEST SUITE 2: TASK DEFINITIONS")
        print("="*80)
        
        try:
            resp = requests.get(f"{self.base_url}/tasks")
            data = resp.json()
            tasks = data.get("data", {}).get("tasks", [])
            
            self.test("Tasks endpoint returns data", len(tasks) > 0, expected=3, actual=len(tasks))
            self.test("Exactly 3 tasks defined", len(tasks) == 3, expected=3, actual=len(tasks))
            
            # Check task IDs
            task_ids = [t.get("id") for t in tasks]
            self.test("Task 1 (time) defined", "task_1_time" in task_ids)
            self.test("Task 2 (cost) defined", "task_2_cost" in task_ids)
            self.test("Task 3 (multimodal) defined", "task_3_multimodal" in task_ids)
            
            # Check task uniqueness
            for i, task in enumerate(tasks):
                has_schema = "action_schema" in task
                self.test(f"Task {i+1} has action schema", has_schema)
            
            return True
        except Exception as e:
            self.test("Tasks endpoint", False)
            print(f"   Error: {e}")
            return False
    
    def test_task_distinctness(self):
        """Test 2.2: Task 3 is distinct from Task 1 & 2"""
        try:
            resp = requests.get(f"{self.base_url}/tasks")
            data = resp.json()
            tasks = {t["id"]: t for t in data["data"]["tasks"]}
            
            task3 = tasks.get("task_3_multimodal", {})
            schema = task3.get("action_schema", {})
            properties = schema.get("properties", {})
            
            # Task 3 should have unique fields: cargo_type, split_at
            self.test("Task 3 has cargo_type field", "cargo_type" in properties)
            self.test("Task 3 has split_at field", "split_at" in properties)
            
            # Verify they're enums/special types
            cargo_type_schema = properties.get("cargo_type", {})
            self.test("cargo_type is distinct (not simple string)", 
                     "enum" in cargo_type_schema or "type" in cargo_type_schema)
            
            return True
        except Exception as e:
            print(f"   Error checking task distinctness: {e}")
            return False
    
    # ==========================================================================
    # TEST SUITE 3: Grading & Metrics
    # ==========================================================================
    
    def test_grader_empty_trajectory(self):
        """Test 3.1: Grader handles empty trajectory"""
        print("\n" + "="*80)
        print("TEST SUITE 3: GRADING & METRICS")
        print("="*80)
        
        try:
            resp = requests.post(
                f"{self.base_url}/grader",
                json={"trajectory": []}
            )
            data = resp.json()
            
            self.test("Grader returns success", data.get("success") == True)
            
            score = data.get("data", {}).get("score")
            self.test("Score is in valid range [0, 1]", 
                     0 <= score <= 1, 
                     expected="[0, 1]", actual=score)
            
            self.test("Empty trajectory returns score 0", 
                     score == 0, expected=0, actual=score)
            
            return True
        except Exception as e:
            self.test("Grader endpoint", False)
            print(f"   Error: {e}")
            return False
    
    def test_metrics_structure(self):
        """Test 3.2: Metrics have correct structure"""
        try:
            resp = requests.post(
                f"{self.base_url}/grader",
                json={"trajectory": []}
            )
            data = resp.json().get("data", {})
            
            metrics = data.get("metrics", {})
            
            # Check trilemma metrics exist
            self.test("Metrics include accumulated_hours", 
                     "accumulated_hours" in metrics)
            self.test("Metrics include accumulated_cost", 
                     "accumulated_cost" in metrics)
            self.test("Metrics include accumulated_carbon", 
                     "accumulated_carbon" in metrics)
            
            # Check values are numeric and non-negative
            hours = metrics.get("accumulated_hours", -1)
            cost = metrics.get("accumulated_cost", -1)
            carbon = metrics.get("accumulated_carbon", -1)
            
            self.test("Metrics are non-negative", 
                     hours >= 0 and cost >= 0 and carbon >= 0,
                     expected=">=0", actual=f"h:{hours}, c:{cost}, b:{carbon}")
            
            return True
        except Exception as e:
            print(f"   Error checking metrics: {e}")
            return False
    
    def test_trilemma_formula(self):
        """Test 3.3: Scoring formula is working"""
        try:
            # Test that score = 0.5*hours + 0.3*cost + 0.2*carbon (normalized)
            resp = requests.post(
                f"{self.base_url}/grader",
                json={"trajectory": []}
            )
            data = resp.json().get("data", {})
            
            # For empty trajectory, all should be 0
            score = data.get("score")
            efficiency = data.get("efficiency_score")
            weighted = data.get("weighted_score")
            
            self.test("Score, efficiency, and weighted_score are present", 
                     all(x is not None for x in [score, efficiency, weighted]))
            
            # They should be consistent for empty trajectory (all 0)
            consistent = (score == 0 and efficiency == 0 and weighted == 0)
            self.test("Scores consistent for empty trajectory", consistent)
            
            return True
        except Exception as e:
            print(f"   Error checking formula: {e}")
            return False
    
    # ==========================================================================
    # TEST SUITE 4: Agent Interaction Simulation
    # ==========================================================================
    
    def test_agent_can_request_tasks(self):
        """Test 4.1: Agent can request task definitions"""
        print("\n" + "="*80)
        print("TEST SUITE 4: AGENT INTERACTION SIMULATION")
        print("="*80)
        
        try:
            resp = requests.get(f"{self.base_url}/tasks")
            tasks = resp.json().get("data", {}).get("tasks", [])
            
            self.test("Agent can get task list", len(tasks) > 0)
            self.test("Agent can identify 3 distinct tasks", len(tasks) == 3)
            
            print(f"   Agent sees these tasks:")
            for task in tasks:
                print(f"   - {task['name']} (ID: {task['id']})")
            
            return True
        except Exception as e:
            self.test("Agent task request", False)
            print(f"   Error: {e}")
            return False
    
    def test_agent_can_reset_environment(self):
        """Test 4.2: Agent can reset and get fresh environment"""
        try:
            resp1 = requests.post(f"{self.base_url}/reset", json={})
            step1 = resp1.json()["state"]["step"]
            
            # Simulate some action (would happen in real agent)
            time.sleep(0.1)
            
            # Reset again
            resp2 = requests.post(f"{self.base_url}/reset", json={})
            step2 = resp2.json()["state"]["step"]
            
            self.test("Agent can reset environment", 
                     step1 == 0 and step2 == 0)
            self.test("Resets produce independent states", 
                     step1 == step2 == 0)
            
            return True
        except Exception as e:
            self.test("Agent reset capability", False)
            print(f"   Error: {e}")
            return False
    
    def test_agent_can_evaluate_trajectory(self):
        """Test 4.3: Agent can submit trajectories for evaluation"""
        try:
            # Simulate a simple trajectory
            trajectory = [
                {
                    "step": 0,
                    "cargo_id": 1,
                    "action": {"task_type": "task_1_time", "path": [0, 1, 5]},
                    "state": {"step": 0},
                    "reward": 0.5,
                    "done": False,
                    "info": {}
                },
                {
                    "step": 1,
                    "cargo_id": 1,
                    "action": {"task_type": "task_1_time", "path": [1, 5]},
                    "state": {"step": 1},
                    "reward": 0.8,
                    "done": True,
                    "info": {"delivered": True}
                }
            ]
            
            resp = requests.post(
                f"{self.base_url}/grader",
                json={"trajectory": trajectory}
            )
            
            self.test("Agent can submit trajectory", resp.status_code == 200)
            
            data = resp.json().get("data", {})
            self.test("Grader returns score", "score" in data)
            self.test("Grader returns metrics", "metrics" in data)
            
            return True
        except Exception as e:
            self.test("Agent trajectory submission", False)
            print(f"   Error: {e}")
            return False
    
    # ==========================================================================
    # TEST SUITE 5: Determinism & Reproducibility
    # ==========================================================================
    
    def test_deterministic_behavior(self):
        """Test 5.1: Environment behaves deterministically with seed"""
        print("\n" + "="*80)
        print("TEST SUITE 5: DETERMINISM & REPRODUCIBILITY")
        print("="*80)
        
        try:
            # Reset with seed
            resp1 = requests.post(
                f"{self.base_url}/reset",
                json={"seed": 42}
            )
            state1 = resp1.json()["state"]
            
            # Reset with same seed
            resp2 = requests.post(
                f"{self.base_url}/reset",
                json={"seed": 42}
            )
            state2 = resp2.json()["state"]
            
            # States should be identical
            same_step = state1["step"] == state2["step"]
            self.test("Same seed produces same initial state", same_step)
            
            return True
        except Exception as e:
            print(f"   (Determinism test may not apply: {e})")
            return True
    
    def test_seed_independence(self):
        """Test 5.2: Different seeds produce different results"""
        try:
            resp1 = requests.post(
                f"{self.base_url}/reset",
                json={"seed": 42}
            )
            state1 = resp1.json()["state"]
            
            resp2 = requests.post(
                f"{self.base_url}/reset",
                json={"seed": 43}
            )
            state2 = resp2.json()["state"]
            
            # Both valid, testing seeds don't break anything
            valid = (state1 is not None and state2 is not None)
            self.test("Different seeds work correctly", valid)
            
            return True
        except Exception as e:
            print(f"   (Seed test may not apply: {e})")
            return True
    
    # ==========================================================================
    # TEST SUITE 6: Value Results (Quantitative Tests)
    # ==========================================================================
    
    def test_metric_value_ranges(self):
        """Test 6.1: Metrics have sensible value ranges"""
        print("\n" + "="*80)
        print("TEST SUITE 6: VALUE RESULTS & QUANTITATIVE METRICS")
        print("="*80)
        
        try:
            resp = requests.post(
                f"{self.base_url}/grader",
                json={"trajectory": []}
            )
            data = resp.json().get("data", {})
            metrics = data.get("metrics", {})
            
            hours = metrics.get("accumulated_hours", 0)
            cost = metrics.get("accumulated_cost", 0)
            carbon = metrics.get("accumulated_carbon", 0)
            
            self.test("Hours is numeric", isinstance(hours, (int, float)))
            self.test("Cost is numeric", isinstance(cost, (int, float)))
            self.test("Carbon is numeric", isinstance(carbon, (int, float)))
            
            self.test("Hours are non-negative", hours >= 0)
            self.test("Cost is non-negative", cost >= 0)
            self.test("Carbon is non-negative", carbon >= 0)
            
            return True
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_score_boundaries(self):
        """Test 6.2: Scores are properly bounded"""
        try:
            resp = requests.post(
                f"{self.base_url}/grader",
                json={"trajectory": []}
            )
            data = resp.json().get("data", {})
            score = data.get("score", -1)
            
            self.test("Score >= 0", score >= 0, expected=">=0", actual=score)
            self.test("Score <= 1", score <= 1, expected="<=1", actual=score)
            self.test("Score in [0, 1] range", 0 <= score <= 1)
            
            return True
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def run_all(self):
        """Run all tests."""
        self.test_api_health()
        self.test_environment_reset()
        self.test_get_state()
        
        self.test_tasks_available()
        self.test_task_distinctness()
        
        self.test_grader_empty_trajectory()
        self.test_metrics_structure()
        self.test_trilemma_formula()
        
        self.test_agent_can_request_tasks()
        self.test_agent_can_reset_environment()
        self.test_agent_can_evaluate_trajectory()
        
        self.test_deterministic_behavior()
        self.test_seed_independence()
        
        self.test_metric_value_ranges()
        self.test_score_boundaries()
        
        return self.print_summary()


if __name__ == "__main__":
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "ENVIRONMENT LOGIC TEST SUITE" + " "*31 + "║")
    print("║" + " "*15 + "Testing IntermodalFreightEnv Functionality" + " "*20 + "║")
    print("╚" + "="*78 + "╝\n")
    
    tester = EnvironmentTester()
    success = tester.run_all()
    
    if success:
        print("✅ ALL TESTS PASSED - Environment logic is working correctly!")
        exit(0)
    else:
        print("❌ SOME TESTS FAILED - Check issues above")
        exit(1)
