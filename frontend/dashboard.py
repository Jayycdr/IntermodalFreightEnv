#!/usr/bin/env python3
"""
IntermodalFreightEnv Frontend Dashboard

Interactive Streamlit interface for testing and visualizing the freight environment.
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="IntermodalFreightEnv Dashboard",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .success {
        color: #00cc00;
        font-weight: bold;
    }
    .error {
        color: #ff4444;
        font-weight: bold;
    }
    .warning {
        color: #ffaa00;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"
if "episode_id" not in st.session_state:
    st.session_state.episode_id = None
if "current_task" not in st.session_state:
    st.session_state.current_task = 1
if "current_state" not in st.session_state:
    st.session_state.current_state = None
if "trajectory" not in st.session_state:
    st.session_state.trajectory = []
if "metrics_history" not in st.session_state:
    st.session_state.metrics_history = []


def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{st.session_state.api_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_tasks():
    """Fetch available tasks from API"""
    try:
        response = requests.get(f"{st.session_state.api_url}/tasks", timeout=5)
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch tasks: {e}")
        return None


def reset_environment(task_id, seed=None):
    """Reset environment to initial state"""
    try:
        payload = {"task_id": task_id}
        if seed is not None:
            payload["seed"] = seed
        
        response = requests.post(
            f"{st.session_state.api_url}/reset",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            state = response.json()
            st.session_state.current_state = state
            st.session_state.trajectory = []
            st.session_state.metrics_history = []
            st.session_state.episode_id = state.get("episode_id")
            return state
        else:
            st.error(f"Reset failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to reset environment: {e}")
        return None


def grade_trajectory(task_id, trajectory):
    """Submit trajectory for grading"""
    try:
        payload = {
            "task_id": task_id,
            "trajectory": trajectory
        }
        
        response = requests.post(
            f"{st.session_state.api_url}/grader",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Grading failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to grade trajectory: {e}")
        return None


# Header
st.title("🚚 IntermodalFreightEnv Dashboard")
st.markdown("**Interactive testing platform for multimodal freight routing**")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    api_url = st.text_input(
        "API URL",
        value=st.session_state.api_url,
        placeholder="http://localhost:8000"
    )
    st.session_state.api_url = api_url
    
    # Health check
    if check_api_health():
        st.success("✅ API Connected")
    else:
        st.error("❌ API Disconnected")
    
    st.divider()
    
    # Task selection
    st.subheader("Task Selection")
    task_id = st.radio(
        "Select Task",
        options=[1, 2, 3],
        format_func=lambda x: [
            "Task 1: Time Minimization",
            "Task 2: Cost Minimization",
            "Task 3: Multimodal Balancing"
        ][x-1]
    )
    st.session_state.current_task = task_id
    
    # Seed control
    st.subheader("Environment Control")
    use_seed = st.checkbox("Use fixed seed for reproducibility")
    seed = None
    if use_seed:
        seed = st.number_input("Seed", value=42, min_value=0)
    
    # Reset button
    if st.button("🔄 Reset Environment", use_container_width=True):
        with st.spinner("Resetting..."):
            reset_environment(task_id, seed)
            st.success("Environment reset!")
            st.rerun()


# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📊 Task {st.session_state.current_task}")
    
    # Fetch and display tasks
    tasks_data = get_tasks()
    if tasks_data:
        tasks = tasks_data.get("tasks", [])
        if st.session_state.current_task <= len(tasks):
            task = tasks[st.session_state.current_task - 1]
            
            with st.expander("Task Details", expanded=True):
                col_task1, col_task2 = st.columns(2)
                
                with col_task1:
                    st.write(f"**Name:** {task.get('name', 'N/A')}")
                    st.write(f"**ID:** {task.get('task_id', 'N/A')}")
                
                with col_task2:
                    st.write(f"**Description:** {task.get('description', 'N/A')}")
                
                st.write("**Action Schema:**")
                st.json(task.get("action_schema", {}))

with col2:
    st.subheader("📍 Status")
    if st.session_state.current_state:
        state = st.session_state.current_state
        
        st.metric("Episode ID", state.get("episode_id", "N/A")[:8] + "...")
        st.metric("Current Step", state.get("current_step", 0))
        st.metric("Destination", state.get("destination", "N/A"))


# Current Environment State
st.divider()
st.subheader("🔍 Current Environment State")

if st.session_state.current_state:
    state = st.session_state.current_state
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "⏱️ Time (hours)",
            f"{state.get('time_consumed', 0):.2f}",
            help="Accumulated delivery time"
        )
    
    with col2:
        st.metric(
            "💰 Cost ($1000s)",
            f"{state.get('cost_consumed', 0):.2f}",
            help="Accumulated transportation cost"
        )
    
    with col3:
        st.metric(
            "🌍 Carbon (tons CO2)",
            f"{state.get('carbon_emitted', 0):.2f}",
            help="Accumulated emissions"
        )
    
    with col4:
        st.metric(
            "📦 Weight (tons)",
            f"{state.get('cargo_weight', 0):.2f}",
            help="Total cargo weight"
        )
    
    # Full state display
    with st.expander("Full State JSON"):
        st.json(state)
else:
    st.info("👆 Reset environment to see state")


# Trajectory Interface
st.divider()
st.subheader("📈 Trajectory Builder")

col1, col2 = st.columns([3, 1])

with col1:
    st.write("Build a trajectory by defining actions:")
    
    trajectory_input = st.text_area(
        "Enter trajectory (JSON format)",
        value="[]",
        height=150,
        placeholder='[{"action": "truck_to_rail", "observation": {...}}, ...]'
    )
    
    try:
        trajectory = json.loads(trajectory_input)
    except json.JSONDecodeError:
        trajectory = []
        st.warning("Invalid JSON format")

with col2:
    st.write("")
    st.write("")
    if st.button("📊 Grade Trajectory", use_container_width=True):
        if trajectory:
            with st.spinner("Grading..."):
                result = grade_trajectory(st.session_state.current_task, trajectory)
                if result:
                    st.session_state.metrics_history.append({
                        "timestamp": datetime.now(),
                        "score": result.get("score", 0),
                        "hours": result.get("metrics", {}).get("accumulated_hours", 0),
                        "cost": result.get("metrics", {}).get("accumulated_cost", 0),
                        "carbon": result.get("metrics", {}).get("accumulated_carbon", 0),
                    })
                    st.rerun()
        else:
            st.warning("Trajectory is empty")


# Grading Results
if st.session_state.metrics_history:
    st.divider()
    st.subheader("✅ Grading Results")
    
    latest = st.session_state.metrics_history[-1]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🎯 Score",
            f"{latest['score']:.3f}",
            delta=None,
            help="Score in range [0, 1]"
        )
    
    with col2:
        st.metric("⏱️ Time", f"{latest['hours']:.2f}h")
    
    with col3:
        st.metric("💰 Cost", f"${latest['cost']:.2f}k")
    
    with col4:
        st.metric("🌍 Carbon", f"{latest['carbon']:.2f}t CO2")
    
    # History chart
    if len(st.session_state.metrics_history) > 1:
        df_history = pd.DataFrame(st.session_state.metrics_history)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            y=df_history["score"],
            mode="lines+markers",
            name="Score",
            line=dict(color="green", width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Score History",
            xaxis_title="Trajectory Index",
            yaxis_title="Score [0, 1]",
            hovermode="x unified",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)


# Information Section
st.divider()
st.subheader("ℹ️ About This Environment")

with st.expander("Scoring Formula"):
    st.markdown("""
    The scoring formula uses a weighted trilemma approach:
    
    **Score = 1 - (0.5 × normalized_time + 0.3 × normalized_cost + 0.2 × normalized_carbon)**
    
    - **50%**: Delivery time efficiency
    - **30%**: Economic cost
    - **20%**: Environmental impact
    
    Score is bounded to [0, 1] where 1 is best.
    """)

with st.expander("Task Descriptions"):
    st.markdown("""
    ### Task 1: Time Minimization ⏱️
    Minimize delivery time on a dense urban network. Find the fastest routes.
    
    ### Task 2: Cost Minimization 💰
    Minimize transportation cost on a regional network. Slower modes can be cheaper.
    
    ### Task 3: Multimodal Balancing 🎯
    Balance all three metrics using strategic cargo splitting and cargo type selection.
    Features:
    - `cargo_type`: Choose appropriate freight type
    - `split_at`: Decide where to split cargo between modes
    """)

with st.expander("API Endpoints"):
    st.markdown("""
    - **GET /health** - API health check
    - **POST /reset** - Reset environment
    - **GET /tasks** - Get task definitions
    - **POST /grader** - Grade a trajectory
    
    Base URL: `{}`
    """.format(st.session_state.api_url))


# Footer
st.divider()
st.markdown("""
---
**IntermodalFreightEnv** - A multimodal freight routing environment  
Built by Jay, Harsh, and Aryan
""")

st.markdown("""
<style>
footer {
    font-size: 0.8rem;
    color: #666;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)
