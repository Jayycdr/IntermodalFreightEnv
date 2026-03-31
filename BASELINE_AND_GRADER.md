# Evaluation & Baselines: Grader and Baseline Agents

## Overview

This document describes the **Evaluation & Baselines** layer of the IntermodalFreightEnv project. This layer provides:

1. **Grader** (`app/api/grader.py`): Evaluates agent trajectories using the weighted formula
2. **Baseline Agents** (`baseline/agent.py`): Three agent types for proof-of-work benchmarking
3. **Baseline Runner** (`baseline/run_baseline.py`): Orchestrates experiments and comparisons

## Weighted Scoring Formula

The evaluation formula balances three objectives (trilemma):

$$\text{Score} = 0.5 \times \text{accumulated\_hours} + 0.3 \times \text{accumulated\_cost} + 0.2 \times \text{accumulated\_carbon}$$

**Interpretation:**
- **0.5 weight on time**: Transportation efficiency is the primary objective
- **0.3 weight on cost**: Economic efficiency is secondary
- **0.2 weight on carbon**: Environmental impact is also important but tertiary

The grader converts this raw score into an efficiency score (0-100) factoring in:
- Low weighted metric values (favorable)
- High cargo delivery counts (favorable)
- Low step counts relative to deliveries (favorable)

## Grader (`app/api/grader.py`)

### Key Classes

#### `TrilemmaMetrics`
Accumulates the three dimensions of the trilemma:
```python
metrics = TrilemmaMetrics()
metrics.add(hours=2.5, cost=150.0, carbon=10.5)
```

#### `TrajectoryStep`
Represents a single step in an agent's trajectory:
```python
step = TrajectoryStep(
    step=0,
    cargo_id=1,
    action={"task_type": "task_1_time", "cargo_id": 1, "path": ["A", "B"]},
    state={"network": {...}, "disabled_nodes": []},
    reward=5.0,
    done=False,
    info={"trilemma": {...}, "completed_cargos": 1}
)
```

#### `EvaluationResult`
Complete evaluation output:
```python
result = EvaluationResult(
    task_type=TaskType.TASK_3_MULTIMODAL,
    weighted_score=156.2,          # Raw weighted score (lower is better)
    raw_metrics=metrics,            # Accumulated trilemma values
    task_specific_score=10.5,       # Carbon for Task 3
    cargos_delivered=2,
    num_steps=25,
    trajectory_length=25,
    efficiency_score=78.5,          # 0-100 normalized score
    feedback="Task: task_3_multimodal | Efficiency: 78.5/100 | ..."
)
```

#### `Grader` Class

**Main Methods:**

1. **`load_trajectory(steps)`** - Load trajectory from list of step dicts
2. **`evaluate(task_type)`** - Evaluate loaded trajectory
3. **`evaluate_multiple_trajectories(trajectories)`** - Evaluate multiple agent trajectories
4. **`compare_agents(trajectories)`** - Compare agents and rank them

**Example Usage:**

```python
from app.api.grader import Grader, TaskType

grader = Grader()

# Load trajectory from agent
grader.load_trajectory(agent_trajectory)

# Evaluate
result = grader.evaluate(task_type=TaskType.TASK_1_TIME)

# Access results
print(f"Efficiency: {result.efficiency_score:.1f}")
print(f"Weighted Score: {result.weighted_score:.2f}")
print(f"Deliveries: {result.cargos_delivered}")
```

## Baseline Agents (`baseline/agent.py`)

### Agent Architecture

All agents inherit from `BaseAgent` and interact with the API:

```
BaseAgent (abstract)
├── RandomAgent
├── GreedyAgent
└── DijkstraAgent
```

### BaseAgent

Abstract base class with common functionality:

**Key Methods:**
- `select_action(state)` - Abstract; implemented by subclasses
- `record_step(...)` - Records trajectory step
- `get_trajectory()` - Returns full trajectory
- `reset()` - Clears trajectory for new episode
- `_get_available_edges(state)` - Filters disabled edges/nodes from state
- `_get_edge_weight(edge, weight_type)` - Gets edge weight for optimization objective

### 1. RandomAgent

**Strategy:** Randomly selects among available (non-disrupted) edges.

**Use Case:** Baseline for comparison; shows random performance.

**Example:**
```python
agent = RandomAgent(
    agent_id="random_1",
    api_url="http://localhost:8000"
)

state = requests.get("http://localhost:8000/state").json()
action = agent.select_action(state)
# Output: {"task_type": "task_1_time", "cargo_id": 0, "path": ["A", "B"]}
```

### 2. GreedyAgent

**Strategy:** Selects the single edge with minimum weight (cost/time/carbon).

**Parameters:**
- `weight_type`: "time", "cost", or "carbon"

**Use Case:** Local optimization; shows single-edge greedy performance.

**Example:**
```python
# Minimize cost
agent = GreedyAgent(
    agent_id="greedy_cost",
    api_url="http://localhost:8000",
    weight_type="cost"
)

action = agent.select_action(state)
# Selects edge with lowest cost
```

**Behavior:**
1. Gets all available edges from state (filtering disrupted ones)
2. Finds edge with minimum weight
3. Returns action with that edge as path

### 3. DijkstraAgent

**Strategy:** Uses Dijkstra's algorithm to find shortest path avoiding disrupted nodes/edges.

**Parameters:**
- `weight_type`: "time", "cost", or "carbon"

**Use Case:** Global optimization; finds best complete path around disruptions.

**Example:**
```python
# Minimize time
agent = DijkstraAgent(
    agent_id="dijkstra_time",
    api_url="http://localhost:8000",
    weight_type="time"
)

action = agent.select_action(state)
# Computes shortest path from start to end
```

**Behavior:**
1. Builds available graph (filtering disrupted nodes/edges)
2. Runs Dijkstra's algorithm from start to end node
3. Returns full path, or fallback to random edge if no path found
4. Handles disruptions by excluding them from the graph

## Baseline Runner (`baseline/run_baseline.py`)

### BaselineRunner Class

Orchestrates multi-agent experiments with trajectory collection and grading.

**Key Methods:**

1. **`run_episode(agent, max_steps, num_cargos)`**
   - Runs single episode with an agent
   - Interacts with API endpoints
   - Collects full trajectory
   - Returns trajectory and cumulative reward

2. **`run_agent(agent, agent_name, num_episodes, ...)`**
   - Runs multiple episodes for one agent
   - Evaluates trajectory with grader
   - Returns summary statistics

3. **`run_comparison(agent_configs, num_episodes)`**
   - Runs all agents in parallel/sequence
   - Collects results
   - Generates comparison report

4. **`print_comparison_report(report)`**
   - Formats and prints ranking table
   - Shows detailed metrics per agent

### Running Baselines

#### Prerequisites

1. **API Server Running:**
```bash
# Terminal 1: Start the API
python -m uvicorn app.main:app --reload --port 8000
```

2. **Dependencies Installed:**
```bash
pip install -r requirements.txt
```

#### Basic Usage

**Run All Baseline Agents:**
```bash
cd /home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv
python baseline/run_baseline.py \
    --agent_type all \
    --num_episodes 3 \
    --max_steps 50
```

**Run Specific Agent:**
```bash
python baseline/run_baseline.py \
    --agent_type greedy \
    --num_episodes 5 \
    --max_steps 100
```

**Save Results to File:**
```bash
python baseline/run_baseline.py \
    --agent_type all \
    --output results.json \
    --num_episodes 3
```

#### Command-Line Arguments

- `--api_url` (str): Base URL for API (default: `http://localhost:8000`)
- `--agent_type` (str): `random`, `greedy`, `dijkstra`, or `all` (default: `all`)
- `--num_episodes` (int): Episodes per agent (default: 3)
- `--max_steps` (int): Max steps per episode (default: 50)
- `--output` (str): Output JSON file for results (optional)

### Example Output

```
================================================================================
BASELINE COMPARISON REPORT
================================================================================

Total Agents: 5
Best Agent: DijkstraCost (Score: 82.3)

Rankings:
--------------------------------------------------------------------------------
Rank   Agent                         Efficiency    Avg Reward     
--------------------------------------------------------------------------------
1      DijkstraCost                  82.3           12.45         
2      GreedyCost                    78.1           11.20         
3      DijkstraTime                  75.9           10.85         
4      GreedyTime                    72.4           9.60          
5      RandomAgent                   65.2           7.30          

Detailed Results:
--------------------------------------------------------------------------------

RandomAgent:
  Episodes: 3
  Total Steps: 156
  Avg Reward: 7.30
  Max Reward: 8.50
  Efficiency Score: 65.2
  Weighted Score: 245.60
  Deliveries: 6
  Metrics:
    - Time: 45.30h
    - Cost: $1250.00
    - Carbon: 85.40kg

DijkstraCost:
  Episodes: 3
  Total Steps: 168
  Avg Reward: 12.45
  Max Reward: 14.20
  Efficiency Score: 82.3
  Weighted Score: 156.20
  Deliveries: 9
  Metrics:
    - Time: 32.10h
    - Cost: $780.00
    - Carbon: 52.30kg

================================================================================
```

## Integration with API

### API Endpoints Used

1. **`GET /health`** - Verify API is running
2. **`POST /reset`** - Reset environment for new episode
3. **`GET /state`** - Get current state with network and disruptions
4. **`POST /cargo/add`** - Create cargo for transport
5. **`POST /task1/route`** - Route cargo (time optimization)
6. **`POST /task2/route`** - Route cargo (cost optimization)
7. **`POST /task3/route`** - Route cargo (multimodal)

### State Structure

Agents receive state from `/state` endpoint:
```json
{
    "network": {
        "num_nodes": 6,
        "nodes": ["Warehouse", "Port A", ...],
        "edges": [
            {
                "from": "Warehouse",
                "to": "Port A",
                "time": 2.5,
                "cost": 150.0,
                "carbon": 12.5
            },
            ...
        ]
    },
    "disabled_nodes": ["Port A"],
    "disabled_edges": [["Warehouse", "Truck Terminal"]],
    "cargos": {...},
    "current_step": 3,
    "max_steps": 100
}
```

## Task-Specific Evaluation

### Task 1: Time Minimization
- Agent optimizes for speed
- Uses `Task1Action` schema
- Grader weights time heavily
- Best agent: Time-optimized Dijkstra

### Task 2: Cost Minimization
- Agent optimizes for cost
- Uses `Task2Action` schema
- Grader weights cost heavily
- Best agent: Cost-optimized Greedy/Dijkstra

### Task 3: Multimodal Optimization
- Agent optimizes for carbon emissions
- Uses `Task3Action` schema with cargo_type and split options
- Grader uses balanced trilemma formula
- Best agent: Carbon-aware Dijkstra

## Disruption Handling

Agents handle disruptions by:

1. **Observing** `disabled_nodes` and `disabled_edges` from state
2. **Filtering** available edges (excluding disabled ones)
3. **Routing** around: 
   - RandomAgent: Picks random available edge
   - GreedyAgent: Picks best available edge
   - DijkstraAgent: Finds best path avoiding disabled nodes/edges

Example:
```python
# If "Port A" is disabled:
disabled_nodes = ["Port A"]

# Agents filter out edges involving "Port A"
available_edges = [
    ("Warehouse", "Rail Hub"),
    ("Warehouse", "Truck Terminal"),
    # ("Warehouse", "Port A") is filtered out
]
```

## Performance Metrics

### Efficiency Score (0-100)
Combines:
- Weighted trilemma cost (lower better)
- Cargo deliveries (higher better)
- Step efficiency (fewer steps better)

### Weighted Score (lower better)
Raw calculation: $0.5 \times time + 0.3 \times cost + 0.2 \times carbon$

### Task-Specific Score
- Task 1: Accumulated hours
- Task 2: Accumulated cost
- Task 3: Accumulated carbon

## Example Workflow

### 1. Start API Server
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Run Baselines
```bash
python baseline/run_baseline.py --agent_type all --num_episodes 5
```

### 3. Analyze Results
```bash
# Results printed to console
# Optionally save to JSON
python baseline/run_baseline.py --agent_type dijkstra --output dijkstra_results.json
```

### 4. Visualize/Compare
```python
import json

with open("dijkstra_results.json") as f:
    results = json.load(f)

# Access specific agent results
for name, data in results.items():
    print(f"{name}: {data['evaluation']['efficiency_score']:.1f}")
```

## Known Limitations & Future Improvements

### Current Limitations
1. API-dependent: Requires running server with `/tasks` endpoint
2. Single-edge routing: Greedy only considers immediate edges
3. No learning: Agents don't adapt across episodes
4. Deterministic: DijkstraAgent always picks same optimal path

### Future Improvements
1. **Learning Agents**: Q-learning, PPO for adaptive routing
2. **Multi-leg Routes**: Route planning across multiple edges
3. **Uncertainty**: Handle uncertain edge weights/disruptions
4. **Batch Optimization**: Multi-cargo planning
5. **Real-time Adaptation**: Replan when disruptions occur mid-route

## References

- **Grader**: [app/api/grader.py](app/api/grader.py)
- **Agents**: [baseline/agent.py](baseline/agent.py)
- **Runner**: [baseline/run_baseline.py](baseline/run_baseline.py)
- **API**: [app/main.py](app/main.py)
- **Schemas**: [app/api/schemas.py](app/api/schemas.py)
