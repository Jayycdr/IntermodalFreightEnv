# 🚚 Transportation Modes System

## Overview

The grading system now supports **4 transportation modes** with realistic characteristics:

- **Truck** 🚛 - Fast, flexible
- **Ship** ⛵ - Cheap, slow, high capacity
- **Rail** 🚂 - Balanced, high capacity
- **Flight** ✈️ - Ultra-fast, expensive

Each mode has different **time**, **cost**, and **carbon** characteristics per 100 km.

---

## Mode Characteristics

### 🚛 TRUCK
```
Speed:      80 km/h
Cost:       $15 per 100 km
Carbon:     2.5 kg CO2 per 100 km
Capacity:   25 tons
Min Dist:   50 km
```
**Best For:** Short-medium distances, time-sensitive cargo

### 🚂 RAIL  
```
Speed:      90 km/h
Cost:       $8 per 100 km
Carbon:     0.8 kg CO2 per 100 km
Capacity:   100 tons
Min Dist:   200 km
```
**Best For:** Medium-long distances, bulk cargo

### ⛵ SHIP
```
Speed:      40 km/h
Cost:       $5 per 100 km
Carbon:     0.3 kg CO2 per 100 km
Capacity:   500 tons
Min Dist:   500 km
```
**Best For:** Long intercontinental routes, cost-conscious

### ✈️ FLIGHT
```
Speed:      900 km/h
Cost:       $100 per 100 km
Carbon:     15 kg CO2 per 100 km
Capacity:   50 tons
Min Dist:   300 km
```
**Best For:** Ultra-urgent, long-distance delivery

---

## How to Use in Trajectories

### Format: Mode-Based Action

```json
[{
  "action": {
    "mode": "truck",
    "distance": 500,
    "cargo_tons": 10
  }
}]
```

The grader will automatically:
1. Look up the mode characteristics
2. Calculate time based on distance/speed
3. Calculate cost based on distance/rate
4. Calculate carbon based on distance/emissions
5. Apply to your score

---

## Test Examples

### Example 1: Quick Truck Delivery (Task 1 - Time)
**Use Case:** Minimize time for urgent cargo

```json
[{"action": {"mode": "truck", "distance": 300, "cargo_tons": 5}}]
```

**Calculated Metrics:**
- Time: 300 ÷ 80 = **3.75 hours** ✅ (fast)
- Cost: 300 × $0.15 = **$45** (medium)
- Carbon: 300 × 0.025 = **7.5 kg** (high)

**Score Impact:** Good for Task 1, bad for Task 3 (high carbon)

---

### Example 2: Cheap Rail Transport (Task 2 - Cost)
**Use Case:** Minimize cost for bulk cargo

```json
[{"action": {"mode": "rail", "distance": 800, "cargo_tons": 50}}]
```

**Calculated Metrics:**
- Time: 800 ÷ 90 = **8.89 hours** (medium)
- Cost: 800 × $0.08 = **$64** ✅ (cheap)
- Carbon: 800 × 0.008 = **6.4 kg** (low)

**Score Impact:** Good for Tasks 2 & 3

---

### Example 3: Eco-Friendly Ship (Task 3 - Balanced)
**Use Case:** Balance all metrics with environmental focus

```json
[{"action": {"mode": "ship", "distance": 2000, "cargo_tons": 100}}]
```

**Calculated Metrics:**
- Time: 2000 ÷ 40 = **50 hours** (slow but OK for long distance)
- Cost: 2000 × $0.05 = **$100** (cheap!)
- Carbon: 2000 × 0.003 = **6 kg** ✅ (best!)

**Score Impact:** Excellent for Tasks 2 & 3, poor for Task 1

---

### Example 4: Premium Express Flight
**Use Case:** Urgent delivery regardless of cost

```json
[{"action": {"mode": "flight", "distance": 3000, "cargo_tons": 20}}]
```

**Calculated Metrics:**
- Time: 3000 ÷ 900 = **3.33 hours** ✅ (fastest)
- Cost: 3000 × $1.0 = **$3000** ❌ (very expensive)
- Carbon: 3000 × 0.15 = **450 kg** ❌ (worst)

**Score Impact:** Only good for Task 1 if time is critical

---

## Multimodal Strategy (Task 3)

**Combine multiple modes in one trajectory:**

```json
[
  {
    "action": {"mode": "truck", "distance": 100, "cargo_tons": 50}
  },
  {
    "action": {"mode": "rail", "distance": 600, "cargo_tons": 50}
  },
  {
    "action": {"mode": "truck", "distance": 100, "cargo_tons": 50}
  }
]
```

**Total Metrics:**
- Truck (100km): 1.25h, $15, 2.5kg
- Rail (600km): 6.67h, $48, 4.8kg
- Truck (100km): 1.25h, $15, 2.5kg
- **Total: 9.17 hours, $78 cost, 9.8 kg carbon**

This is **balanced and efficient**! Good for Task 3.

---

## API Endpoints

### Get Mode Characteristics
```bash
curl http://localhost:8000/modes
```

Response shows all modes with their speed, cost, carbon characteristics.

### Get Example Trajectory
```bash
curl -X POST http://localhost:8000/modes/example \
  -H "Content-Type: application/json" \
  -d '{"mode": "ship", "distance_km": 1000, "cargo_tons": 100}'
```

Response: Example trajectory with calculated metrics.

---

## Strategy by Task

### Task 1: Time Minimization
**→ Use TRUCK for short distances**

```json
[{"action": {"mode": "truck", "distance": 200, "cargo_tons": 10}}]
```
Fast delivery, medium metrics.

### Task 2: Cost Minimization  
**→ Use SHIP for long distances or RAIL for medium**

```json
[{"action": {"mode": "ship", "distance": 2000, "cargo_tons": 50}}]
```
Cheapest option, ignoring time/carbon.

### Task 3: Balanced Multimodal
**→ Combine RAIL + TRUCK**

```json
[
  {"action": {"mode": "truck", "distance": 200, "cargo_tons": 50}},
  {"action": {"mode": "rail", "distance": 800, "cargo_tons": 50}},
  {"action": {"mode": "truck", "distance": 200, "cargo_tons": 50}}
]
```
Good balance of all three metrics.

---

## Scoring Formula

```
Score = 1 - (0.5×hours + 0.3×cost + 0.2×carbon)

Where:
- hours = time divided by max time
- cost = cost divided by max cost
- carbon = carbon divided by max carbon
```

**Higher score = better performance** ✅

---

## Testing in Dashboard

1. **Open:** http://localhost:8501
2. **Select Task 1** (or 2 or 3)
3. **Click Reset**
4. **Paste a trajectory** (from examples above)
5. **Click Grade Trajectory**
6. **Compare scores** for different modes!

---

## Example Trajectories (Copy-Paste Ready)

### Truck (Fast, Medium Cost)
```json
[{"action": {"mode": "truck", "distance": 500, "cargo_tons": 15}}]
```

### Rail (Balanced)
```json
[{"action": {"mode": "rail", "distance": 800, "cargo_tons": 40}}]
```

### Ship (Cheap)
```json
[{"action": {"mode": "ship", "distance": 2000, "cargo_tons": 100}}]
```

### Flight (Ultra-Fast)
```json
[{"action": {"mode": "flight", "distance": 1500, "cargo_tons": 10}}]
```

### Multimodal (Best Balanced)
```json
[
  {"action": {"mode": "truck", "distance": 200, "cargo_tons": 50}},
  {"action": {"mode": "rail", "distance": 600, "cargo_tons": 50}},
  {"action": {"mode": "truck", "distance": 200, "cargo_tons": 50}}
]
```

---

## Trade-Off Matrix

| Mode | Speed | Cost | Carbon | Capacity | Best For |
|------|-------|------|--------|----------|----------|
| Truck | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | Fast delivery |
| Rail | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Balanced |
| Ship | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Long haul |
| Flight | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐ | Urgent |

---

## Next Steps

1. ✅ Understand mode characteristics
2. ✅ Test different modes in dashboard
3. ✅ Compare scores for each task
4. ✅ Design optimal multimodal routes
5. ✅ Submit best trajectories

Good luck! 🚀
