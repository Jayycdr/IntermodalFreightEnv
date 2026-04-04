#!/usr/bin/env python3
"""
Step-by-step environment debugging and metric visualization.

Shows exactly what happens at each step of agent interaction:
- How metrics accumulate
- How scores calculate
- What signals agents receive
"""

import requests
import json
from typing import Dict, List, Any

BASE_URL = "http://localhost:8000"


class EnvironmentDebugger:
    """Debug and visualize environment state at each step."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    def print_step_breakdown(self, trajectory: List[Dict], task_id: str = "task_3_multimodal"):
        """Show step-by-step metric accumulation."""
        
        print("\n" + "="*80)
        print("STEP-BY-STEP ENVIRONMENT BREAKDOWN")
        print("="*80 + "\n")
        
        print(f"Task: {task_id}\n")
        print(f"{'Step':<6} {'Action':<30} {'Time':<10} {'Cost':<10} {'Carbon':<10}")
        print("-" * 80)
        
        step_count = 0
        accumulated_hours = 0
        accumulated_cost = 0
        accumulated_carbon = 0
        
        for step in trajectory:
            step_count += 1
            action = step.get("action", {})
            action_type = action.get("task_type", "unknown")
            path = action.get("path", [])
            
            # Simulate metric calculation (in real env, this comes from simulation)
            # For demo, we'll show the trajectory structure
            
            print(f"{step_count:<6} ", end="")
            
            # Action description
            if path:
                action_desc = f"Move via {action_type}"
            else:
                action_desc = f"Execute {action_type}"
            
            print(f"{action_desc:<30} ", end="")
            print(f"?, ?, ?")  # Real env would calculate these
        
        # Now show the actual grading result
        print("\n" + "="*80)
        print("GRADING RESULT")
        print("="*80 + "\n")
        
        resp = requests.post(
            f"{self.base_url}/grader",
            json={"trajectory": trajectory}
        )
        
        data = resp.json().get("data", {})
        metrics = data.get("metrics", {})
        
        print("📊 FINAL ACCUMULATED METRICS:")
        print(f"   Hours (time):    {metrics.get('accumulated_hours', 0):.2f}")
        print(f"   Cost ($):        ${metrics.get('accumulated_cost', 0):.2f}")
        print(f"   Carbon (kg):     {metrics.get('accumulated_carbon', 0):.2f}")
        
        print(f"\n📈 SCORES:")
        print(f"   Final Score:     {data.get('score', 0):.4f} / 1.0")
        print(f"   Efficiency:      {data.get('efficiency_score', 0):.2f} / 100.0")
        print(f"   Weighted:        {data.get('weighted_score', 0):.4f}")
        
        print(f"\n🎯 WORK PRODUCT:")
        print(f"   Cargos Delivered: {data.get('cargos_delivered', 0)}")
        print(f"   Steps Executed:   {len(trajectory)}")
    
    def show_metric_breakdown(self):
        """Show how each metric component contributes to score."""
        
        print("\n" + "="*80)
        print("METRIC COMPONENT BREAKDOWN")
        print("="*80 + "\n")
        
        print("📊 HOW METRICS ARE TRACKED:\n")
        
        print("1️⃣  ACCUMULATION DURING TRAJECTORY:")
        print("""
   Each agent action accumulates metrics:
   - Time: How long the transport takes (hours)
   - Cost: How much it costs to execute (dollars)
   - Carbon: Environmental impact (kg CO2)
        """)
        
        print("2️⃣  SCORING FORMULA (Trilemma Weighted):")
        print("""
   Raw Score = 0.5 × accumulated_hours + 0.3 × accumulated_cost + 0.2 × accumulated_carbon
   
   This means:
   - TIME has 50% importance → Agents prioritize speed (Task 1 focus)
   - COST has 30% importance → Agents optimize budget (Task 2 focus)  
   - CARBON has 20% importance → Agents consider environment (Task 3 balance)
        """)
        
        print("3️⃣  NORMALIZATION:")
        print("""
   Efficiency Score = Raw Score normalized to 0-100 scale
   Weighted Score = Normalized to 0-1 range [final score]
        """)
        
        print("4️⃣  AGENT REWARD:")
        print("""
   For each cargo delivered:
   - Score increases based on efficiency
   - Metrics (hours, cost, carbon) are minimized
   - More deliveries with less resources = higher score
        """)
    
    def show_task_specific_rewards(self):
        """Explain task-specific reward structures."""
        
        print("\n" + "="*80)
        print("TASK-SPECIFIC REWARD SIGNALS")
        print("="*80 + "\n")
        
        print("🎯 WHAT EACH TASK TEACHES:\n")
        
        print("TASK 1: TIME MINIMIZATION")
        print("""
   Objective: Minimize accumulated_hours
   Agent learns: Fast routes, direct paths, quick transitions
   Reward signal: Lower hours = higher score
   Example: Path [0→1→5] is better than [0→2→4→5]
        """)
        
        print("-" * 80)
        
        print("TASK 2: COST MINIMIZATION")
        print("""
   Objective: Minimize accumulated_cost  
   Agent learns: Cheaper routes, bulk transport, consolidation
   Reward signal: Lower cost = higher score
   Example: Rail route cheaper than air route
        """)
        
        print("-" * 80)
        
        print("TASK 3: MULTIMODAL OPTIMIZATION (Balanced Trilemma)")
        print("""
   Objective: Balance all 3 metrics (0.5×hours + 0.3×cost + 0.2×carbon)
   Agent learns: Mode selection (truck, rail, ship, air)
   Reward signal: Optimal combination = highest score
   Example: Rail for long distances (cheap+fast), truck for last-mile
   
   Unique features:
   - cargo_type: Choose transportation mode
   - split_at: Split shipments across modes
        """)
    
    def show_agent_learning_signals(self):
        """Show what reinforcement learning signals agents receive."""
        
        print("\n" + "="*80)
        print("WHAT AGENTS LEARN FROM VALUE SIGNALS")
        print("="*80 + "\n")
        
        print("🧠 LEARNING LOOP:\n")
        
        print("1. Agent observes: Task definition + Current state")
        print("2. Agent chooses: Path, mode, or strategy")
        print("3. Trajectory generated: [action_1, action_2, ..., action_N]")
        print("4. Environment evaluates: Calculates metrics + returns score")
        print("5. Agent learns: Trajectory → Score mapping")
        print("6. Agent improves: Tries different strategies next episode\n")
        
        print("📊 VALUE SIGNALS AGENTS GET:\n")
        
        print("✅ Immediate feedback:")
        print("   - Score [0-1]: Simple numeric reward")
        print("   - Metrics: Detailed breakdown of performance")
        print("   - Cargo count: Progress indicator\n")
        
        print("✅ Comparative feedback:")
        print("   - Different actions → different scores")
        print("   - Agent learns which actions are better")
        print("   - Optimization through trial-and-error\n")
        
        print("✅ Multi-objective guidance:")
        print("   - Task 1: Optimize hours")
        print("   - Task 2: Optimize cost")
        print("   - Task 3: Balance all three")
        print("   - Agent learns task-specific strategies\n")
    
    def show_success_indicators(self):
        """Show how to know if agents are learning successfully."""
        
        print("\n" + "="*80)
        print("SUCCESS INDICATORS - Is Your Agent Learning?")
        print("="*80 + "\n")
        
        print("✅ SIGNS OF SUCCESSFUL LEARNING:\n")
        
        print("1. Score Improvement:")
        print("   Episode 1 score: 0.2 → Episode 100 score: 0.8")
        print("   Indicates agent is optimizing toward target")
        
        print("\n2. Metric Reduction:")
        print("   Early episodes: hours=10, cost=500, carbon=100")
        print("   Later episodes: hours=3, cost=200, carbon=30")
        print("   Agent finding more efficient routes")
        
        print("\n3. Cargo Delivery Increase:")
        print("   Episode 1: 1 cargo delivered")
        print("   Episode 100: 10 cargos with better metrics")
        print("   Agent handling more workload efficiently")
        
        print("\n4. Convergence:")
        print("   Scores stabilize around consistent value")
        print("   Agent found good strategy (local optimum)")
        
        print("\n❌ SIGNS OF LEARNING PROBLEMS:\n")
        
        print("1. Score doesn't improve (always 0)")
        print("   → Agent not finding valid trajectories")
        print("   → Check: action_schema, path validation")
        
        print("\n2. Metrics stay zero")
        print("   → Environment not calculating metrics")
        print("   → Check: setup_network, trajectory format")
        
        print("\n3. Random performance")
        print("   → Score fluctuates wildly")
        print("   → Check: reward signal consistency")
        
        print("\n4. All tasks perform equally")
        print("   → Task-specific strategies not differentiating")
        print("   → Check: metric weights, task definitions")


def main():
    """Run environment debugging tools."""
    
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*18 + "ENVIRONMENT DEBUGGING & AGENT LEARNING SIGNALS" + " "*15 + "║")
    print("║" + " "*22 + "How Agents Learn from Your Environment" + " "*22 + "║")
    print("╚" + "="*78 + "╝")
    
    debugger = EnvironmentDebugger()
    
    # Create sample trajectory
    sample_trajectory = [
        {
            "step": 0,
            "cargo_id": 1,
            "action": {"task_type": "task_1_time", "path": [0, 1, 5]},
            "state": {"step": 0},
            "reward": 0.8,
            "done": False,
            "info": {}
        },
        {
            "step": 1,
            "cargo_id": 1,
            "action": {"task_type": "task_1_time", "path": [1, 5]},
            "state": {"step": 1},
            "reward": 0.9,
            "done": True,
            "info": {}
        }
    ]
    
    debugger.print_step_breakdown(sample_trajectory, "task_1_time")
    debugger.show_metric_breakdown()
    debugger.show_task_specific_rewards()
    debugger.show_agent_learning_signals()
    debugger.show_success_indicators()
    
    print("\n" + "="*80)
    print("✅ YOUR ENVIRONMENT PROVIDES CLEAR LEARNING SIGNALS FOR AGENTS")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
