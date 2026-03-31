# API & Infrastructure Layer

## Overview

This document describes the API & Infrastructure layer implementation for IntermodalFreightEnv, including Pydantic schemas, FastAPI routes, and configuration mapping.

## 1. Pydantic Schemas (`app/api/schemas.py`)

### Design Philosophy

The schema layer provides:
- **Type validation** via Pydantic BaseModel
- **Task distinctiveness** with specialized action schemas
- **Structural clarity** for API contract definition
- **Interactive documentation** via FastAPI/OpenAPI

### Key Enums

#### TaskType
Maps three optimization objectives:
- `TASK_1_TIME`: Time minimization
- `TASK_2_COST`: Cost minimization
- `TASK_3_MULTIMODAL`: Multimodal routing (balanced)

#### CargoType (Task 3 Specific)
Transportation modes for multimodal routing:
- `TRUCK`: Road transport
- `RAIL`: Rail transport
- `SHIP`: Maritime transport
- `AIR`: Air freight

### Response Models

#### BaseResponse
All API responses follow this structure:
```python
{
  "success": bool,
  "message": str,
  "data": Optional[dict]
}
```

#### EnvironmentState
Current simulation state with trilemma counters:
```python
{
  "step": int,
  "active_cargos": int,
  "completed_cargos": int,
  "trilemma": {
    "accumulated_hours": float,
    "accumulated_cost": float,
    "accumulated_carbon": float
  },
  "network": {
    "nodes": List[NodeData],
    "edges": List[EdgeData]
  }
}
```

#### EvaluationResult
Task-specific performance metrics:
```python
{
  "task_type": TaskType,
  "score": 0.0-100.0,
  "metrics": dict,
  "feedback": str,
  "trilemma_final": TrilemmaState
}
```

### Task-Specific Action Schemas

#### Task 1Action (Time Minimization)
```python
{
  "task_type": "task_1_time",
  "cargo_id": int,
  "path": [int, ...]  # Sequence of nodes
}
```

#### Task2Action (Cost Minimization)
```python
{
  "task_type": "task_2_cost",
  "cargo_id": int,
  "path": [int, ...]  # Sequence of nodes
}
```

#### Task3Action (Multimodal Routing) - **STRUCTURALLY DISTINCT**
```python
{
  "task_type": "task_3_multimodal",
  "cargo_id": int,
  "cargo_type": CargoType,      # ← UNIQUE FIELD
  "path": [int, ...],
  "split_at": Optional[List[int]]  # ← UNIQUE FIELD
}
```

**Structural Distinctness Key Features:**
1. **cargo_type enum**: Forces explicit mode selection (truck/rail/ship/air)
2. **split_at nodes**: Allows mode transitions at specific locations
3. **Different field sets**: Task 3 schema is fundamentally different

This ensures agents treating Task 3 differently from Tasks 1 & 2.

## 2. FastAPI Routes (`app/main.py`)

### Architecture

The FastAPI application integrates with the core `FreightEnvironment` through:

```
FastAPI Routes
    ↓
Request Validation (Pydantic)
    ↓
Environment Methods
    ↓
Response Building
    ↓
OpenAPI Documentation
```

### Global Environment Management

```python
_env: Optional[FreightEnvironment] = None

def get_env() -> FreightEnvironment:
    """Get or create singleton environment instance"""
```

The application maintains a single environment instance with a default network configuration (6 nodes, 10 edges).

### Endpoint Categories

#### 1. Health & Status (No Impact)
- `GET /health` → Health check
- `GET /status` → Environment status

#### 2. Environment Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/reset` | POST | Reset with seed/disruption config |
| `/state` | GET | Get current environment state |

#### 3. Cargo Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/cargo/add` | POST | Create new cargo |
| `/cargo/split` | POST | Split cargo into multiple shipments |

#### 4. Task-Specific Routing
| Endpoint | Method | Task | Purpose |
|----------|--------|------|---------|
| `/task1/route` | POST | 1 | Route for time minimization |
| `/task2/route` | POST | 2 | Route for cost minimization |
| `/task3/route` | POST | 3 | Route with multimodal optimization |

#### 5. Simulation
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/step` | POST | Execute one simulation step |
| `/run-episode` | POST | Run complete episode |

#### 6. Evaluation
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/evaluate` | POST | Evaluate episode for specific task |

#### 7. Utilities
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/path` | GET | Find shortest path with weight metric |

### Request/Response Flow Example

#### Task 1 (Time Minimization) Workflow

```
1. POST /reset
   ↓ ResetRequest
   ↓ Environment resets, disruptions applied
   ↓ ResetResponse with initial state

2. POST /cargo/add
   ↓ CargoRequest
   ↓ Environment creates cargo
   ↓ CargoResponse with cargo_id

3. GET /path?origin=0&destination=5&weight=time
   ↓ Dijkstra finds fastest path
   ↓ BaseResponse with path and metrics

4. POST /task1/route
   ↓ Task1Action(cargo_id, path)
   ↓ Environment routes cargo
   ↓ BaseResponse confirms routing

5. POST /step
   ↓ StepRequest
   ↓ Cargo moves, trilemma updates
   ↓ StepResponse with new state/reward

6. POST /evaluate?task_type=task_1_time
   ↓ Evaluate performance
   ↓ EvaluationResult with task-specific score
```

#### Task 3 (Multimodal) Workflow

```
1. POST /reset
   ↓ ResetResponse

2. POST /cargo/add
   ↓ CargoResponse

3. POST /cargo/split
   ↓ Split into multiple shipments
   ↓ BaseResponse with split cargo IDs

4. POST /task3/route (for each split)
   ↓ Task3Action with cargo_type (rail/truck/ship/air)
   ↓ Environment routes with mode awareness
   ↓ BaseResponse

5. POST /step (repeated)
   ↓ Move cargos, update trilemma
   ↓ StepResponse

6. POST /evaluate?task_type=task_3_multimodal
   ↓ Balance time/cost/carbon
   ↓ EvaluationResult
```

## 3. Configuration (`config/openenv.yaml`)

### Structure

The YAML file maps to all three layers:

#### API Configuration
```yaml
api:
  host: "0.0.0.0"
  port: 8000
  docs_url: "/docs"
```

#### Environment Configuration
```yaml
environment:
  num_nodes: 6
  max_steps: 100
  disruption_probability: 0.1
```

#### Network Configuration
```yaml
network:
  nodes:
    - id: 0
      location: "Warehouse"
      capacity: 1000.0
  edges:
    - source: 0
      target: 1
      time: 2.0
      cost: 100.0
      carbon: 30.0
```

#### Task Definitions
```yaml
tasks:
  task_1:
    name: "Time Minimization"
    objective: "Minimize accumulated_hours"
    endpoints: [...]
  
  task_2:
    name: "Cost Minimization"
    objective: "Minimize accumulated_cost"
    endpoints: [...]
  
  task_3:
    name: "Multimodal Routing"
    objective: "Balance time, cost, carbon"
    cargo_modes: [truck, rail, ship, air]
    endpoints: [...]
```

#### Endpoint Mapping
```yaml
endpoints:
  task1_route:
    method: "POST"
    path: "/task1/route"
    request_schema: "Task1Action"
    response_schema: "BaseResponse"
```

#### Trilemma Configuration
```yaml
trilemma:
  objectives:
    - name: "time"
      weight_task1: 1.0
      weight_task2: 0.2
      weight_task3: 0.33
    - name: "cost"
      weight_task1: 0.2
      weight_task2: 1.0
      weight_task3: 0.33
    - name: "carbon"
      weight_task1: 0.2
      weight_task2: 0.2
      weight_task3: 0.34
```

### YAML-to-API Mapping

| YAML Section | Maps To |
|--------------|---------|
| `api.*` | FastAPI server config |
| `environment.*` | EnvironmentConfig |
| `network.nodes` | FreightNetwork nodes |
| `network.edges` | FreightNetwork edges |
| `tasks.task_1` | Task1Action, /task1/route |
| `tasks.task_2` | Task2Action, /task2/route |
| `tasks.task_3` | Task3Action, /task3/route |
| `endpoints.*` | FastAPI routes |
| `trilemma.*` | Scoring weights |

## 4. Error Handling

All endpoints return structured error responses:

```python
@app.post("/task1/route")
def task1_route_cargo(action: Task1Action):
    try:
        # Validate path
        if action.path[0] != cargo.origin:
            raise ValueError("Path origin mismatch")
        
        # Route cargo
        env.route_cargo(action.cargo_id, action.path)
        
        return BaseResponse(success=True, ...)
    except Exception as e:
        logger.error(f"Routing failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
```

HTTP Status Codes:
- `200`: Success
- `400`: Bad request (validation/logic error)
- `500`: Server error

## 5. OpenAPI Documentation

Available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Automatically generated from:
- Route descriptions
- Pydantic model docstrings (Config.json_schema_extra)
- Type hints

## 6. Usage Examples

### Example 1: Task 1 Complete Workflow

```bash
# Reset environment
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"seed": 42}'

# Create cargo
curl -X POST http://localhost:8000/cargo/add \
  -H "Content-Type: application/json" \
  -d '{
    "origin": 0,
    "destination": 5,
    "quantity": 100,
    "weight": 5000,
    "priority": 1
  }'

# Find fastest path
curl -X GET "http://localhost:8000/path?origin=0&destination=5&weight=time"

# Route for time minimization
curl -X POST http://localhost:8000/task1/route \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "task_1_time",
    "cargo_id": 0,
    "path": [0, 2, 5]
  }'

# Run steps
curl -X POST http://localhost:8000/step

# Evaluate
curl -X POST "http://localhost:8000/evaluate?task_type=task_1_time"
```

### Example 2: Task 3 Multimodal Workflow

```bash
# Create and split cargo
curl -X POST http://localhost:8000/cargo/split \
  -H "Content-Type: application/json" \
  -d '{
    "cargo_id": 0,
    "quantities": [50, 50]
  }'

# Route via rail (Task 3 - structurally distinct)
curl -X POST http://localhost:8000/task3/route \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "task_3_multimodal",
    "cargo_id": 1,
    "cargo_type": "rail",
    "path": [0, 2, 5],
    "split_at": [2]
  }'

# Route via truck
curl -X POST http://localhost:8000/task3/route \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "task_3_multimodal",
    "cargo_id": 2,
    "cargo_type": "truck",
    "path": [0, 4, 5]
  }'
```

## 7. Design Decisions

### Pydantic for Validation
- **Why**: Built-in validation, automatic OpenAPI schema generation
- **Benefit**: Type-safe request/response handling
- **Cost**: External dependency (acceptable trade-off)

### Single Environment Instance
- **Why**: Stateful simulations require persistent environment
- **How**: Module-level singleton with `get_env()`
- **Benefit**: Consistent state across requests

### Task-Specific Schemas
- **Why**: Structural distinctness forces different handling
- **How**: Separate Task1Action, Task2Action, Task3Action classes
- **Benefit**: Agents can't accidentally treat Task 3 like Tasks 1 & 2

### YAML for Configuration
- **Why**: Machine-readable, human-friendly, widely adopted
- **How**: Mapped to Python dataclasses at startup
- **Benefit**: Easy to update without code changes

## 8. Testing Commands

```bash
# Check syntax
python3 -m py_compile app/api/schemas.py app/main.py

# Start API server
python3 -m uvicorn app.main:app --reload

# Run tests
python3 test_api_layer.py
```

