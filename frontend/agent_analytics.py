#!/usr/bin/env python3
"""
Agent Learning Visualization Dashboard

Visualize how different agents learn across the three tasks.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="Agent Learning Analytics",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Agent Learning Analytics")
st.markdown("**Monitor and analyze agent learning across tasks**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    api_url = st.text_input("API URL", value="http://localhost:8000")
    
    st.divider()
    st.subheader("Simulation Parameters")
    num_episodes = st.slider("Episodes per task", 5, 50, 20)
    num_trajectories = st.slider("Trajectories per episode", 1, 10, 3)

# Try to connect to API
try:
    response = requests.get(f"{api_url}/health", timeout=2)
    api_connected = response.status_code == 200
except:
    api_connected = False

if not api_connected:
    st.error("❌ Cannot connect to API. Make sure the backend is running on {}".format(api_url))
    st.stop()

st.success("✅ API Connected")

# Get task definitions
@st.cache_data
def get_tasks():
    response = requests.get(f"{api_url}/tasks", timeout=5)
    return response.json()

tasks_data = get_tasks()
tasks = tasks_data.get("tasks", [])

# Simulation
if st.button("🚀 Start Learning Simulation", use_container_width=True):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    learning_curves = {
        1: {"scores": [], "times": [], "costs": [], "carbons": []},
        2: {"scores": [], "times": [], "costs": [], "carbons": []},
        3: {"scores": [], "times": [], "costs": [], "carbons": []},
    }
    
    total_steps = len(tasks) * num_episodes * num_trajectories
    current_step = 0
    
    for task_id in [1, 2, 3]:
        for episode in range(num_episodes):
            # Reset environment
            reset_response = requests.post(
                f"{api_url}/reset",
                json={"task_id": task_id, "seed": episode},
                timeout=5
            )
            
            for traj in range(num_trajectories):
                # Simulate grading (random trajectory)
                fake_trajectory = [{"action": f"action_{i}", "observation": {}} for i in range(np.random.randint(2, 6))]
                
                grade_response = requests.post(
                    f"{api_url}/grader",
                    json={"task_id": task_id, "trajectory": fake_trajectory},
                    timeout=5
                )
                
                if grade_response.status_code == 200:
                    metrics = grade_response.json().get("metrics", {})
                    score = grade_response.json().get("score", 0)
                    
                    learning_curves[task_id]["scores"].append(score)
                    learning_curves[task_id]["times"].append(metrics.get("accumulated_hours", 0))
                    learning_curves[task_id]["costs"].append(metrics.get("accumulated_cost", 0))
                    learning_curves[task_id]["carbons"].append(metrics.get("accumulated_carbon", 0))
                
                current_step += 1
                progress = current_step / total_steps
                progress_bar.progress(progress)
                status_text.text(f"Task {task_id} | Episode {episode+1}/{num_episodes} | Trajectory {traj+1}/{num_trajectories}")
    
    progress_bar.empty()
    status_text.empty()
    st.success("✅ Simulation completed!")
    
    # Display results
    st.divider()
    st.subheader("📊 Learning Curves")
    
    cols = st.columns(3)
    for i, task_id in enumerate([1, 2, 3]):
        with cols[i]:
            st.metric(
                f"Task {task_id} Avg Score",
                f"{np.mean(learning_curves[task_id]['scores']):.3f}",
                delta=f"{learning_curves[task_id]['scores'][-1] - learning_curves[task_id]['scores'][0]:.3f}"
            )
    
    # Score progression
    fig = go.Figure()
    
    colors = ["#00cc00", "#0099ff", "#ff6600"]
    for i, task_id in enumerate([1, 2, 3]):
        fig.add_trace(go.Scatter(
            y=learning_curves[task_id]["scores"],
            mode="lines+markers",
            name=f"Task {task_id}",
            line=dict(color=colors[i], width=2),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        title="Agent Score Progression Across Tasks",
        xaxis_title="Trajectory Index",
        yaxis_title="Score [0, 1]",
        hovermode="x unified",
        height=400,
        template="plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Metrics comparison
    st.subheader("📈 Metrics Comparison")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig_time = go.Figure()
        for i, task_id in enumerate([1, 2, 3]):
            fig_time.add_trace(go.Scatter(
                y=learning_curves[task_id]["times"],
                mode="lines",
                name=f"Task {task_id}",
                line=dict(color=colors[i])
            ))
        
        fig_time.update_layout(
            title="Time Consumption",
            xaxis_title="Trajectory",
            yaxis_title="Hours",
            height=300,
            template="plotly_white"
        )
        st.plotly_chart(fig_time, use_container_width=True)
    
    with col2:
        fig_cost = go.Figure()
        for i, task_id in enumerate([1, 2, 3]):
            fig_cost.add_trace(go.Scatter(
                y=learning_curves[task_id]["costs"],
                mode="lines",
                name=f"Task {task_id}",
                line=dict(color=colors[i])
            ))
        
        fig_cost.update_layout(
            title="Cost Consumption",
            xaxis_title="Trajectory",
            yaxis_title="Cost ($1000s)",
            height=300,
            template="plotly_white"
        )
        st.plotly_chart(fig_cost, use_container_width=True)
    
    with col3:
        fig_carbon = go.Figure()
        for i, task_id in enumerate([1, 2, 3]):
            fig_carbon.add_trace(go.Scatter(
                y=learning_curves[task_id]["carbons"],
                mode="lines",
                name=f"Task {task_id}",
                line=dict(color=colors[i])
            ))
        
        fig_carbon.update_layout(
            title="Carbon Emissions",
            xaxis_title="Trajectory",
            yaxis_title="tons CO2",
            height=300,
            template="plotly_white"
        )
        st.plotly_chart(fig_carbon, use_container_width=True)
    
    # Summary statistics
    st.subheader("📊 Summary Statistics")
    
    summary_data = {
        "Task": [1, 2, 3],
        "Avg Score": [np.mean(learning_curves[i]["scores"]) for i in [1, 2, 3]],
        "Max Score": [np.max(learning_curves[i]["scores"]) for i in [1, 2, 3]],
        "Min Score": [np.min(learning_curves[i]["scores"]) for i in [1, 2, 3]],
        "Avg Time": [np.mean(learning_curves[i]["times"]) for i in [1, 2, 3]],
        "Avg Cost": [np.mean(learning_curves[i]["costs"]) for i in [1, 2, 3]],
        "Avg Carbon": [np.mean(learning_curves[i]["carbons"]) for i in [1, 2, 3]],
    }
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

else:
    st.info("👆 Click the button to start a learning simulation")
