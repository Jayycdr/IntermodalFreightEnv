"""
LLM-based Inference Agent for IntermodalFreightEnv Hackathon.

This script demonstrates how to build an agent that:
1. Reads and processes environment variables properly
2. Uses OpenAI client for LLM-based decision making
3. Follows strict START/STEP/END logging format
4. Interacts with the IntermodalFreightEnv API

Pre-Submission Checklist:
✓ Environment variables: API_BASE_URL, MODEL_NAME, HF_TOKEN, LOCAL_IMAGE_NAME
✓ Defaults only for API_BASE_URL and MODEL_NAME
✓ All LLM calls use OpenAI client
✓ Stdout logs follow START/STEP/END structured format
"""

import os
import sys
import json
import requests
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# 1. ENVIRONMENT VARIABLES - Following Exact Submission Requirements
# ============================================================================

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4")
HF_TOKEN = os.getenv("HF_TOKEN")

# Optional — if you use from_docker_image():
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

# Initialize OpenAI client (uses api_key from OPENAI_API_KEY env var)
try:
    openai_client = OpenAI()
except Exception as e:
    print(f"Warning: OpenAI initialization failed: {e}")
    print("Ensure OPENAI_API_KEY environment variable is set")
    openai_client = None


# ============================================================================
# 2. STRUCTURED LOGGING - START/STEP/END Format
# ============================================================================

def log_structured(event_type: str, **kwargs) -> None:
    """
    Log events in structured START/STEP/END format.
    
    Args:
        event_type: One of "START", "STEP", or "END"
        **kwargs: Additional fields to include in the log
    """
    log_entry = {
        "event": event_type,
        **kwargs
    }
    print(json.dumps(log_entry))
    sys.stdout.flush()


# ============================================================================
# 3. API INTERACTION LAYER
# ============================================================================

def api_reset() -> Dict[str, Any]:
    """Reset the environment and return initial state."""
    response = requests.post(f"{API_BASE_URL}/reset", json={})
    response.raise_for_status()
    return response.json()


def api_get_tasks() -> Dict[str, Any]:
    """Fetch available tasks."""
    response = requests.get(f"{API_BASE_URL}/tasks")
    response.raise_for_status()
    return response.json()


def api_step(action: Dict[str, Any]) -> Dict[str, Any]:
    """Submit action and get next state."""
    response = requests.post(
        f"{API_BASE_URL}/step",
        json={"action": action},
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    return response.json()


def api_grader(trajectory: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Submit trajectory to grader."""
    response = requests.post(
        f"{API_BASE_URL}/grader",
        json={"trajectory": trajectory},
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    return response.json()


# ============================================================================
# 4. LLM AGENT - Using OpenAI Client
# ============================================================================

class InferenceAgent:
    """
    LLM-based agent for freight routing optimization.
    Uses OpenAI client for decision making and follows structured logging.
    """
    
    def __init__(
        self,
        api_base_url: str = API_BASE_URL,
        model_name: str = MODEL_NAME,
        hf_token: Optional[str] = HF_TOKEN,
        local_image_name: Optional[str] = LOCAL_IMAGE_NAME
    ):
        """Initialize agent with environment configuration."""
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.hf_token = hf_token
        self.local_image_name = local_image_name
        self.openai_client = openai_client
        self.trajectory = []
        
        log_structured(
            "START",
            phase="agent_initialization",
            api_base_url=self.api_base_url,
            model_name=self.model_name,
            hf_token_provided=(self.hf_token is not None),
            local_image_name=self.local_image_name
        )
    
    def _llm_decide_action(
        self,
        state: Dict[str, Any],
        task_type: str
    ) -> Dict[str, Any]:
        """
        Use OpenAI client to decide the next action.
        This is the core LLM inference call.
        """
        prompt = f"""Given this state and task, decide the routing action:

State: {json.dumps(state)}
Task: {task_type}

You must respond with a JSON object containing:
- task_type: "{task_type}"
- cargo_id: <int>
- path: [<list of node ids>]

For task_3_multimodal, also include:
- cargo_type: <string>
- split_at: <int>

Return ONLY the JSON object, no other text."""

        # Using OpenAI client for LLM inference
        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert freight routing optimizer. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            action = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback to basic action if parsing fails
            if task_type == "task_3_multimodal":
                action = {
                    "task_type": task_type,
                    "cargo_id": 0,
                    "cargo_type": "truck",
                    "path": [0, 1, 5],
                    "split_at": []
                }
            else:
                action = {
                    "task_type": task_type,
                    "cargo_id": 0,
                    "path": [0, 1, 5]
                }
        
        return action
    
    def run_episode(
        self,
        task_type: str = "task_1_time",
        max_steps: int = 5
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Run a single episode for the task."""
        log_structured("START", phase="episode", task_type=task_type)
        
        # Reset environment
        reset_response = api_reset()
        state = reset_response.get("data", {}).get("state", {})
        
        trajectory = []
        cumulative_reward = 0.0
        
        for step_idx in range(max_steps):
            # Use LLM to decide action (OpenAI client call)
            action = self._llm_decide_action(state, task_type)
            
            # Execute action
            step_response = api_step(action)
            step_data = step_response.get("data", {})
            
            reward = step_data.get("reward", 0.0)
            done = step_data.get("done", False)
            next_state = step_data.get("state", {})
            info = step_data.get("info", {})
            
            # Log step
            log_structured(
                "STEP",
                step=step_idx,
                task_type=task_type,
                action=action,
                reward=reward,
                done=done
            )
            
            # Record trajectory
            trajectory.append({
                "step": step_idx,
                "state": state,
                "action": action,
                "reward": reward,
                "done": done,
                "info": info
            })
            
            cumulative_reward += reward
            state = next_state
            
            if done:
                break
        
        log_structured(
            "END",
            phase="episode",
            task_type=task_type,
            steps=len(trajectory),
            cumulative_reward=cumulative_reward
        )
        
        return cumulative_reward, trajectory
    
    def solve_all_tasks(self) -> Dict[str, Any]:
        """Solve all three tasks and return results."""
        log_structured("START", phase="solve_all_tasks")
        
        results = {}
        all_trajectories = []
        
        for task_type in ["task_1_time", "task_2_cost", "task_3_multimodal"]:
            log_structured("START", phase=f"task_{task_type}")
            
            cumulative_reward, trajectory = self.run_episode(task_type=task_type)
            all_trajectories.extend(trajectory)
            
            # Grade this task
            grade_response = api_grader(trajectory)
            score = grade_response.get("data", {}).get("score", 0.0)
            
            results[task_type] = {
                "cumulative_reward": cumulative_reward,
                "score": score,
                "trajectory_length": len(trajectory)
            }
            
            log_structured(
                "END",
                phase=f"task_{task_type}",
                score=score,
                reward=cumulative_reward
            )
        
        # Final grade on all trajectories
        final_grade = api_grader(all_trajectories)
        final_score = final_grade.get("data", {}).get("score", 0.0)
        
        log_structured(
            "END",
            phase="solve_all_tasks",
            final_score=final_score,
            results=results
        )
        
        return {
            "results": results,
            "final_score": final_score,
            "total_trajectory_length": len(all_trajectories)
        }


# ============================================================================
# 5. MAIN EXECUTION
# ============================================================================

def main():
    """Main entry point for inference."""
    log_structured(
        "START",
        phase="inference_main",
        api_base_url=API_BASE_URL,
        model_name=MODEL_NAME,
        hf_token_configured=(HF_TOKEN is not None)
    )
    
    try:
        # Create agent
        agent = InferenceAgent(
            api_base_url=API_BASE_URL,
            model_name=MODEL_NAME,
            hf_token=HF_TOKEN,
            local_image_name=LOCAL_IMAGE_NAME
        )
        
        # Solve all tasks
        solution = agent.solve_all_tasks()
        
        log_structured(
            "END",
            phase="inference_main",
            success=True,
            final_score=solution["final_score"]
        )
        
        return 0
    
    except Exception as e:
        log_structured(
            "END",
            phase="inference_main",
            success=False,
            error=str(e)
        )
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
