# 🤖 Agent Learning Guide - IntermodalFreightEnv

**Purpose:** This guide explains how to build learning agents that can train effectively in the IntermodalFreightEnv.

**Date:** April 4, 2026  
**Status:** ✅ Environment optimized for agent learning

---

## 📋 Quick Start

Your environment is now **fully optimized** for any RL agent to learn smoothly. Here's what we've implemented:

### ✅ What's Ready
- Proper reward function (trilemma-based)
- State space documentation (via `/state-descriptor` endpoint)
- Helper utilities for state normalization
- Task-specific action formatters
- Comprehensive logging utilities

---

## 🎯 Environment Overview

### What Agents Optimize
- **Time** (Task 1): Minimize transit hours
- **Cost** (Task 2): Minimize transportation cost  
- **Carbon** (Task 3): Minimize CO2 emissions
- **Trilemma** (Task 3): Balance all three metrics

### Reward Function
```
reward = -(0.5×time + 0.3×cost + 0.2×carbon)

Interpretation:
- Lower cost → Higher reward (closer to 0)
- Agents learn to minimize the weighted trilemma
- Standard RL setup where agent maximizes cumulative reward
```

### Episode Structure
```
1. Agent calls /reset → Environment resets
2. Agent calls /state → Gets current state
3. Agent selects action based on state
4. Agent calls /step with action → Gets (state, reward, done, info)
5. Repeat steps 2-4 until done=true (max 1000 steps)
```

---

## 🔌 API Endpoints for Agents

### 1. Get State Space Descriptor (Before Learning)
```bash
curl http://localhost:8000/state-descriptor | jq .
```

**Response:** Full specification of:
- State fields (types, ranges, units)
- Reward function details
- Action schema
- Episode mechanics

**Why it helps:** Agents understand exact observation/action spaces

---

### 2. Reset Environment (Start Episode)
```bash
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**
```json
{
  "state": {
    "step": 0,
    "active_cargos": 0,
    "completed_cargos": 0,
    "trilemma": {
      "accumulated_hours": 0.0,
      "accumulated_cost": 0.0,
      "accumulated_carbon": 0.0
    },
    "network": {...}
  },
  "message": "Environment reset successfully"
}
```

---

### 3. Get Current State (During Episode)
```bash
curl http://localhost:8000/state
```

**Response:** Current observation with all metrics

---

### 4. Execute Step (Agent Action)
```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "task_type": "task_1_time",
      "cargo_id": 0,
      "path": [0, 2, 5]
    }
  }'
```

**Response:**
```json
{
  "state": {...},           /* New state after action */
  "reward": -45.5,          /* Reward for this step */
  "done": false,            /* Episode finished? */
  "info": {                 /* Additional info */
    "step": 1,
    "completed_cargos": 0,
    "message": "Action executed"
  }
}
```

---

## 🧠 Building a Learning Agent

### Python Example: Simple Q-Learning Agent

```python
import requests
import numpy as np
from collections import defaultdict

class QLearningAgent:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.learning_rate = 0.1
        self.discount = 0.99
        self.epsilon = 0.1
        
        # Q-table: {state_key: {action: q_value}}
        self.q_table = defaultdict(lambda: defaultdict(float))
        
        # Learning statistics
        self.episode_rewards = []
        self.episode_steps = []
    
    def get_state_descriptor(self):
        """Get state space documentation"""
        resp = requests.get(f"{self.api_url}/state-descriptor")
        return resp.json()
    
    def reset(self):
        """Reset environment for new episode"""
        resp = requests.post(f"{self.api_url}/reset", json={})
        return resp.json()["data"]["state"]
    
    def get_state(self):
        """Get current environment state"""
        resp = requests.get(f"{self.api_url}/state")
        return resp.json()
    
    def take_step(self, action):
        """Execute one step with action"""
        resp = requests.post(
            f"{self.api_url}/step",
            json={"action": action},
            headers={"Content-Type": "application/json"}
        )
        data = resp.json()
        return (
            data["state"],
            data["reward"],
            data["done"],
            data["info"]
        )
    
    def state_to_key(self, state):
        """
        Convert state dict to hashable key for Q-table.
        
        For learning, you'll discretize continuous state:
        - Use disrupted nodes as state representation
        - Or bin continuous metrics (cost, time, carbon)
        """
        trilemma = state.get("trilemma", {})
        
        # Simple discretization: bin the trilemma metrics
        time_bin = int(trilemma.get("accumulated_hours", 0) / 10)  # 10h bins
        cost_bin = int(trilemma.get("accumulated_cost", 0) / 100)  # $100 bins
        
        # Create hashable state key
        return (time_bin, cost_bin, state.get("step", 0))
    
    def select_action(self, state):
        """Epsilon-greedy action selection"""
        state_key = self.state_to_key(state)
        
        # Get available paths from network
        available_actions = self.get_available_actions(state)
        
        if np.random.rand() < self.epsilon:
            # Explore: random action
            return available_actions[np.random.randint(len(available_actions))]
        else:
            # Exploit: best known action
            q_values = [self.q_table[state_key][a] for a in available_actions]
            best_idx = np.argmax(q_values)
            return available_actions[best_idx]
    
    def get_available_actions(self, state):
        """Get valid actions from current state"""
        network = state.get("network", {})
        actions = []
        
        # For each edge, create a simple routing action
        for edge in network.get("edges", []):
            if not edge.get("disabled", False):
                action = {
                    "task_type": "task_1_time",  # Time minimization task
                    "cargo_id": 0,
                    "path": [edge["source"], edge["target"]]
                }
                actions.append(action)
        
        return actions if actions else [{
            "task_type": "task_1_time",
            "cargo_id": 0,
            "path": [0, 1]
        }]
    
    def train(self, num_episodes=100):
        """Train the Q-learning agent"""
        
        for episode in range(num_episodes):
            state = self.reset()["state"]
            episode_reward = 0
            episode_steps = 0
            done = False
            
            while not done:
                # Select and execute action
                action = self.select_action(state)
                next_state, reward, done, info = self.take_step(action)
                episode_steps += 1
                episode_reward += reward
                
                # Q-learning update
                state_key = self.state_to_key(state)
                next_key = self.state_to_key(next_state)
                action_key = str(action)  # Convert action to string key
                
                old_q = self.q_table[state_key][action_key]
                
                if done:
                    target_q = reward
                else:
                    next_actions = self.get_available_actions(next_state)
                    next_action_qvalues = [
                        self.q_table[next_key][str(a)] 
                        for a in next_actions
                    ]
                    max_next_q = max(next_action_qvalues) if next_action_qvalues else 0
                    target_q = reward + self.discount * max_next_q
                
                # Update Q-table
                new_q = old_q + self.learning_rate * (target_q - old_q)
                self.q_table[state_key][action_key] = new_q
                
                state = next_state
            
            # Record episode stats
            self.episode_rewards.append(episode_reward)
            self.episode_steps.append(episode_steps)
            
            if (episode + 1) % 10 == 0:
                avg_reward = np.mean(self.episode_rewards[-10:])
                print(f"Episode {episode+1:3d} | "
                      f"Avg Reward: {avg_reward:8.2f} | "
                      f"Steps: {episode_steps:4d}")
        
        return self.episode_rewards


# Usage
if __name__ == "__main__":
    agent = QLearningAgent("http://localhost:8000")
    rewards = agent.train(num_episodes=50)
    print(f"\nTraining complete! Final avg reward: {np.mean(rewards[-5:]):.2f}")
```

---

## 🛠️ Using Helper Functions

The environment provides utilities in `app.utils.helpers` to make agent development easier:

### State Normalization
```python
from app.utils.helpers import normalize_state, state_to_vector

# Normalize state to [0, 1] range
normalized = normalize_state(
    state={"time": 50, "cost": 200, "carbon": 30},
    min_vals={"time": 0, "cost": 0, "carbon": 0},
    max_vals={"time": 100, "cost": 1000, "carbon": 100}
)
# Result: {"time": 0.5, "cost": 0.2, "carbon": 0.3}

# Convert to feature vector for neural networks
vector = state_to_vector(normalized, key_order=["time", "cost", "carbon"])
# Result: [0.5, 0.2, 0.3]
```

### Extracting Metrics
```python
from app.utils.helpers import extract_trilemma_metrics

metrics = extract_trilemma_metrics(state)
# Result: {"time": 45.5, "cost": 125.0, "carbon": 28.5}
```

### Building Action
```python
from app.utils.helpers import build_task1_action, build_task2_action

action1 = build_task1_action(cargo_id=0, path=[0, 2, 5])
action2 = build_task2_action(cargo_id=1, path=[0, 4, 5])
```

### Logging
```python
from app.utils.helpers import format_for_agent_logging

log_msg = format_for_agent_logging(
    episode=5, step=100, reward=-45.5, state=state, done=False
)
print(log_msg)
# Output: Episode   5 | Step  100 | Reward  -45.5000 | Time  50.00h | Cost $125.00 | Carbon  28.50t | Done False
```

---

## 📊 State Space Details

### Trilemma Metrics (Key for Learning)
```python
trilemma = {
    "accumulated_hours": 45.5,     # Total transit time (hours)
    "accumulated_cost": 125.0,     # Total cost (dollars)  
    "accumulated_carbon": 28.5,    # Total emissions (tons CO2)
}
```

### Network Representation
```python
network = {
    "nodes": [
        {"id": 0, "location": "Warehouse", "capacity": 1000.0},
        {"id": 1, "location": "Port A", "capacity": 500.0},
        # ... more nodes
    ],
    "edges": [
        {
            "source": 0,
            "target": 1,
            "time": 2.0,      # Hours
            "cost": 100.0,    # Dollars
            "carbon": 50.0,   # Tons
            "disabled": False # Is route disrupted?
        },
        # ... more edges
    ]
}
```

---

## 🎓 Advanced: Deep Learning with PyTorch/TensorFlow

### DQN Agent Skeleton
```python
import torch
import torch.nn as nn
from collections import deque
import random

class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        
        # Neural networks
        self.model = self._build_model()
        self.target_model = self._build_model()
    
    def _build_model(self):
        """Build Q-value neural network"""
        return nn.Sequential(
            nn.Linear(self.state_size, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, self.action_size)
        )
    
    def remember(self, state, action, reward, next_state, done):
        """Store transition in memory"""
        self.memory.append((state, action, reward, next_state, done))
    
    def replay(self, batch_size):
        """Learn from memory using experience replay"""
        if len(self.memory) < batch_size:
            return
        
        batch = random.sample(self.memory, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        # Convert to tensors
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones)
        
        # Current Q-values
        q_values = self.model(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # Target Q-values
        next_q_values = self.target_model(next_states).detach().max(1)[0]
        target_q = rewards + (1 - dones) * self.gamma * next_q_values
        
        # Compute loss and optimize
        loss = nn.MSELoss()(q_values, target_q)
        # ... optimizer step ...
```

---

## 📈 Performance Metrics to Track

### During Training
```python
metrics = {
    "episode_reward": sum(step_rewards),
    "avg_time_hours": trilemma["accumulated_hours"],
    "total_cost_dollars": trilemma["accumulated_cost"],
    "total_carbon_tons": trilemma["accumulated_carbon"],
    "cargos_delivered": state["completed_cargos"],
    "steps_taken": state["step"],
    "efficiency_score": (100 - trilemma_score) / 100,
}
```

### Convergence Indicators
- Reward increases over episodes
- Time/Cost/Carbon decrease
- Completed cargos increase
- Variance in rewards decreases

---

## 🐛 Debugging Tips

### 1. Check State Descriptor First
```bash
curl http://localhost:8000/state-descriptor | jq .
```
Understand exact state/action spaces before coding

### 2. Test Single Episode
```python
state = agent.reset()["state"]
action = {"task_type": "task_1_time", "cargo_id": 0, "path": [0, 1]}
next_state, reward, done, info = agent.take_step(action)
print(f"Reward: {reward}, Done: {done}")
```

### 3. Verify Reward Function
```python
# Reward should be:
# - Negative (because we minimize cost)
# - More negative for worse performance
# - Less negative (or zero) for good performance
assert reward < 0, "Reward should be negative (cost minimization)"
```

### 4. Check Network Connectivity
```python
network = state["network"]
print(f"Nodes: {len(network['nodes'])}")
print(f"Edges: {len(network['edges'])}")
# Should have 6 nodes, 17+ edges
```

---

## 🚀 Next Steps

1. **Run State Descriptor**
   ```bash
   curl http://localhost:8000/state-descriptor
   ```

2. **Test Basic Episode**
   ```python
   # See Q-Learning example above
   ```

3. **Train Agent**
   ```python
   agent = QLearningAgent()
   rewards = agent.train(num_episodes=100)
   ```

4. **Evaluate Performance**
   ```python
   import matplotlib.pyplot as plt
   plt.plot(rewards)
   plt.show()
   ```

---

## 📚 Resources in This Project

- **[API_AND_LEARNING_STATUS.md](API_AND_LEARNING_STATUS.md)** - API overview
- **[app/utils/helpers.py](../app/utils/helpers.py)** - Learning utilities
- **[app/constants.py](../app/constants.py)** - Environment configuration
- **[baseline/agent.py](../baseline/agent.py)** - Baseline agents for comparison

---

## 💡 Why This Setup Works Well

✅ **Standard RL Interface** - Environment follows OpenAI Gym conventions  
✅ **Clear Reward Signal** - Trilemma-based optimization is well-defined  
✅ **Normalized Metrics** - All rewards in consistent range  
✅ **Documentation** - `/state-descriptor` endpoint explains everything  
✅ **Helper Utilities** - Helper functions reduce agent code  
✅ **Network Structure** - 6 nodes with diverse edges enables interesting learning  
✅ **Task Variety** - 3 different optimization objectives  
✅ **Episode Mechanics** - Clear start/reset, step execution, done conditions  

---

**Your environment is ready for any agent to learn! 🎓**

Good luck with your learning agents! 🚀

