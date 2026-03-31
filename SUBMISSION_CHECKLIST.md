# INTERMODALFREIGHTENV SUBMISSION FLIGHT CHECKLIST

> **Status:** MANDATORY BEFORE APRIL 7, 11:59 PM IST  
> **Rule:** If ANY of these checkboxes are empty, DO NOT hit submit.  
> **Project:** IntermodalFreightEnv - Multi-objective Freight Routing with Disruption Handling

---

## 🚀 1. The Disqualification Zero-Tolerance Check

*These checks are run automatically by scripts. If they fail, humans will never see your code.*

- [ ] `openenv validate --verbose` runs with **0 errors**
  - Validates `openenv.yaml` syntax
  - Confirms `FreightEnvironment` class exists
  - Verifies task schema definitions
  - Ensures all required endpoints are implemented

- [ ] HuggingFace Space deployed and `ping https://<your-space>.hf.space/health` returns `HTTP 200 OK`
  - Space must be publicly accessible
  - `/health` endpoint responds within 5 seconds
  - No authentication required for health check

- [ ] `reset()` called on your live Space returns a valid JSON `Observation`
  - Observation contains graph nodes (Warehouse, Port A, Rail Hub, Air Terminal, Truck Terminal, Destination)
  - Observation includes budget parameters (`budget_hours`, `budget_dollars`, `budget_carbon`)
  - Observation lists `disrupted_nodes` and `disrupted_edges` (may be empty initially)
  - Response is valid JSON with no malformed data

- [ ] Docker builds successfully (`openenv build`)
  - No build errors
  - Image size < 2 GB (reasonable for Python/FastAPI)
  - Builds from clean state without cached layers

- [ ] `openenv.yaml` exists at the root, is valid, and matches your python types
  - Located at `/home/harsh/CodeWithHarsh/ML Projects/IntermodalFreightEnv/openenv.yaml`
  - YAML syntax is valid (no parsing errors)
  - Environment config matches `EnvironmentConfig` dataclass
  - Task definitions match `Task1Action`, `Task2Action`, `Task3Action` schemas
  - Network definition with 6+ nodes and edges with time/cost/carbon attributes

- [ ] Target domain is **NOT** a classic game (no Chess, Tic-Tac-Toe, Snake)
  - ✅ Supply chain routing with real-world constraints (multi-objective optimization)
  - ✅ Disruption scenarios (node/edge failures)
  - ✅ Budget constraints (trilemma: time, cost, carbon)
  - ✅ NOT a game—is operational research problem

---

## 🚀 2. The Golden Ratio (The 3 Tasks)

*Checking the core OpenEnv requirements.*

### Task 1: Time Minimization
- [ ] `POST /task1/route` endpoint exists
- [ ] Action schema is `Task1Action` with fields:
  - `task_type: "task_1_time"` ✅
  - `cargo_id: int` ✅
  - `path: List[str]` (sequence of nodes) ✅
- [ ] Response includes:
  - `reward: float` (negative penalty for time cost)
  - `done: bool` (episode termination flag)
  - `observation: {...}` (updated state with trilemma counters)
  - `info: {...}` (metadata)
- [ ] Grader applies time weight: `0.5×accumulated_hours`

### Task 2: Cost Minimization
- [ ] `POST /task2/route` endpoint exists
- [ ] Action schema is `Task2Action` with fields:
  - `task_type: "task_2_cost"` ✅
  - `cargo_id: int` ✅
  - `path: List[str]` (sequence of nodes) ✅
- [ ] Response includes same structure as Task 1
- [ ] Grader applies cost weight: `0.3×accumulated_cost`

### Task 3: Multimodal Optimization (Structurally Distinct)
- [ ] `POST /task3/route` endpoint exists
- [ ] Action schema is `Task3Action` with **UNIQUE** fields:
  - `task_type: "task_3_multimodal"` ✅
  - `cargo_id: int` ✅
  - `cargo_type: CargoType` enum (truck/rail/ship/air) ✅ **← DISTINCT from Task 1/2**
  - `path: List[str]` ✅
  - `split_at: List[int]` (node indices to split cargo) ✅ **← DISTINCT from Task 1/2**
- [ ] Response includes same structure
- [ ] Grader applies carbon weight: `0.2×accumulated_carbon`

### Unified Requirements
- [ ] `GET /tasks` endpoint returns HTTP 200 with all 3 task definitions
- [ ] Each task includes:
  ```json
  {
    "name": "Task 1: Time Minimization",
    "description": "Route cargo to minimize transit time",
    "action_schema": {"type": "object", "properties": {...}},
    "reward_type": "continuous",
    "optimization_objective": "minimize"
  }
  ```
- [ ] `POST /grader` endpoint accepts trajectory and returns:
  ```json
  {
    "score": 0.75,
    "metrics": {
      "accumulated_hours": 24.3,
      "accumulated_cost": 1250.50,
      "accumulated_carbon": 45.2
    },
    "efficiency_score": 78.5
  }
  ```
- [ ] Grader score calculation follows weighted formula:
  - `weighted_score = 0.5×time + 0.3×cost + 0.2×carbon`
  - Normalized to `[0.0, 1.0]` range
  - Never negative, never > 1.0

---

## 🚀 3. The Baseline Script Proof

*Proving your environment is playable.*

- [ ] `baseline/run_baseline.py` exists at `/home/harsh/CodeWithHarsh/ML Projects/IntermodalFreightEnv/baseline/run_baseline.py`

- [ ] Script accepts `--base-url` argument
  ```bash
  python baseline/run_baseline.py --base-url http://localhost:8000
  python baseline/run_baseline.py --base-url https://your-space.hf.space
  ```

- [ ] Script plays all 3 tasks sequentially
  - Task 1: Time minimization agent
  - Task 2: Cost minimization agent
  - Task 3: Carbon/multimodal optimization agent

- [ ] Uses greedy heuristic agent (provided: `GreedyAgent` in `baseline/agent.py`)
  - Queries `/state` endpoint
  - Filters disabled nodes/edges from `disrupted_nodes` and `disrupted_edges`
  - Selects minimum-weight available edge
  - Repeats until episode ends or max_steps reached

- [ ] Exception handling: Failures don't crash early
  - Task 1 failure → still runs Task 2
  - Task 2 failure → still runs Task 3
  - Uses try-except blocks around each episode run
  - Logs errors but continues

- [ ] Prints 3 final scores clearly to console
  ```bash
  Task 1 (Time) Final Score: 0.82
  Task 2 (Cost) Final Score: 0.71
  Task 3 (Multimodal) Final Score: 0.78
  ```

- [ ] Exits with `exit(0)` on success
  - No exit code other than 0
  - All 3 scores successfully computed

---

## 🚀 4. The Defensive Programming Check

*Agents do stupid things. Your server must never crash.*

### No Bare Raises
- [ ] `step()` function never contains unhandled `raise ValueError(...)`
  - Invalid edge selections return penalty in observation, not crash
  - Disabled node access returns 0 reward + done=True, not crash
  - Path validation returns graceful error, not KeyError

### No Silent Failures
- [ ] No `except: pass` blocks in business logic
  - Use specific exception types: `except ValueError as e: log_error(e)`
  - All exceptions logged with context
  - Never swallow exceptions without re-raising or explicit handling

### Determinism with Seed
- [ ] Calling `reset(seed=42)` twice yields identical scenario
  - Same disrupted nodes/edges (deterministic disorder)
  - Same cargo weights
  - Same budget parameters
  - Shuffled seed at initialization, not per-step

```python
# Pseudo-code validation
env1 = FreightEnvironment(config)
obs1 = env1.reset(seed=42)

env2 = FreightEnvironment(config)
obs2 = env2.reset(seed=42)

assert obs1["disrupted_nodes"] == obs2["disrupted_nodes"]
assert obs1["disrupted_edges"] == obs2["disrupted_edges"]
```

### State Bleed Prevention
- [ ] `episode_id` is a newly generated UUID inside every `reset()` call
  - UUID4 generated at reset
  - Not reused across episodes
  - Guarantees unique trajectory tracking

```python
import uuid
def reset(self, seed=None):
    self.episode_id = str(uuid.uuid4())
    ...
```

### Score Boundaries
- [ ] All grader scores are wrapped in valid range `[0.0, 1.0]`
  ```python
  score = max(0.0, min(1.0, raw_score))
  ```
- [ ] Negative trajectory costs don't produce negative scores
- [ ] Exceptional performance doesn't exceed 1.0

### Hard Stop at Max Steps
- [ ] Hard-coded maximum step limit in `step()` function
  - After 50 steps (or configured max), `done = True` regardless
  - Prevents infinite episodes
  - Logged when step limit reached

```python
def step(self, action):
    self.current_step += 1
    if self.current_step >= self.max_steps:
        done = True
    ...
```

---

## 🚀 5. The "Wow Factor" (Human Judging)

*Once scripts pass, humans grade these specific elements.*

### README Completeness
- [ ] **Action Space Documented**
  - Task 1 Action: `task_type`, `cargo_id`, `path`
  - Task 2 Action: Same structure
  - Task 3 Action: Plus `cargo_type` and `split_at`
  - JSON schema examples for each task

- [ ] **Observation Space Documented**
  - `network`: Graph with nodes and edges (time/cost/carbon attributes)
  - `disrupted_nodes`: List of disabled nodes
  - `disrupted_edges`: List of (from, to) disabled edges
  - `cargos`: Current cargo states
  - `trilemma_counters`: Accumulated hours, cost, carbon
  - `current_step`: Episode step number

- [ ] **Reward Formulas Written Out**
  - Weighted formula: `0.5×time + 0.3×cost + 0.2×carbon`
  - Per-edge costs: time (hours), cost ($), carbon (kg CO2)
  - Efficiency score: normalized to 0-100 scale
  - Partial credit mechanism for incomplete deliveries

- [ ] **Setup Instructions Clear**
  1. Clone repository
  2. Install dependencies: `pip install -r requirements.txt`
  3. Start API: `python -m uvicorn app.main:app --reload`
  4. Run baselines: `python baseline/run_baseline.py`
  5. View results

### Partial Credit (Not All-or-Nothing)
- [ ] Medium/Hard task graders return nuanced scores (0.3, 0.7, etc.)
  - Not just 0.0 or 1.0
  - Reflects partial success on deliveries
  - Weighted by time/cost/carbon appropriately
  - Example: "Delivered 2 of 3 cargos, exceeded time budget by 10%" → score 0.62

### Semantic Meaning (Clear Naming)
- [ ] Variables named descriptively, not `x1`, `y2`
  - ✅ `accumulated_hours`, `accumulated_cost`, `accumulated_carbon`
  - ✅ `medical_supplies`, `refrigerated_goods`, `hazmat_cargo`
  - ✅ `budget_remaining_usd`, `carbon_budget_remaining_kg_co2`
  - ✅ `disrupted_nodes`, `disabled_edges`
  - ✅ NOT: `x`, `y`, `z`, `temp1`, `val2`

- [ ] Comments explain *why*, not *what*
  - ✅ "Dijkstra with disruption-aware graph filtering"
  - ✅ "Normalize score to [0,1] to enable cross-task comparison"
  - ✅ NOT: "Loop through edges" (obvious from code)

### Clean Git & Deployment
- [ ] No API keys committed
  - Search for `api_key`, `secret`, `token` → 0 results
  - .env not in repo
  - HF Space tokens not hardcoded

- [ ] No `.venv`, `node_modules`, `__pycache__` committed
  - `.gitignore` includes standard Python patterns
  - `git status` shows clean working tree

- [ ] No debug logs or `outputs/` directories in repo
  - No `print()` statements except for user-facing output
  - No temporary test files
  - No locally-generated results committed

- [ ] README, BASELINE_AND_GRADER.md, PHASE_3_SUMMARY.md included
  - Clear user guide
  - Complete API reference
  - Implementation architecture

---

## 🚀 6. The Final Run (Exact Sequence)

Run this **exact sequence** one last time before submitting the URL.  
**Every command must succeed.** Copy-paste these commands:

### Step 1: Build Docker image from scratch
```bash
cd /home/harsh/CodeWithHarsh/ML\ Projects/IntermodalFreightEnv
openenv build
# Expected: "Successfully built docker image"
```

- [ ] Build completes with exit code 0

### Step 2: Run the container locally
```bash
docker run -p 8000:8000 openenv-intermodalfreightenv
# Expected: "Application startup complete" on port 8000
# Keep this window open
```

- [ ] Container starts without errors

### Step 3: Test all required endpoints (in a new terminal)
```bash
# Test reset endpoint
curl -X POST http://localhost:8000/reset

# Test tasks endpoint
curl http://localhost:8000/tasks

# Test grader endpoint (with sample trajectory)
curl -X POST http://localhost:8000/grader \
  -H "Content-Type: application/json" \
  -d '{"trajectory": []}'

# Test baseline endpoint
curl -X POST http://localhost:8000/baseline
```

- [ ] `/reset` returns valid JSON Observation (HTTP 200)
- [ ] `/tasks` returns 3 task definitions (HTTP 200)
- [ ] `/grader` returns `{"score": X.XX}` (HTTP 200)
- [ ] `/baseline` returns task scores (HTTP 200)

### Step 4: Run baseline script (the judge's automated check)
```bash
python baseline/run_baseline.py --base-url http://localhost:8000
```

- [ ] Exits with code 0
- [ ] Prints all 3 scores to console
- [ ] All scores are floats in range [0.0, 1.0]
- [ ] Output resembles:
  ```
  Task 1 (Time) Final Score: 0.82
  Task 2 (Cost) Final Score: 0.71
  Task 3 (Multimodal) Final Score: 0.78
  ```

### Step 5: Validate OpenEnv spec
```bash
openenv validate --verbose
```

- [ ] Exits with code 0
- [ ] Messages show:
  - ✅ Config valid
  - ✅ Tasks defined
  - ✅ Endpoints reachable
  - ✅ No errors

### Step 6: Push to HuggingFace Space
```bash
openenv push
```

- [ ] Exits with code 0
- [ ] Space URL provided in output

### Step 7: Confirm live Space works
```bash
# Replace <your-space> with actual Space username/name
curl -X POST https://<your-space>.hf.space/reset
# Expected: HTTP 200, valid JSON Observation

python baseline/run_baseline.py --base-url https://<your-space>.hf.space
# Expected: Exit 0, all 3 scores printed
```

- [ ] Live Space responds to `/reset` with HTTP 200
- [ ] Live Space runs baseline script successfully
- [ ] All 3 scores returned from live Space

---

## ✅ Sign-Off

> **Date Completed:** _______________  
> **Team Member:** _______________  
> **Git Commit Hash (for this verification):** _______________  

### Final Certification

- [ ] **I have checked every single box above**
- [ ] **I have run the exact sequence in Section 6 and all commands succeeded**
- [ ] **I am ready to submit to OpenEnv for automated + human judging**

```bash
# Print this to verify you're on feature/baseline-and-grader branch
git branch
# Output should show: * feature/baseline-and-grader

# Confirm clean git state
git status
# Output should show: "nothing to commit, working tree clean"
```

---

## 📋 Appendix: Quick Reference

### Endpoint Summary
| Endpoint | Method | Parameters | Expected Response |
|----------|--------|------------|------------------|
| `/health` | GET | — | `{"status": "ok"}` |
| `/reset` | POST | `seed?` | Full Observation JSON |
| `/state` | GET | — | Current Observation JSON |
| `/tasks` | GET | — | List of 3 task definitions |
| `/cargo/add` | POST | `cargo_id`, `origin`, `destination` | Confirmation |
| `/task1/route` | POST | `task_type`, `cargo_id`, `path` | Step response (reward, obs, done) |
| `/task2/route` | POST | `task_type`, `cargo_id`, `path` | Step response |
| `/task3/route` | POST | `task_type`, `cargo_id`, `cargo_type`, `path`, `split_at` | Step response |
| `/grader` | POST | `trajectory` (list of steps) | `{"score": 0.0-1.0}` |
| `/baseline` | POST | — | Task scores (optional, for convenience) |

### Key Classes
- `FreightEnvironment` - Main environment class
- `GreedyAgent` - Baseline heuristic agent
- `Grader` - Trajectory evaluation with weighted formula
- `Task1Action`, `Task2Action`, `Task3Action` - Distinct action schemas

### Critical Files
- `openenv.yaml` - Config (must be valid)
- `app/main.py` - FastAPI server
- `app/engine/core_env.py` - FreightEnvironment
- `baseline/run_baseline.py` - Automated judge script
- `Dockerfile` - Docker image definition

---

**Good luck! You've got this. 🚀**
