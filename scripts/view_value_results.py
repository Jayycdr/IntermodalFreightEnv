#!/usr/bin/env python3
"""
View detailed VALUE RESULTS from the environment.

This shows exactly what agents see and learn from trajectories:
- Metric values (time, cost, carbon)
- Score calculations
- Task performance comparisons
"""

import requests
import json
from typing import Dict, List, Any
import statistics

BASE_URL = "http://localhost:8000"


class ValueResultsViewer:
    """View and analyze value results from the environment."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    def print_header(self, text: str):
        """Print formatted header."""
        print(f"\n{'='*80}")
        print(f"{text:^80}")
        print(f"{'='*80}\n")
    
    def get_tasks(self) -> Dict:
        """Get all task definitions."""
        resp = requests.get(f"{self.base_url}/tasks")
        return resp.json()
    
    def grade_trajectory(self, trajectory: List[Dict]) -> Dict:
        """Grade a trajectory and return metrics."""
        resp = requests.post(
            f"{self.base_url}/grader",
            json={"trajectory": trajectory}
        )
        return resp.json()
    
    # ========================================================================
    # VALUE RESULT VIEWERS
    # ========================================================================
    
    def view_task_definitions(self):
        """Show what each task expects agents to optimize."""
        self.print_header("TASK DEFINITIONS - What Agents Optimize For")
        
        data = self.get_tasks()
        tasks = data.get("data", {}).get("tasks", [])
        
        for i, task in enumerate(tasks, 1):
            print(f"📌 TASK {i}: {task['name']}")
            print(f"   ID: {task['id']}")
            print(f"   Objective: {task.get('objective', 'N/A')}")
            print(f"   Description: {task.get('description', 'N/A')}")
            
            schema = task.get("action_schema", {})
            props = schema.get("properties", {})
            
            if props:
                print(f"   Action Parameters:")
                for param_name, param_schema in props.items():
                    if param_name != "task_type":  # Skip task_type
                        param_type = param_schema.get("type", "unknown")
                        print(f"      - {param_name}: {param_type}")
                        if "enum" in param_schema:
                            print(f"        (options: {param_schema['enum']})")
            print()
    
    def view_empty_trajectory_metrics(self):
        """Show metrics for empty (no action) trajectory."""
        self.print_header("METRICS FOR EMPTY TRAJECTORY (No Agent Action)")
        
        result = self.grade_trajectory([])
        data = result.get("data", {})
        metrics = data.get("metrics", {})
        
        print("📊 METRIC VALUES:")
        print(f"   Accumulated Hours (time):   {metrics.get('accumulated_hours', 0):.2f}")
        print(f"   Accumulated Cost ($):       ${metrics.get('accumulated_cost', 0):.2f}")
        print(f"   Accumulated Carbon (kg):    {metrics.get('accumulated_carbon', 0):.2f} kg")
        
        print(f"\n📈 SCORE RESULTS:")
        print(f"   Raw Score:              {data.get('score', 0):.4f}")
        print(f"   Efficiency Score:       {data.get('efficiency_score', 0):.2f}")
        print(f"   Weighted Score:         {data.get('weighted_score', 0):.4f}")
        
        print(f"\n🎯 OTHER METRICS:")
        print(f"   Cargos Delivered:       {data.get('cargos_delivered', 0)}")
        print(f"   Task Type:              {data.get('task_type', 'N/A')}")
        
        print(f"\nℹ️  INTERPRETATION:")
        print(f"   Empty trajectory = no actions taken")
        print(f"   All metrics = 0 (no progress)")
        print(f"   Score = 0 (no benefit)")
    
    def view_sample_trajectory_metrics(self):
        """Show metrics for a sample trajectory with agent action."""
        self.print_header("METRICS FOR SAMPLE TRAJECTORY (With Agent Action)")
        
        # Create a sample trajectory with multiple steps
        trajectory = [
            {
                "step": 0,
                "cargo_id": 1,
                "action": {
                    "task_type": "task_1_time",
                    "cargo_id": 1,
                    "path": [0, 1, 5]
                },
                "state": {"step": 0, "location": 0},
                "reward": 0.8,
                "done": False,
                "info": {"action": "move_cargo"}
            },
            {
                "step": 1,
                "cargo_id": 1,
                "action": {
                    "task_type": "task_1_time",
                    "cargo_id": 1,
                    "path": [1, 5]
                },
                "state": {"step": 1, "location": 1},
                "reward": 0.9,
                "done": False,
                "info": {"action": "continue_transport"}
            },
            {
                "step": 2,
                "cargo_id": 1,
                "action": {
                    "task_type": "task_1_time",
                    "cargo_id": 1,
                    "path": [5]
                },
                "state": {"step": 2, "location": 5},
                "reward": 1.0,
                "done": True,
                "info": {"delivered": True}
            }
        ]
        
        result = self.grade_trajectory(trajectory)
        data = result.get("data", {})
        metrics = data.get("metrics", {})
        
        print("📊 TRAJECTORY SUMMARY:")
        print(f"   Steps executed:         {len(trajectory)}")
        print(f"   Cargo delivered:        {'Yes' if data.get('cargos_delivered') > 0 else 'No'}")
        print(f"   Task type:              {data.get('task_type', 'N/A')}")
        
        print(f"\n📊 METRIC VALUES:")
        print(f"   Accumulated Hours:      {metrics.get('accumulated_hours', 0):.2f}")
        print(f"   Accumulated Cost:       ${metrics.get('accumulated_cost', 0):.2f}")
        print(f"   Accumulated Carbon:     {metrics.get('accumulated_carbon', 0):.2f} kg")
        
        print(f"\n📈 SCORE RESULTS:")
        print(f"   Raw Score:              {data.get('score', 0):.4f}")
        print(f"   Efficiency Score:       {data.get('efficiency_score', 0):.2f}")
        print(f"   Weighted Score:         {data.get('weighted_score', 0):.4f}")
        
        print(f"   Trilemma Formula:")
        print(f"      = 0.5 × hours + 0.3 × cost + 0.2 × carbon")
        print(f"      = 0.5 × {metrics.get('accumulated_hours', 0):.2f} + 0.3 × {metrics.get('accumulated_cost', 0):.2f} + 0.2 × {metrics.get('accumulated_carbon', 0):.2f}")
        
        print(f"\nℹ️  INTERPRETATION:")
        print(f"   Higher score = better performance (optimizing trilemma)")
        print(f"   Agent delivery = +points for cargos_delivered")
        print(f"   Efficient routes = lower metrics = higher score")
    
    def view_comparison(self):
        """Compare different trajectory strategies."""
        self.print_header("STRATEGY COMPARISON - How Agent Choices Affect Metrics")
        
        # Strategy 1: Fast route (high time = lower time priority)
        fast_trajectory = [
            {
                "step": i,
                "cargo_id": 1,
                "action": {"task_type": "task_1_time", "path": [0, 5]},
                "state": {"step": i},
                "reward": 1.0,
                "done": (i == 0),
                "info": {"route": "direct", "distance": 1}
            }
            for i in range(1)
        ]
        
        # Strategy 2: Cheap route (low cost)
        cheap_trajectory = [
            {
                "step": i,
                "cargo_id": 1,
                "action": {"task_type": "task_2_cost", "path": [0, 2, 4, 5]},
                "state": {"step": i},
                "reward": 0.85,
                "done": (i == 2),
                "info": {"route": "economical", "transfers": 2}
            }
            for i in range(3)
        ]
        
        # Grade both
        fast_result = self.grade_trajectory(fast_trajectory)
        cheap_result = self.grade_trajectory(cheap_trajectory)
        
        fast_data = fast_result.get("data", {})
        cheap_data = cheap_result.get("data", {})
        
        fast_metrics = fast_data.get("metrics", {})
        cheap_metrics = cheap_data.get("metrics", {})
        
        print("🔄 COMPARISON TABLE:\n")
        print(f"{'Metric':<30} {'Fast Route':<20} {'Cheap Route':<20}")
        print("-" * 70)
        print(f"{'Hours spent':<30} {fast_metrics.get('accumulated_hours', 0):<20.2f} {cheap_metrics.get('accumulated_hours', 0):<20.2f}")
        print(f"{'Cost ($)':<30} {fast_metrics.get('accumulated_cost', 0):<20.2f} {cheap_metrics.get('accumulated_cost', 0):<20.2f}")
        print(f"{'Carbon (kg)':<30} {fast_metrics.get('accumulated_carbon', 0):<20.2f} {cheap_metrics.get('accumulated_carbon', 0):<20.2f}")
        print(f"{'Score (0-1)':<30} {fast_data.get('score', 0):<20.4f} {cheap_data.get('score', 0):<20.4f}")
        
        print(f"\n📊 ANALYSIS:")
        fast_score = fast_data.get('score', 0)
        cheap_score = cheap_data.get('score', 0)
        
        if fast_score > cheap_score:
            print(f"   ✅ Fast route is better for this task")
            print(f"      Score advantage: {(fast_score - cheap_score):.4f}")
        elif cheap_score > fast_score:
            print(f"   ✅ Cheap route is better for this task")
            print(f"      Score advantage: {(cheap_score - fast_score):.4f}")
        else:
            print(f"   ⚖️  Both routes perform equally")
    
    def view_scoring_sensitivity(self):
        """Show how metrics affect scoring."""
        self.print_header("SCORING SENSITIVITY - How Changes Affect Score")
        
        print("🎯 TRILEMMA WEIGHTS (Formula: Score = 0.5×H + 0.3×C + 0.2×B):\n")
        
        print("Impact of each metric on score:")
        print("   - Hours (Time):    50% weight → Big impact on score")
        print("   - Cost (Money):    30% weight → Medium impact")
        print("   - Carbon (Env):    20% weight → Lower impact")
        
        print("\n📈 Example impact calculations:")
        print("   If you reduce 1 hour:     score += 0.5")
        print("   If you reduce 1$ cost:   score += 0.3")
        print("   If you reduce 1kg carbon: score += 0.2")
        
        print("\n💡 Agent learning implications:")
        print("   1. Agents will prioritize TIME optimization (50%)")
        print("   2. Then optimize COST (30%)")
        print("   3. Carbon is secondary objective (20%)")
        print("   4. Different task priorities (Task1=time, Task2=cost, Task3=balanced)")
    
    def view_environment_health_check(self):
        """Check environment is functioning properly."""
        self.print_header("ENVIRONMENT HEALTH CHECK")
        
        checks = {
            "API responding": False,
            "Tasks defined": False,
            "Grader working": False,
            "Metrics calculating": False,
            "Scores in range": False
        }
        
        # Check 1: API
        try:
            resp = requests.get(f"{self.base_url}/health")
            checks["API responding"] = resp.status_code == 200
        except:
            pass
        
        # Check 2: Tasks
        try:
            resp = requests.get(f"{self.base_url}/tasks")
            tasks = resp.json().get("data", {}).get("tasks", [])
            checks["Tasks defined"] = len(tasks) == 3
        except:
            pass
        
        # Check 3: Grader
        try:
            resp = requests.post(f"{self.base_url}/grader", json={"trajectory": []})
            checks["Grader working"] = resp.status_code == 200
        except:
            pass
        
        # Check 4 & 5: Metrics & Scores
        try:
            result = self.grade_trajectory([])
            data = result.get("data", {})
            metrics = data.get("metrics", {})
            score = data.get("score", -1)
            
            checks["Metrics calculating"] = all(k in metrics for k in 
                                               ["accumulated_hours", "accumulated_cost", "accumulated_carbon"])
            checks["Scores in range"] = 0 <= score <= 1
        except:
            pass
        
        print("✅ ENVIRONMENT STATUS:\n")
        for check, status in checks.items():
            symbol = "✅" if status else "❌"
            print(f"   {symbol} {check}")
        
        all_ok = all(checks.values())
        if all_ok:
            print(f"\n🎉 Environment is FULLY OPERATIONAL")
            print(f"   Agents can learn and train in this environment!")
        else:
            print(f"\n⚠️  Some issues detected - agents may not learn properly")


def main():
    """Run all value result viewers."""
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "VALUE RESULTS & METRICS VIEWER" + " "*28 + "║")
    print("║" + " "*15 + "Understanding What Your Agents See & Learn" + " "*21 + "║")
    print("╚" + "="*78 + "╝")
    
    viewer = ValueResultsViewer()
    
    # View all information
    viewer.view_task_definitions()
    viewer.view_empty_trajectory_metrics()
    viewer.view_sample_trajectory_metrics()
    viewer.view_comparison()
    viewer.view_scoring_sensitivity()
    viewer.view_environment_health_check()
    
    print("\n" + "="*80)
    print("✅ SUMMARY: Your environment is providing clear value signals to agents")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
