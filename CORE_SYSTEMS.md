# Core Systems Implementation

## Overview

This document describes the implementation of the core systems for IntermodalFreightEnv, including the network graph structure, the environment state machine, cargo management, and the disruption engine.

## 1. Graph Structure (`app/engine/graph.py`)

### Design: Dictionary-Based Adjacency List

The `FreightNetwork` class uses a dictionary-based adjacency list representation for efficient graph operations:

```
adjacency_list = {
    node_id: {
        neighbor_id: EdgeData(time, cost, carbon),
        ...
    },
    ...
}
```

### EdgeData Class

Each edge contains the **"Trilemma"** attributes representing the three competing objectives:

- **time**: Hours required to traverse this edge
- **cost**: Monetary cost in dollars
- **carbon**: CO2 emissions in kilograms

### Key Methods

| Method | Purpose |
|--------|---------|
| `add_node(node_id, **attributes)` | Add a location node |
| `add_edge(source, target, time, cost, carbon)` | Add a route with trilemma attributes |
| `get_shortest_path(source, target, weight)` | Find optimal path (by time/cost/carbon) using Dijkstra's algorithm |
| `get_available_nodes()` | Get non-disabled nodes (for disruptions) |
| `get_available_edges()` | Get non-disabled edges (for disruptions) |
| `disable_node(node_id)` | Disable a node (disruption engine) |
| `disable_edge(source, target)` | Disable an edge (disruption engine) |

### Shortest Path Algorithm

Implements Dijkstra's algorithm with support for three weight metrics:
- **time**: Minimize transit time (fast routes)
- **cost**: Minimize monetary cost (cheap routes)
- **carbon**: Minimize carbon emissions (green routes)

This enables the agent to optimize for different objectives while handling the trilemma.

## 2. Core Environment (`app/engine/core_env.py`)

### State Machine Architecture

The `FreightEnvironment` class implements a complete state machine:

```
reset() → initialize network with disruptions
    ↓
add_cargo() → create cargo shipments
    ↓
split_cargo() → optionally split shipments
    ↓
route_cargo() → assign paths to cargos
    ↓
step() → simulate transit and accumulate costs
    ↓
repeat → until max_steps or goal achieved
```

### Core Classes

#### Cargo
Represents a shipment with:
- Origin/destination nodes
- Quantity and weight
- Priority level (1=low, 2=medium, 3=high)
- Optional deadline

#### TrilemmaCounters
Tracks accumulated costs across the episode:
- `accumulated_hours`: Total transit time
- `accumulated_cost`: Total monetary cost
- `accumulated_carbon`: Total CO2 emissions

#### CargoState
Tracks in-transit cargo:
- Current location in the network
- Remaining quantity
- Planned path
- Position on path
- Accumulated trilemma costs for this shipment

### Key Methods

| Method | Purpose |
|--------|---------|
| `setup_network(config)` | Initialize network with nodes/edges |
| `reset()` | Reset environment and apply disruptions |
| `add_cargo(origin, dest, qty, weight)` | Create a new cargo |
| `split_cargo(cargo_id, quantities)` | Split cargo into multiple shipments |
| `route_cargo(cargo_id, path)` | Assign a path to a cargo |
| `step(action)` | Simulate one timestep |
| `get_state()` | Get current environment state |
| `get_trilemma()` | Get current trilemma counters |

## 3. Cargo Management

### Adding Cargos
```python
cargo = env.add_cargo(
    origin=0,
    destination=5,
    quantity=100.0,
    weight=5000.0,
    priority=2
)
```

### Splitting Cargos
Split a cargo into multiple shipments for different routes/modes:
```python
splits = env.split_cargo(cargo_id, [60.0, 40.0])
# Creates two new cargos with proportional weight
```

### Routing Cargos
Assign a specific path from origin to destination:
```python
path = env.network.get_shortest_path(origin, destination, weight='time')
env.route_cargo(cargo_id, path)
```

## 4. Disruption Engine

The disruption engine simulates real-world disruptions (accidents, weather, infrastructure failures) by probabilistically disabling nodes and edges during `reset()`.

### How It Works
1. **Seeded Randomness**: Uses the environment seed for reproducible disruptions
2. **Node Disruptions**: Each node has `disruption_probability` chance of being disabled
3. **Edge Disruptions**: Each edge has `disruption_probability` chance of being disabled
4. **Pathfinding**: Shortest path algorithms automatically avoid disabled nodes/edges

### Example
```python
config = EnvironmentConfig(
    disruption_probability=0.1,  # 10% of nodes/edges disabled
    seed=42  # Reproducible disruptions
)
env = FreightEnvironment(config)
state = env.reset()  # Disruptions applied here

print(env.network.disabled_nodes)   # {1, 3, 5}
print(env.network.disabled_edges)   # {(0, 1), (2, 3)}
```

## 5. State Transitions

### Step Function
Each call to `step()`:
1. **Move Cargos**: Advance active cargos along their paths
2. **Accumulate Costs**: Add time/cost/carbon to trilemma counters
3. **Complete Deliveries**: Mark cargos as delivered when reaching destination
4. **Calculate Reward**: Based on deliveries and cost penalties
5. **Return Info**: Current state, reward, episode status

### Example Simulation
```python
state = env.reset()

for step in range(10):
    state, reward, done, info = env.step({})
    
    print(f"Step {step}:")
    print(f"  Active cargos: {info['active_cargos']}")
    print(f"  Completed: {info['completed_cargos']}")
    print(f"  Trilemma: {info['trilemma']}")
    
    if done:
        break
```

## 6. The Trilemma Optimization Problem

The environment naturally presents the "Trilemma" challenge:

### Three Competing Objectives
1. **Time**: Minimize transit hours (fast delivery)
2. **Cost**: Minimize operational cost (cheap routes)
3. **Carbon**: Minimize environmental impact (green logistics)

### Tradeoffs Example
Given three routes from City 0 to City 3:

| Route | Time | Cost | Carbon | Best For |
|-------|------|------|--------|----------|
| Fast Route | 5h | $200 | 20kg | Time |
| Cheap Route | 15h | $150 | 150kg | Cost |
| Green Route | 12h | $180 | 30kg | Carbon |

Agents must learn to balance these objectives based on:
- Cargo priority
- Delivery deadlines
- Environmental constraints
- Budget constraints

## 7. API Example: Complete Workflow

```python
from app.engine.core_env import FreightEnvironment, EnvironmentConfig

# 1. Create environment
config = EnvironmentConfig(max_steps=100, disruption_probability=0.15, seed=42)
env = FreightEnvironment(config)

# 2. Setup network
network_config = {
    "nodes": [
        {"id": 0, "location": "Warehouse"},
        {"id": 1, "location": "Port"},
        {"id": 2, "location": "Rail Hub"},
        {"id": 3, "location": "Destination"},
    ],
    "edges": [
        {"source": 0, "target": 1, "time": 2.0, "cost": 100.0, "carbon": 30.0},
        {"source": 0, "target": 2, "time": 1.5, "cost": 80.0, "carbon": 20.0},
        {"source": 1, "target": 3, "time": 3.0, "cost": 150.0, "carbon": 50.0},
        {"source": 2, "target": 3, "time": 4.0, "cost": 120.0, "carbon": 40.0},
    ],
}
env.setup_network(network_config)

# 3. Reset with disruptions applied
state = env.reset()

# 4. Create and route cargos
cargo = env.add_cargo(origin=0, destination=3, quantity=100.0, weight=5000.0)
path = env.network.get_shortest_path(0, 3, weight='cost')
env.route_cargo(cargo.cargo_id, path)

# 5. Run simulation
for _ in range(100):
    state, reward, done, info = env.step({})
    if done:
        break

print(f"Reward: {reward}")
print(f"Trilemma: {env.get_trilemma().to_dict()}")
```

## 8. Testing

Run the comprehensive test suite:
```bash
python3 test_core_systems.py
```

Tests cover:
- Graph structure and pathfinding (all three weight metrics)
- Disruption engine and disabled node handling
- Cargo creation and management
- Cargo splitting
- State transitions and trilemma tracking
- Multi-objective optimization tradeoffs

## 9. Design Decisions

### Dictionary vs NetworkX
- **Chosen**: Dictionary-based adjacency list
- **Reason**: Direct control, efficient for specific operations, simpler disruption handling
- **Benefit**: Explicit trilemma edge attributes without wrapping

### Standard Library Random
- **Chosen**: `random` module instead of `numpy`
- **Reason**: Reduces dependencies, sufficient for disruption engine
- **Note**: Can upgrade to numpy if needed for performance

### Dijkstra's Algorithm
- **Chosen**: Custom implementation
- **Reason**: Supports multi-objective pathfinding, handles disruptions naturally
- **Complexity**: O((V + E) log V) with priority queue

### Trilemma as Episode-Level Counter
- **Chosen**: Single accumulating counter per episode
- **Reason**: Agents must balance multiple objectives holistically
- **Benefit**: Natural reward function: deliveries - costs

