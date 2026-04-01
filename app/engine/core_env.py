"""
Core environment class for the freight simulation.

Manages the state, dynamics, and rules of the intermodal freight environment.
"""

from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
import numpy as np
import uuid

from app.utils.logger import logger


@dataclass
class EnvironmentConfig:
    """Configuration for the freight environment."""
    
    num_nodes: int = 10
    max_steps: int = 1000
    initial_demand: int = 100
    seed: Optional[int] = None


class FreightEnvironment:
    """
    Core freight environment simulation.
    
    Manages state transitions, reward calculation, and episode mechanics.
    """

    def __init__(self, config: Optional[EnvironmentConfig] = None):
        """
        Initialize the freight environment.
        
        Args:
            config: Environment configuration
        """
        self.config = config or EnvironmentConfig()
        self.current_step = 0
        self.state = {}
        self.network_config = {}
        self.nodes = {}
        self.edges = []
        self.episode_id = str(uuid.uuid4())
        
        if self.config.seed is not None:
            np.random.seed(self.config.seed)
        
        logger.info(f"FreightEnvironment initialized with config: {self.config}")

    def reset(self) -> Dict[str, Any]:
        """
        Reset the environment to initial state.
        
        Generates a new episode_id (UUID) to prevent state bleed.
        
        Returns:
            Initial environment state
        """
        self.current_step = 0
        self.episode_id = str(uuid.uuid4())  # Generate new UUID for each reset
        self.state = self._initialize_state()
        logger.info(f"Environment reset with episode_id={self.episode_id}")
        return self.state

    def setup_network(self, network_config: Dict[str, Any]) -> None:
        """
        Setup the network configuration.
        
        Args:
            network_config: Dictionary with nodes and edges
        """
        self.network_config = network_config
        self.nodes = {node["id"]: node for node in network_config.get("nodes", [])}
        self.edges = network_config.get("edges", [])
        logger.info(f"Network setup with {len(self.nodes)} nodes and {len(self.edges)} edges")

    def step(self, action: Dict[str, Any]) -> Tuple[Dict[str, Any], float, bool, Dict]:
        """
        Execute one step in the environment.
        
        Args:
            action: Action to execute
            
        Returns:
            Tuple of (state, reward, done, info)
        """
        self.current_step += 1
        
        # Update state based on action
        self.state = self._update_state(action)
        
        # Calculate reward
        reward = self._calculate_reward(action)
        
        # Check if episode is done
        done = self.current_step >= self.config.max_steps
        
        # Additional info
        info = {
            "step": self.current_step,
            "done": done,
        }
        
        return self.state, reward, done, info

    def _initialize_state(self) -> Dict[str, Any]:
        """
        Initialize the environment state.
        
        Returns:
            Initial state dictionary
        """
        return {
            "nodes": list(range(self.config.num_nodes)),
            "demand": np.random.randint(1, self.config.initial_demand, self.config.num_nodes).tolist(),
            "time": 0,
        }

    def _update_state(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Update state based on action."""
        # Placeholder: implement state update logic
        return self.state

    def _calculate_reward(self, action: Dict[str, Any]) -> float:
        """Calculate reward for the action."""
        # Placeholder: implement reward logic
        return 0.0

    def render(self) -> None:
        """Render the current environment state."""
        logger.info(f"Step {self.current_step}: {self.state}")
