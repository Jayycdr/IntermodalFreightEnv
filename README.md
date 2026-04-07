---
title: Intermodal Freight Environment
emoji: 🚚
colorFrom: blue
colorTo: indigo
sdk: docker
sdk_version: "1.0"
app_file: app/main.py
pinned: false
---

# Intermodal Freight Environment

**AI-Powered Multi-Objective Freight Routing Optimization for Reinforcement Learning**

**Project by:** Jay, Harsh, and Aryan  
**Status:** ✅ Production Ready | 🟢 Fully Tested | 🚀 Live Deployment

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Quick Start](#quick-start)
4. [How It Works](#how-it-works)
5. [Task Types](#task-types)
6. [Scoring & Evaluation](#scoring--evaluation)
7. [API Reference](#api-reference)
8. [Environment State](#environment-state)
9. [Running Agents](#running-agents)
10. [Code Quality](#code-quality)
11. [Testing](#testing)
12. [Project Structure](#project-structure)

---

## 🎯 Overview

**Intermodal Freight Environment** is a sophisticated multi-objective optimization platform for freight transportation routing. It simulates a realistic logistics network where agents learn to make optimal decisions across competing objectives:

- ⏱️ **Time** - Minimize delivery duration
- 💰 **Cost** - Minimize transportation expenses  
- 🌱 **Carbon** - Minimize environmental impact

The environment implements the **"Trilemma" framework** - a 3-dimensional optimization challenge requiring balanced decision-making across conflicting objectives. Agents must learn to navigate trade-offs and discover Pareto-optimal solutions.

### Real-World Relevance

Modern logistics faces genuine pressure to optimize across multiple dimensions:
- Customers demand fast delivery (time)
- Companies need to maintain profitability (cost)
- Regulations and sustainability goals require low emissions (carbon)

This environment models these realistic constraints in a structured, learnable environment suitable for RL research and agent development.

---

## ✨ Key Features

| Feature | Details |
|---------|---------|
| **Multi-Objective Optimization** | Simultaneous optimization of time, cost, and carbon emissions |
| **Realistic Network** | Fully-connected transportation network (30 nodes, 100% reachability) |
| **Multiple Modes** | Road (truck), Rail, Air, Sea transportation methods |
| **RL-Ready** | Standard MDP formulation with discrete actions and continuous state |
| **Production Code** | Clean, well-tested, documented Python codebase |
| **Fast Evaluation** | O(1) path validation, instant reward calculation |
| **Deterministic** | Fully reproducible results for fair evaluation |
| **API-Driven** | REST API for easy integration with learning frameworks |
| **Live Deployment** | Running on HuggingFace Spaces (production-ready) |
| **Comprehensive Tests** | 45+ unit tests covering all core functionality |

---

## 🚀 Quick Start

### Option 1: Run with Python

```bash
# Clone repository
git clone https://github.com/HarshPawar-7/IntermodalFreightEnv.git
cd IntermodalFreightEnv

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start API server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, run inference agent
python scripts/inference.py
```

### Option 2: Run with Docker

```bash
# Start all services
docker-compose up

# Access dashboard at http://localhost:7860
```

### Option 3: Use Live Deployment

**No installation needed!** Use the live environment on HuggingFace Spaces:  
👉 https://huggingface.co/spaces/HarshPawar-7/intermodal-freight-env

---

## 🔧 How It Works

### The Environment Loop

```
1. RESET → Initialize environment with random task
2. OBSERVE → Get current state (nodes, cargo, constraints)
3. DECIDE → Agent selects an action (route + transport mode)
4. STEP → Execute action, calculate rewards
5. REPEAT → Until episode terminates or max steps reached
6. GRADE → Final evaluation score
```

### State Representation

Each state includes:
- **Current Location** - Where the agent currently is in the network
- **Available Actions** - Possible next nodes and transport modes
- **Cargo Info** - Current load, destination, time/cost constraints
- **Network Info** - Node distances, mode capabilities, carbon factors

### Action Space

Actions are combinations of:
- **Target Node** - Where to route next (1-30)
- **Transport Mode** - How to travel (truck, rail, air, sea)

Selected action determines:
- Time to deliver
- Cost incurred
- Carbon emissions produced

### Reward Definition

Reward is a weighted combination:

$$\text{Score} = 0.5 \times \text{time\_score} + 0.3 \times \text{cost\_score} + 0.2 \times \text{carbon\_score}$$

Where each component is normalized (0-1):
- **time_score** = 1 - (actual_time / max_time)
- **cost_score** = 1 - (actual_cost / max_cost)  
- **carbon_score** = 1 - (actual_carbon / max_carbon)

---

## 📦 Task Types

The environment generates different optimization challenges:

### 1. **Traveling Salesman Problem (TSP)**
- **Goal:** Visit a set of nodes and return to origin
- **Constraint:** Must visit all nodes exactly once
- **Challenge:** Minimize total time/cost/carbon
- **Difficulty:** Low (single objective focus possible)

### 2. **Multi-Depot Vehicle Routing Problem (MDVRP)**
- **Goal:** Distribute cargo from multiple sources to multiple destinations
- **Constraint:** Respect vehicle capacity and time windows
- **Challenge:** Optimize multi-leg routes with varied constraints
- **Difficulty:** Medium (multi-objective trade-offs emerge)

### 3. **Capacitated Vehicle Routing (CVRP)**
- **Goal:** Deliver all packages with vehicle capacity constraints
- **Constraint:** Single depot, capacity limits
- **Challenge:** Efficient routing under resource constraints
- **Difficulty:** Medium

### 4. **Time-Windowed Routing (VRPTW)**
- **Goal:** Deliver cargo meeting strict time windows
- **Constraint:** Cannot arrive outside [earliest, latest] times
- **Challenge:** Balance speed (expensive, low carbon via air) with constraints
- **Difficulty:** Hard (conflicting objectives)

Each task type tests different aspects of the agent's learning capability.

---

## 🏆 Scoring & Evaluation

### Individual Episode Score

Score ranges from **0 to 1** (higher is better):

$$\text{Episode\_Score} = 0.5 \times t_{score} + 0.3 \times c_{score} + 0.2 \times e_{score}$$

### Multi-Episode Performance

Over multiple episodes, agents are evaluated on:

1. **Average Score** - Mean performance across episodes
2. **Score Stability** - Low variance indicates consistent learning
3. **Convergence** - How quickly scores improve with training
4. **Pareto Optimality** - Finding solutions on the efficiency frontier

### Grading API

```python
# Get final grade for completed trajectory
POST /grader
{
    "task_id": "task_123",
    "trajectory": [
        {"node": 1, "mode": "truck"},
        {"node": 2, "mode": "rail"},
        {"node": 1, "mode": "truck"}
    ]
}

# Response: { "score": 0.87, "components": {...} }
```

---

## 🔌 API Reference

### Base URL
- **Local:** `http://localhost:8000`
- **Live:** `https://huggingface.co/spaces/HarshPawar-7/intermodal-freight-env`

### Core Endpoints

#### 1. Health Check
```
GET /health
```
Response: `{"status": "ok", "timestamp": "2026-04-08T10:30:45Z"}`

#### 2. Get Available Tasks
```
GET /tasks
```
Returns list of available task types: TSP, MDVRP, CVRP, VRPTW

#### 3. Reset Environment
```
POST /reset
Body: { "task_type": "TSP" }
```
Returns: Initial state, task_id, action space

#### 4. Execute Step
```
POST /step
Body: {
    "task_id": "task_123",
    "action": {
        "target_node": 5,
        "transport_mode": "rail"
    }
}
```
Returns: New state, reward, done flag

#### 5. Grade Trajectory
```
POST /grader
Body: {
    "task_id": "task_123",
    "trajectory": [...]
}
```
Returns: Final score breakdown

---

## 📊 Environment State

### State Structure

```python
{
    "current_node": 1,
    "cargo": {
        "origin": 1,
        "destination": 15,
        "weight": 100,
        "fragile": false
    },
    "constraints": {
        "time_limit": 480,        # minutes
        "cost_budget": 5000,      # currency units
        "carbon_limit": 200       # kg CO2
    },
    "available_actions": [
        {
            "target_node": 2,
            "modes": ["truck", "rail", "air"]
        },
        ...
    ],
    "metrics_so_far": {
        "time_used": 60,
        "cost_incurred": 500,
        "carbon_emitted": 20
    }
}
```

---

## 🤖 Running Agents

### Built-in Inference Script

```bash
python scripts/inference.py
```

This script:
- Connects to the API automatically
- Runs intelligent step-taking
- Handles multiple episodes
- Stops when convergence detected
- Logs all metrics

### Custom Agent Loop

```python
import requests

API_URL = "http://localhost:8000"

# Reset
response = requests.post(f"{API_URL}/reset", json={"task_type": "TSP"})
state = response.json()
task_id = state["task_id"]

# Run episode
done = False
while not done:
    # Choose action
    action = {"target_node": 5, "transport_mode": "rail"}
    
    # Step
    response = requests.post(
        f"{API_URL}/step",
        json={"task_id": task_id, "action": action}
    )
    
    state = response.json()
    reward = state["reward"]
    done = state["done"]

# Grade
response = requests.post(
    f"{API_URL}/grader",
    json={"task_id": task_id, "trajectory": state["trajectory"]}
)
score = response.json()["score"]
```

---

## 🏗️ Project Structure

```
IntermodalFreightEnv/
├── app/                           # FastAPI Application
│   ├── main.py                   # Entry point, API routes
│   ├── constants.py              # Network, mode definitions
│   ├── exceptions.py             # Custom exceptions
│   ├── api/
│   │   ├── grader.py            # Scoring logic
│   │   └── schemas.py           # Request/response models
│   ├── engine/
│   │   ├── core_env.py          # MDP environment
│   │   └── graph.py             # Network topology
│   └── utils/
│       ├── helpers.py           # Utility functions
│       └── logger.py            # Structured logging
│
├── scripts/
│   └── inference.py              # Main agent runner
│
├── baseline/
│   ├── agent.py                  # Baseline agent class
│   └── run_baseline.py           # Runner script
│
├── tests/                         # Test Suite (45+ tests)
│   ├── test_api_layer.py
│   ├── test_core_environment.py
│   ├── test_mathematics.py
│   ├── test_task_types.py
│   └── ...
│
├── frontend/                      # Dashboard
│   ├── dashboard.py              # Main dashboard
│   └── agent_analytics.py        # Analytics
│
├── requirements.txt               # Python dependencies
├── docker-compose.yml            # Docker setup
├── Dockerfile                    # Container config
└── README.md                     # This file
```

### Not Included (Reference Only)

The repository uses `.gitignore` to exclude:
- `docs/` - Development documentation
- `_reference/` - Testing/verification scripts
- `_archive/` - Archived analysis reports

---

## ✅ Code Quality

### Clean Code Standards

✅ **Single Responsibility** - Each module has one clear purpose  
✅ **DRY Principle** - No code duplication  
✅ **Clear Naming** - Variables/functions are self-documenting  
✅ **Type Hints** - Full type annotations throughout  
✅ **Error Handling** - Comprehensive exception handling  
✅ **Documentation** - Every public function documented  
✅ **Testing** - 45+ unit tests with >90% coverage  

### Performance

✅ **Fast Evaluations** - O(1) action validation  
✅ **Deterministic** - Fully reproducible results  
✅ **Scalable** - Handles 30+ nodes efficiently  
✅ **Memory Efficient** - Minimal state overhead  

---

## 🧪 Testing

### Run All Tests

```bash
# Run entire test suite
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Run specific test category
pytest tests/test_mathematics.py -v
```

### Test Coverage

- **API Layer** - 8 tests covering all endpoints
- **Core Environment** - 12 tests for MDP logic
- **Mathematics** - 15 tests for scoring/rewards
- **Task Types** - 10 tests for each task variant
- **Integration** - 5+ tests for end-to-end workflows

### Key Test Files

- `test_mathematics.py` - Validates trilemma formula, scoring
- `test_core_environment.py` - Environment state transitions
- `test_api_layer.py` - HTTP endpoint behavior
- `test_task_types.py` - Task generation and constraints

---

## 🌐 Deployment

### Local Deployment

```bash
# Development mode
python -m uvicorn app.main:app --reload

# Production mode
gunicorn app.main:app -w 4
```

### Docker Deployment

```bash
# Build image
docker build -t intermodal-freight-env .

# Run container
docker run -p 8000:8000 intermodal-freight-env

# Or use Docker Compose
docker-compose up
```

### HuggingFace Spaces (Live)

Deployed at: https://huggingface.co/spaces/HarshPawar-7/intermodal-freight-env

---

## 📚 Learning Resources

### For RL Practitioners

- Start with `scripts/inference.py` to understand the interface
- Review `app/engine/core_env.py` for MDP formulation
- Study `baseline/agent.py` for a simple learning agent

### For Logistics Enthusiasts

- See `app/constants.py` for network definition
- Review transportation modes and their characteristics
- Understand the trilemma weighting and trade-offs

### For Developers

- Read `API_INFRASTRUCTURE.md` for API design decisions
- Check `CORE_SYSTEMS.md` for environment mechanics
- Review test files for usage examples

---

## 🚀 Getting Started with Development

1. **Clone & Setup**
   ```bash
   git clone <repo>
   cd IntermodalFreightEnv
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Start Development Server**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

3. **Run Tests**
   ```bash
   pytest tests/
   ```

4. **Launch Agent**
   ```bash
   python scripts/inference.py
   ```

---

## 📋 Pre-Submission Checklist

✅ Environment variables with defaults  
✅ OpenAI client integration  
✅ Structured logging (START/STEP/END)  
✅ Complete documentation  
✅ 45+ passing tests  
✅ Clean code standards met  
✅ Deterministic behavior  
✅ Live deployment verified  
✅ API fully functional  
✅ Dashboard operational  

---

## 📞 Support

### Issues & Questions
- Create an issue on GitHub
- Check existing documentation in `docs/`
- Run tests to debug locally

### Submission Info
- **Hackathon:** Scaler School of Technology
- **Repository:** https://github.com/HarshPawar-7/IntermodalFreightEnv
- **Live Demo:** https://huggingface.co/spaces/HarshPawar-7/intermodal-freight-env

---

**Made with ❤️ by Jay, Harsh, and Aryan**

## License

Project submission for Scaler School of Technology Hackathon 2026