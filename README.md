# IntermodalFreightEnv

An intelligent multimodal freight routing environment that challenges agents to optimize logistics considering time, cost, and environmental impact.

**Project by Jay, Harsh and Aryan**

## Overview

IntermodalFreightEnv is a reinforcement learning environment for optimizing intermodal freight transportation. Agents learn to route cargo through multimodal networks (truck, rail, ship, air) while balancing three competing objectives: minimizing delivery time, cost, and carbon emissions.

## Environment Specification

### Action Space

The agent's action space consists of discrete choices for routing decisions:

- **For Time-Minimization Task**: Choose transportation mode and route from origin to destination, prioritizing speed (air > truck > rail > ship)
- **For Cost-Minimization Task**: Choose route and split cargo across modes to minimize total cost per ton
- **For Multimodal Balancing Task**: In addition to route selection, choose:
  - `cargo_type`: Type of freight being transported (perishable, hazmat, machinery, etc.)
  - `split_at`: Junction point to split cargo across multiple transportation modes

Each action maps to a sequence of transportation legs that the cargo traverses through the network.

### Observation Space

The agent receives the following observations at each step:

```
{
  "current_location": str,           # Current node in the network
  "destination": str,                # Target destination node
  "remaining_distance": float,       # Untraversed distance (km)
  "cargo_weight": float,             # Cargo weight (tons)
  "time_consumed": float,            # Accumulated time (hours)
  "cost_consumed": float,            # Accumulated cost ($1000s)
  "carbon_emitted": float,           # Accumulated emissions (tons CO2)
  "available_modes": list,           # Available transportation modes at current node
  "current_step": int,               # Current environment step (0-1000)
  "episode_id": str,                 # Unique identifier (UUID) for this episode
  "task_id": int                     # Task identifier (1, 2, or 3)
}
```

### Reward Structure

Rewards are computed as a **weighted trilemma score** normalized to [0, 1]:

$$\text{Score} = 1 - \left(0.5 \times \frac{\text{hours}}{h_{\text{max}}} + 0.3 \times \frac{\text{cost}}{c_{\text{max}}} + 0.2 \times \frac{\text{carbon}}{e_{\text{max}}}\right)$$

Where:
- $\text{hours}$: Accumulated delivery time (hours)
- $\text{cost}$: Accumulated transportation cost ($1000s)
- $\text{carbon}$: Accumulated carbon emissions (tons CO2)
- $h_{\text{max}}, c_{\text{max}}, e_{\text{max}}$: Normalization constants per task

**Weighting Scheme**:
- **50%**: Time efficiency (delivery speed matters most)
- **30%**: Economic cost (business viability)
- **20%**: Environmental impact (sustainability)

## Three Task Variants

### Task 1: Time-Optimized Routing
**Objective**: Minimize delivery time on a dense urban network
- Focus on finding the fastest routes
- Reward heavily weighted toward minimizing `accumulated_hours`
- Representative of time-sensitive cargo (perishables, express parcels)

### Task 2: Cost-Optimized Routing
**Objective**: Minimize transportation cost on a large regional network
- Focus on economical routing and mode selection
- Requires learning that slower modes can be cheaper
- Representative of standard freight with cost-driven logistics

### Task 3: Multimodal Balanced Optimization
**Objective**: Balance all three metrics using strategic cargo splitting
- Agents choose where to split cargo between transportation modes
- Agents select appropriate cargo types for different routes
- Combines complexity of Tasks 1 and 2 with additional decision variables

## API Specification

### Endpoints

#### `GET /health`
Health check endpoint
```
Response: {"status": "ok", "version": "1.0"}
```

#### `POST /reset`
Reset environment to initial state
```
Request: {"seed": 42}  # Optional
Response: 
{
  "current_location": "origin",
  "destination": "dest",
  "cargo_weight": 10.0,
  "time_consumed": 0.0,
  "cost_consumed": 0.0,
  "carbon_emitted": 0.0,
  "episode_id": "uuid-string",
  "task_id": task_number
}
```

#### `GET /tasks`
Get all three task definitions with schemas
```
Response:
{
  "tasks": [
    {
      "task_id": 1,
      "name": "Time Minimization",
      "description": "...",
      "action_schema": {...}
    },
    ...
  ]
}
```

#### `POST /grader`
Score a completed trajectory
```
Request:
{
  "task_id": 1,
  "trajectory": [
    {"action": "...", "observation": "..."},
    ...
  ]
}

Response:
{
  "score": 0.87,
  "metrics": {
    "accumulated_hours": 12.5,
    "accumulated_cost": 45.3,
    "accumulated_carbon": 8.2
  }
}
```

## Defensive Programming Features

- **UUID Episode Tracking**: Each environment reset generates a unique `episode_id` (UUID v4) to prevent state bleed between independent runs
- **Score Boundaries**: All scores strictly bounded to [0, 1] range
- **Step Limits**: Hard maximum of 1,000 steps per episode
- **Error Handling**: Comprehensive exception handling with meaningful error messages
- **No Bare Exceptions**: No bare `except:` clauses or `raise` without context

## Deployment

### Docker

Build and run with Docker:

```bash
docker build -t intermodal-freight .
docker run -p 8000:8000 intermodal-freight
```

### Baseline Agent

Run the baseline reinforcement learning agent:

```bash
python baseline/run_baseline.py --base-url http://localhost:8000
```

The baseline demonstrates:
- Task discovering via `/tasks` endpoint
- Environment interaction loop (reset → step → score)
- Handling all 3 task variants
- Exception handling and robustness

## Testing

Comprehensive test suite included:

```bash
# Test environment logic (41 tests)
python test_environment_logic.py

# View value results and metrics
python view_value_results.py

# Debug agent learning signals
python debug_agent_learning.py

# Verify against submission checklist
python verify_checklist.py
```

## Project Structure

```
IntermodalFreightEnv/
├── app/
│   ├── main.py              # FastAPI application
│   ├── api/
│   │   ├── grader.py        # Scoring logic with Trilemma metrics
│   │   └── schemas.py       # Pydantic response schemas
│   └── engine/
│       ├── core_env.py      # Environment simulation
│       └── graph.py         # Network topology
├── baseline/
│   ├── agent.py             # Baseline agent implementation
│   └── run_baseline.py      # CLI entry point
├── config/
│   └── openenv.yaml         # Environment configuration
├── Dockerfile               # Container specification
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Authors

Jay, Harsh, and Aryan