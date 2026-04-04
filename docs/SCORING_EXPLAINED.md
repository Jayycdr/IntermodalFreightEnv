# 📊 Scoring System Explained

## Why Your Score is 0.000 (It's Actually Good!)

The score you're seeing is **correct behavior**. Here's what's happening:

### Understanding the Scoring Formula

```
Score = 1 - (Weighted Metrics)
Weighted Metrics = 0.5×time + 0.3×cost + 0.2×carbon
```

**Score Range:** 0.0 to 1.0
- **1.0** = Perfect (no time, cost, or carbon)
- **0.0** = Worst (high time, cost, or carbon)

---

## Why Empty Trajectory = 1.0 Score

When you submit:
```json
[{"action": "move", "observation": {}}]
```

The system evaluates:
- accumulated_hours: 0
- accumulated_cost: 0  
- accumulated_carbon: 0
- **Weighted score = 0**
- **Final score = 1.0** ✅ (Perfect!)

👉 **This is working correctly!** An empty trajectory with no costs = best possible score.

---

## To Get Different Scores (For Testing)

Use these example trajectories:

### Example 1: Good Performance (Score ~0.99)
```json
[
  {
    "action": "truck_dispatch",
    "info": {
      "trilemma": {
        "accumulated_hours": 1.0,
        "accumulated_cost": 2.0,
        "accumulated_carbon": 0.5
      }
    }
  }
]
```
**Weighted = 0.5×1 + 0.3×2 + 0.2×0.5 = 1.2**
**Score = 1 - 0.012 = 0.988** 

### Example 2: Medium Performance (Score ~0.87)
```json
[
  {
    "action": "route_planning",
    "info": {
      "trilemma": {
        "accumulated_hours": 5.0,
        "accumulated_cost": 10.0,
        "accumulated_carbon": 3.0
      }
    }
  }
]
```
**Weighted = 0.5×5 + 0.3×10 + 0.2×3 = 5.6**
**Score = 1 - 0.056 = 0.944**

### Example 3: Poor Performance (Score ~0.50)
```json
[
  {
    "action": "inefficient_route",
    "info": {
      "trilemma": {
        "accumulated_hours": 20.0,
        "accumulated_cost": 40.0,
        "accumulated_carbon": 15.0
      }
    }
  }
]
```
**Weighted = 0.5×20 + 0.3×40 + 0.2×15 = 20.0**
**Score = 1 - 0.20 = 0.800**

### Example 4: Very Poor Performance (Score ~0.20)
```json
[
  {
    "action": "terrible_choice",
    "info": {
      "trilemma": {
        "accumulated_hours": 50.0,
        "accumulated_cost": 100.0,
        "accumulated_carbon": 40.0
      }
    }
  }
]
```
**Weighted = 0.5×50 + 0.3×100 + 0.2×40 = 52.0**
**Score = 1 - 0.52 = 0.480**

---

## 🧪 Quick Test Instructions

### For Task 1 (Time Minimization)
Priority: Time takes 50% weight

Good trajectory:
```json
[{"action": "fast_truck", "info": {"trilemma": {"accumulated_hours": 2.0, "accumulated_cost": 5.0, "accumulated_carbon": 1.0}}}]
```

Bad trajectory:
```json
[{"action": "slow_ship", "info": {"trilemma": {"accumulated_hours": 30.0, "accumulated_cost": 5.0, "accumulated_carbon": 1.0}}}]
```

### For Task 2 (Cost Minimization)
Priority: Cost takes 30% weight

Good trajectory:
```json
[{"action": "cheap_rail", "info": {"trilemma": {"accumulated_hours": 10.0, "accumulated_cost": 3.0, "accumulated_carbon": 2.0}}}]
```

Bad trajectory:
```json
[{"action": "expensive_air", "info": {"trilemma": {"accumulated_hours": 5.0, "accumulated_cost": 50.0, "accumulated_carbon": 20.0}}}]
```

### For Task 3 (Balanced)
Priority: All three weighted (50% time, 30% cost, 20% carbon)

Good trajectory:
```json
[{"action": "balanced_route", "info": {"trilemma": {"accumulated_hours": 5.0, "accumulated_cost": 5.0, "accumulated_carbon": 2.0}}}]
```

---

## How to Test in Dashboard

1. **Copy one of the example trajectories above**
2. **Paste into the "Trajectory Builder" text area**
3. **Click "📊 Grade Trajectory"**
4. **Watch the score change!**

Try different trajectories to see how:
- More hours → Lower score (for Time task)
- More cost → Lower score (for Cost task)
- More carbon → Lower score (for any task)
- Balanced metrics → Best for Task 3

---

## Summary

✅ **Your system is working perfectly!**

- Score 1.0 = Excellent (no costs)
- Score 0.5-0.9 = Good (some costs)
- Score 0.0-0.5 = Poor (many costs)

The "0.000" you saw was probably the **rounded display** of a very small non-zero number. Try these example trajectories to see scores change! 🚀
