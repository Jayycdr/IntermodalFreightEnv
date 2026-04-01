# IntermodalFreightEnv Frontend

Interactive Streamlit dashboard for testing and visualizing the freight environment.

## Quick Start

### Option 1: Docker Compose (Recommended)

Run both backend and frontend together:

```bash
docker-compose up
```

Then open:
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000

### Option 2: Manual Setup

**Terminal 1 - Start Backend:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Start Frontend:**
```bash
pip install -r frontend/requirements.txt
streamlit run frontend/dashboard.py
```

Then open: http://localhost:8501

## Features

### Dashboard (dashboard.py)

Interactive interface for:
- **Task Selection**: Choose between 3 distinct tasks
- **Environment Reset**: Control seed for reproducibility
- **State Visualization**: Real-time metrics display
- **Trajectory Builder**: Submit custom trajectories for grading
- **Metrics Tracking**: View scores, time, cost, and carbon emissions
- **Score History**: Chart of trajectory performance over time

**Key Sections:**
1. **Configuration** (Sidebar)
   - API URL connection
   - Task selection (Time / Cost / Multimodal)
   - Seed control for reproducibility

2. **Task Details**
   - Task name and description
   - Action schema documentation
   - Status indicators

3. **Environment State**
   - Current metrics (time, cost, carbon, weight)
   - Episode tracking
   - Full JSON state for debugging

4. **Trajectory Builder**
   - JSON trajectory input
   - Grading interface
   - Performance metrics

5. **Results Display**
   - Score visualization
   - Metrics comparison
   - Historical tracking

### Agent Analytics (agent_analytics.py)

Monitor agent learning across tasks:
- **Learning Curves**: Score progression
- **Metrics Comparison**: Time, cost, and carbon tracking
- **Summary Statistics**: Aggregate performance data
- **Interactive Visualization**: Plotly charts with hover data

## File Structure

```
frontend/
├── dashboard.py           # Main interactive dashboard
├── agent_analytics.py     # Learning analytics visualization
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## API Integration

The frontend communicates with the backend via HTTP:

### Endpoints Used

- **GET /health** - Verify API connectivity
- **POST /reset** - Initialize environment
- **GET /tasks** - Fetch task definitions
- **POST /grader** - Score trajectories

### Example Request (Trajectory Grading)

```json
{
  "task_id": 1,
  "trajectory": [
    {"action": "truck_to_rail", "observation": {...}},
    {"action": "rail_to_destination", "observation": {...}}
  ]
}
```

### Example Response

```json
{
  "score": 0.87,
  "metrics": {
    "accumulated_hours": 12.5,
    "accumulated_cost": 45.3,
    "accumulated_carbon": 8.2
  }
}
```

## Scoring Explained

The dashboard displays scores using the **Trilemma Formula**:

$$\text{Score} = 1 - (0.5 \times \frac{\text{time}}{t_{\text{max}}} + 0.3 \times \frac{\text{cost}}{c_{\text{max}}} + 0.2 \times \frac{\text{carbon}}{e_{\text{max}}})$$

**Weights:**
- **50%**: Time efficiency (delivery speed)
- **30%**: Economic cost
- **20%**: Environmental impact

Scores range from **0 (worst) to 1 (best)**

## Customization

### Change API URL
In the sidebar under "Configuration", modify the API URL to point to your backend instance.

### Modify Task Labels
Edit the task definition in the sidebar:
```python
format_func=lambda x: [
    "Task 1: Time Minimization",
    "Task 2: Cost Minimization", 
    "Task 3: Multimodal Balancing"
][x-1]
```

### Adjust Chart Colors
Colors are defined in each dashboard page. Modify the `colors` list:
```python
colors = ["#00cc00", "#0099ff", "#ff6600"]  # Green, Blue, Orange
```

## Troubleshooting

### "API Disconnected" Error
- Ensure backend is running: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Check API URL in sidebar matches backend location
- Default: `http://localhost:8000`

### "Invalid JSON Format" in Trajectory Builder
- Ensure trajectory is valid JSON array
- Example: `[{"action": "...", "observation": {...}}, ...]`
- Use online JSON validator if unsure

### Streamlit App Won't Start
- Install dependencies: `pip install -r frontend/requirements.txt`
- Check Python version: 3.11+ required
- Verify port 8501 is not in use

### Docker Compose Issues
- Rebuild images: `docker-compose build --no-cache`
- View logs: `docker-compose logs -f`
- Stop all: `docker-compose down`

## Performance Notes

- **Dashboard Load Time**: <2 seconds (after first load)
- **State Update**: Real-time (depends on backend response)
- **Chart Rendering**: <1 second for 100+ data points
- **Network**: Requires connectivity to backend (local or remote)

## Security Considerations

⚠️ **For Development Only**

The frontend includes:
- No authentication mechanism
- Full state exposure in expandable sections
- No rate limiting on requests

For production deployment, add:
- API key authentication
- Request rate limiting
- CORS configuration
- HTTPS enforcement

## Browser Support

Tested on:
- ✅ Chrome 120+
- ✅ Firefox 120+
- ✅ Safari 15+
- ✅ Edge 120+

Requires JavaScript enabled and WebSocket support.

## Support

For issues or feature requests:
1. Check troubleshooting section above
2. Verify backend is running and responding
3. Check browser console for errors (F12)
4. Review Streamlit documentation: https://docs.streamlit.io

---

**Built with Streamlit + Plotly for IntermodalFreightEnv**
