# 🧪 Quick Score Test - Copy & Paste

## The Issue You're Seeing

When you paste empty trajectories, the score stays the same because:
- Empty action = 0 time/cost/carbon spent = Perfect score (1.0)
- That's correct behavior!

## Test These Trajectories

### Test 1: Empty (Should show 1.0 or "100")
```json
[{"action": "idle"}]
```
⏝ Expected Score: **1.0** (Perfect - no costs)

---

### Test 2: Add Small Metrics (Should show ~0.99)
```json
[{"action": "move", "info": {"trilemma": {"accumulated_hours": 1.0, "accumulated_cost": 2.0, "accumulated_carbon": 0.5}}}]
```
⏝ Expected Score: **0.99** (Great - minimal costs)

---

### Test 3: Add Medium Metrics (Should show ~0.94)
```json
[{"action": "route", "info": {"trilemma": {"accumulated_hours": 5.0, "accumulated_cost": 10.0, "accumulated_carbon": 3.0}}}]
```
⏝ Expected Score: **0.94** (Good)

---

### Test 4: Add High Metrics (Should show ~0.48)
```json
[{"action": "inefficient", "info": {"trilemma": {"accumulated_hours": 50.0, "accumulated_cost": 100.0, "accumulated_carbon": 40.0}}}]
```
⏝ Expected Score: **0.48** (Poor)

---

## How to Test in Dashboard

**For each trajectory above:**

1. **Copy** the JSON (from ```json to ```)
2. **Select Task 1** in the sidebar
3. **Click Reset**
4. **Paste** into the "Trajectory Builder" text area
5. **Click "Grade Trajectory"**
6. **Check the score** in "Grading Results"

---

## What You Should See

| Test | Trajectory | Expected Score |
|------|-----------|---|
| 1 | Empty | 1.0 or 100 ✅ |
| 2 | Small metrics | 0.99 |
| 3 | Medium metrics | 0.94 |
| 4 | High metrics | 0.48 |

If scores are **different** for each test ✅ = System works!
If scores **stay the same** ❌ = Something wrong

---

## TRY THIS RIGHT NOW

Copy this trajectory:
```json
[{"action": "test", "info": {"trilemma": {"accumulated_hours": 5.0, "accumulated_cost": 10.0, "accumulated_carbon": 3.0}}}]
```

1. Go to http://localhost:8501
2. Reset Task 1
3. Paste it in
4. Grade it
5. **You should see Score = 0.94 (or similar, not 0)**

If you still see 0.000 after doing this, let me know!

---

## Understanding Score

```
Score = 1 - (0.5×hours + 0.3×cost + 0.2×carbon)

Examples:
- 0 hours, 0 cost, 0 carbon → Score = 1.0 (Perfect!)
- 5 hours, 10 cost, 3 carbon → Score = 0.94 (Good)
- 50 hours, 100 cost, 40 carbon → Score = 0.48 (Poor)
```

The lower your time/cost/carbon → The higher your score! 🎯

