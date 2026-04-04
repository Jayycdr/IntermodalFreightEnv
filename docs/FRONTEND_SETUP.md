# Frontend Setup & Deployment Guide

## Overview

We've added an interactive **Streamlit dashboard** for testing and visualizing the IntermodalFreightEnv. This provides a user-friendly interface to:
- Test all 3 tasks interactively
- Visualize metrics and performance
- Monitor agent learning
- Replay trajectories
- See real-time scoring

## Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start Backend
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Start Frontend (New Terminal)
```bash
streamlit run frontend/dashboard.py
```

**Then open:** http://localhost:8501

---

## Architecture

### Backend (Your Existing Setup)
```
FastAPI Server (port 8000)
├── GET /health
├── POST /reset
├── GET /tasks
└── POST /grader
```

### Frontend (New)
```
Streamlit App (port 8501)
├── Dashboard (main interface)
│   ├── Task selection
│   ├── Environment state
│   ├── Trajectory builder
│   └── Metrics visualization
└── Agent Analytics (learning monitor)
    ├── Learning curves
    ├── Metrics comparison
    └── Summary statistics
```

### Communication
```
Browser → Streamlit Frontend (port 8501)
           ↓
         HTTP requests
           ↓
         FastAPI Backend (port 8000)
```

## Deployment Options

### Option A: Docker Compose (Recommended for Demo)

**Single command to run everything:**
```bash
docker-compose up
```

**What it does:**
- Builds backend Docker image
- Installs Streamlit in separate container
- Connects both services on private network
- Exposes ports 8000 (backend) and 8501 (frontend)

**Access:**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000

**Stop:**
```bash
docker-compose down
```

### Option B: Local Development

**Terminal 1 - Backend:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
streamlit run frontend/dashboard.py
```

**Advantages:**
- Hot reload on code changes
- Direct error visibility
- Easier debugging

### Option C: Remote Deployment

For cloud deployment (AWS, GCP, Heroku):

**Backend:**
```bash
docker build -t intermodal-backend .
docker run -p 8000:8000 intermodal-backend
```

**Frontend (Streamlit Cloud):**
```bash
# Deploy to Streamlit Cloud
streamlit run frontend/dashboard.py
# Then set API_URL=http://your-backend:8000 in config
```

---

## Frontend Features Explained

### 1. Dashboard (dashboard.py)

**Purpose:** Interactive testing interface

**Features:**

#### Configuration (Sidebar)
- **API URL**: Connect to any backend (local or remote)
- **Health Check**: Verify API connectivity status
- **Task Selection**: Choose between 3 tasks
- **Seed Control**: Reproducible results with fixed seeds
- **Reset Button**: Initialize environment

#### Task Details
- View selected task description
- See action schema
- Understand objectives

#### Environment State (Real-time)
Shows 4 key metrics:
- ⏱️ **Time (hours)**: Accumulated delivery time
- 💰 **Cost ($1000s)**: Accumulated transportation cost
- 🌍 **Carbon (tons CO2)**: Accumulated emissions
- 📦 **Weight (tons)**: Total cargo weight

#### Trajectory Builder
- Enter custom trajectories (JSON format)
- Submit for grading
- Get instant score feedback
- Track metrics per action

#### Results Visualization
- Score display with color coding
- Metrics breakdown
- Historical progression chart
- Compare multiple trajectories

### 2. Agent Analytics (agent_analytics.py)

**Purpose:** Analyze agent learning across tasks

**Features:**

#### Learning Simulation
- Run multiple episodes per task
- Track score progression
- Generate learning curves
- Compare task difficulty

#### Metrics Comparison
- Time consumption over episodes
- Cost optimization progress
- Carbon emission trends
- Task-specific patterns

#### Summary Statistics
- Average, min, max scores per task
- Performance comparison
- Efficiency metrics
- Task insights

---

## Usage Walkthrough

### Basic Workflow (5 minutes)

1. **Open Dashboard**
   ```
   Go to http://localhost:8501
   ```

2. **Select Task**
   ```
   Sidebar → Task Selection → Choose Task 1 (Time Minimization)
   ```

3. **Reset Environment**
   ```
   Sidebar → Check "Use fixed seed" → Set seed to 42
   Sidebar → Click "🔄 Reset Environment"
   ```

4. **View Current State**
   ```
   Main area shows environment metrics
   - Time, Cost, Carbon, Weight
   - Current location, destination
   ```

5. **Submit a Trajectory**
   ```
   Trajectory Builder section:
   - Copy sample: [{"action": "truck_to_rail", "observation": {}}]
   - Change action name (optional)
   - Click "📊 Grade Trajectory"
   ```

6. **See Results**
   ```
   Grading Results section shows:
   - Score [0-1]
   - Metrics breakdown
   - Historical chart
   ```

### Advanced: Agent Learning Simulation (10 minutes)

1. **Open Agent Analytics**
   ```
   Multi-page app: Click "Agent Analytics" in sidebar
   ```

2. **Configure Simulation**
   ```
   - Episodes per task: 20
   - Trajectories per episode: 3
   ```

3. **Run Simulation**
   ```
   Click "🚀 Start Learning Simulation"
   Monitor progress bar
   ```

4. **Analyze Results**
   ```
   View:
   - Score progression chart
   - Time/Cost/Carbon comparison
   - Summary statistics table
   ```

---

## API Integration Details

### How Frontend Calls Backend

**Example 1: Reset Environment**
```python
# Frontend sends this JSON to POST /reset
{
    "task_id": 1,
    "seed": 42
}

# Backend returns
{
    "current_location": "origin",
    "destination": "warehouse_a",
    "time_consumed": 0.0,
    "cost_consumed": 0.0,
    "carbon_emitted": 0.0,
    "cargo_weight": 10.0,
    "episode_id": "uuid-string",
    "current_step": 0,
    "task_id": 1
}
```

**Example 2: Grade Trajectory**
```python
# Frontend sends this JSON to POST /grader
{
    "task_id": 1,
    "trajectory": [
        {
            "action": "truck_dispatch",
            "observation": {
                "location": "origin",
                "destination": "warehouse_a"
            }
        }
    ]
}

# Backend returns
{
    "score": 0.75,
    "metrics": {
        "accumulated_hours": 5.2,
        "accumulated_cost": 20.1,
        "accumulated_carbon": 3.5
    }
}
```

### Error Handling

**Connection Failed**
```
Error: ❌ Cannot connect to API
Solution: Ensure backend is running on http://localhost:8000
```

**Invalid Trajectory**
```
Error: ⚠️ Invalid JSON format
Solution: Use valid JSON: [{"action": "...", "observation": {...}}, ...]
```

**Bad Request**
```
Error: Grading failed: 422 Unprocessable Entity
Solution: Check task_id (1-3) and trajectory schema
```

---

## Customization Guide

### Change API Connection
```python
# In sidebar Configuration
api_url = st.text_input("API URL", value="http://backend.example.com:8000")
```

### Modify Task Names
```python
# In dashboard.py, sidebar section
task_id = st.radio(
    "Select Task",
    options=[1, 2, 3],
    format_func=lambda x: [
        "Quick Delivery (Time)",
        "Budget Shipping (Cost)",
        "Green Logistics (Balanced)"
    ][x-1]
)
```

### Change Dashboard Theme
```python
# Add to dashboard.py
st.set_page_config(
    page_title="...",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Can change theme in ~/.streamlit/config.toml
# [theme]
# primaryColor = "#FF6B6B"
# backgroundColor = "#F0F2F6"
```

### Add New Metrics
```python
# In metrics display section
st.metric(
    "New Metric",
    value=state.get("new_metric"),
    delta=previous_value - current_value
)
```

---

## Troubleshooting

### Issue: "API Disconnected"

**Causes:**
1. Backend not running
2. Wrong API URL
3. Network connectivity

**Solutions:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not, start it
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# If port is in use
lsof -i :8000  # Find what's using it
kill -9 <PID>  # Kill process
```

### Issue: "Invalid JSON Format"

**Example Bad JSON:**
```
[{action: "truck", observation: {}}]  # Invalid: keys need quotes
```

**Example Good JSON:**
```
[{"action": "truck", "observation": {}}]  # Valid
```

**Validator:**
Use https://jsonlint.com/ to validate before pasting

### Issue: Streamlit Won't Start

```bash
# Try installing again
pip install streamlit==1.28.1 --force-reinstall

# Check Python version (need 3.8+)
python --version

# Try running from project root
cd /path/to/IntermodalFreightEnv
streamlit run frontend/dashboard.py
```

### Issue: Docker Compose Error

```bash
# Rebuild images
docker-compose build --no-cache

# View logs
docker-compose logs backend
docker-compose logs frontend

# Clean everything
docker-compose down -v
docker system prune -a
```

---

## Performance Optimization

### For Production

**Frontend Caching:**
```python
@st.cache_data
def get_tasks():
    return requests.get(f"{api_url}/tasks").json()
```

**Backend Scaling:**
```bash
# Run multiple workers
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

**Frontend Service:**
```bash
# Use Streamlit Cloud or tier
streamlit share frontend/dashboard.py
```

### For Development

**Hot Reload:**
```bash
# Backend auto-reloads with --reload flag
python -m uvicorn app.main:app --reload

# Frontend auto-reloads on file save
streamlit run frontend/dashboard.py
```

---

## File Structure

```
IntermodalFreightEnv/
├── app/
│   ├── main.py              # FastAPI server
│   └── ...
├── frontend/                # NEW
│   ├── dashboard.py         # Main interface
│   ├── agent_analytics.py   # Learning monitor
│   ├── requirements.txt     # Frontend dependencies
│   └── README.md           # Frontend docs
├── docker-compose.yml       # NEW (orchestration)
├── start.sh                # NEW (startup script)
├── requirements.txt         # Updated (added streamlit)
└── ...
```

---

## Next Steps

1. **Test with Backend**
   - Run backend: `uvicorn app.main:app --reload`
   - Run frontend: `streamlit run frontend/dashboard.py`
   - Test task 1, 2, 3 interactions

2. **Customize Dashboard**
   - Add custom CSS styling
   - Modify task descriptions
   - Add agency-specific branding

3. **Deploy Frontend**
   - Option A: Streamlit Cloud (free)
   - Option B: Docker container
   - Option C: Traditional hosting (Heroku, AWS, etc.)

4. **Integrate with CI/CD**
   - Add GitHub Actions workflow
   - Auto-deploy on push
   - Run tests before deployment

---

## Support & FAQ

**Q: Can I run frontend on different port?**
```bash
streamlit run frontend/dashboard.py --server.port 9000
```

**Q: How to connect to remote backend?**
```
In sidebar: API URL = http://your-domain.com:8000
```

**Q: Can I share the dashboard URL?**
```
Yes! Use Streamlit Cloud or deploy both services publicly
```

**Q: How to add authentication?**
```python
import streamlit_authenticator as stauth
# See: https://github.com/mkhorasani/Streamlit-Authenticator
```

---

## Documentation Links

- **Streamlit Docs:** https://docs.streamlit.io
- **Plotly Charts:** https://plotly.com/python/
- **FastAPI:** https://fastapi.tiangolo.com
- **Docker Compose:** https://docs.docker.com/compose

---

**Frontend built with ❤️ for IntermodalFreightEnv**
