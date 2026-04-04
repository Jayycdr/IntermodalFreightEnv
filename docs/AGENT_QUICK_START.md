# 🚀 Quick Start - Build Your First Learning Agent

**For:** Developers who want to train agents in IntermodalFreightEnv  
**Time:** 5-10 minutes to get running  
**Difficulty:** Beginner-friendly

---

## 1️⃣ Understand the Environment (2 min)

```bash
# Query what the environment offers
curl http://localhost:8000/state-descriptor | jq '.data.reward_function'
```

**Key Points:**
- Reward = -(0.5×time + 0.3×cost + 0.2×carbon)
- Lower cost = higher reward (less negative)
- Agent goal: minimize trilemma metrics

---

## 2️⃣ Set Up Agent (2 min)

```python
import requests
import numpy as np
from collections import defaultdict

class SimpleLearningAgent:
    def __init__(self, api="http://localhost:8000"):
        self.api = api
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.alpha = 0.1      # Learning rate
        self.gamma = 0.99     # Discount factor
    
    def reset(self):
        resp = requests.post(f"{self.api}/reset", json={})
        return resp.json()["data"]["state"]
    
    def step(self, action):
        resp = requests.post(
            f"{self.api}/step",
            json={"action": action},
            headers={"Content-Type": "application/json"}
        )
        data = resp.json()
        return data["state"], data["reward"], data["done"], data["info"]
```

---

## 3️⃣ Run Training Loop (5 min)

```python
agent = SimpleLearningAgent()

for episode in range(10):
    state = agent.reset()
    total_reward = 0
    done = False
    
    while not done:
        # Simple action: follow edge 0→1
        action = {
            "task_type": "task_1_time",
            "cargo_id": 0,
            "path": [0, 1]
        }
        
        next_state, reward, done, info = agent.step(action)
        total_reward += reward
        state = next_state
    
    print(f"Episode {episode+1:2d}: Total Reward = {total_reward:8.2f}")
```

**Output:**
```
Episode  1: Total Reward =  -425.50
Episode  2: Total Reward =  -425.50
Episode  3: Total Reward =  -425.50
...
```

---

## 4️⃣ Add Learning Logic (3 min)

```python
class LearningAgent:
    def __init__(self, api="http://localhost:8000"):
        self.api = api
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.alpha = 0.1
        self.gamma = 0.99
        self.epsilon = 0.1
    
    def state_to_key(self, state):
        """Convert state to Q-table key"""
        trilemma = state.get("trilemma", {})
        time_bin = int(trilemma.get("accumulated_hours", 0) / 100)
        cost_bin = int(trilemma.get("accumulated_cost", 0) / 1000)
        return (time_bin, cost_bin)
    
    def select_action(self, state, available_actions):
        """Epsilon-greedy action selection"""
        state_key = self.state_to_key(state)
        
        if np.random.rand() < self.epsilon:
            return available_actions[np.random.randint(len(available_actions))]
        else:
            q_values = [self.q_table[state_key][str(a)] for a in available_actions]
            return available_actions[np.argmax(q_values)]
    
    def learn(self, episodes=50):
        rewards = []
        
        for episode in range(episodes):
            state = self.reset()
            episode_reward = 0
            done = False
            
            # Simple action set: all edges
            actions = [
                {"task_type": "task_1_time", "cargo_id": 0, "path": [0, 1]},
                {"task_type": "task_1_time", "cargo_id": 0, "path": [0, 2]},
                {"task_type": "task_1_time", "cargo_id": 0, "path": [1, 5]},
            ]
            
            while not done:
                action = self.select_action(state, actions)
                next_state, reward, done, info = self.step(action)
                
                # Q-learning update
                state_key = self.state_to_key(state)
                next_key = self.state_to_key(next_state)
                action_str = str(action)
                
                old_q = self.q_table[state_key][action_str]
                next_q_values = [
                    self.q_table[next_key][str(a)] for a in actions
                ]
                max_next_q = max(next_q_values) if next_q_values else 0
                
                new_q = old_q + self.alpha * (
                    reward + self.gamma * max_next_q - old_q
                )
                self.q_table[state_key][action_str] = new_q
                
                episode_reward += reward
                state = next_state
            
            rewards.append(episode_reward)
            
            if (episode + 1) % 10 == 0:
                avg = np.mean(rewards[-10:])
                print(f"Episode {episode+1:3d}: Avg Reward = {avg:8.2f}")
        
        return rewards
```

**Run Training:**
```python
agent = LearningAgent()
rewards = agent.learn(episodes=50)

# Plot results
import matplotlib.pyplot as plt
plt.plot(rewards)
plt.xlabel("Episode")
plt.ylabel("Total Reward")
plt.title("Agent Learning Progress")
plt.show()
```

---

## 5️⃣ Verify Learning Works

✅ **Rewards improve** as agent learns  
✅ **Variance decreases** (more stable behavior)  
✅ **Average reward increases** (less negative)  

Example learning curve:
```
Episode   1: Avg Reward = -425.50
Episode  10: Avg Reward = -390.25
Episode  20: Avg Reward = -320.10  ← Lower = Better!
Episode  30: Avg Reward = -280.50
Episode  40: Avg Reward = -250.75
Episode  50: Avg Reward = -225.00
```

---

## 🎯 Key Points

| Concept | Value |
|---------|-------|
| **Reward Meaning** | - = cost, lower = better |
| **Max Episode Length** | 1000 steps |
| **State Update** | Every step |
| **Learning Signal** | Reward per step |
| **Episode Reset** | Done condition |

---

## 🛠️ Common Issues & Fixes

### Issue: "Connection refused"
```python
# Make sure API is running first!
# In terminal:
cd /home/harsh/CodeWithHarsh/ML-Projects/IntermodalFreightEnv
.venv/bin/python -m uvicorn app.main:app --port 8000
```

### Issue: "All actions are same"
```python
# Create varied action set from network edges
network = state.get("network", {})
actions = [
    {"task_type": "task_1_time", "cargo_id": 0, "path": [e["source"], e["target"]]}
    for e in network.get("edges", [])[:10]  # First 10 edges
]
```

### Issue: "Reward always same"
```python
# Make sure you're taking different actions
# Most actions should have slightly different costs
# Reward reflects that
```

---

## 📚 Next Level Topics

### 1. Deep Q-Learning (DQN)
Replace Q-table with neural network:
```python
import torch
import torch.nn as nn

model = nn.Sequential(
    nn.Linear(4, 128),    # 4 state features
    nn.ReLU(),
    nn.Linear(128, 10)    # 10 actions
)
```

### 2. Policy Gradient
Train policy directly:
```python
log_prob = policy(state).log()
loss = -log_prob * advantage
loss.backward()
```

### 3. Multi-Task Learning
Train on all 3 tasks:
```python
for task in ["task_1_time", "task_2_cost", "task_3_multimodal"]:
    # Train agent for this task
```

---

## 🚀 Run This Now!

**Complete code to copy-paste:**

```python
import requests
import numpy as np
from collections import defaultdict

class Agent:
    def __init__(self):
        self.api = "http://localhost:8000"
        self.q = defaultdict(lambda: defaultdict(float))
    
    def reset(self):
        return requests.post(f"{self.api}/reset", json={}).json()["data"]["state"]
    
    def step(self, action):
        r = requests.post(f"{self.api}/step", json={"action": action}).json()
        return r["state"], r["reward"], r["done"], r["info"]
    
    def train(self, episodes=20):
        for ep in range(episodes):
            s = self.reset()
            R = 0
            while True:
                a = {"task_type": "task_1_time", "cargo_id": 0, "path": [0, 1]}
                s, r, d, _ = self.step(a)
                R += r
                if d: break
            print(f"Ep {ep+1:2d}: {R:8.2f}")

agent = Agent()
agent.train(20)
```

**Expected Output:**
```
Ep  1: -425.50
Ep  2: -425.50
...
Ep 20: -425.50
```

All episodes similar because agent takes same action. Add learning logic to improve!

---

## ✅ Checklist

- [ ] API running on port 8000
- [ ] Query `/state-descriptor` works
- [ ] Reset endpoint works
- [ ] Step endpoint returns reward
- [ ] Agent code runs without errors
- [ ] Rewards are negative (good sign!)
- [ ] Plan next steps (DQN? Policy gradient?)

---

**You're ready to train! 🎓**

Need help? Check:
- `/state-descriptor` endpoint (full spec)
- `docs/AGENT_LEARNING_GUIDE.md` (complete guide)
- `app/utils/helpers.py` (utility functions)

Happy training! 🚀

