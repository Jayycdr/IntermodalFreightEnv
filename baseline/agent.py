"""
Baseline agent implementation for the freight environment.

Provides a simple agent to establish baseline performance.
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from app.utils.logger import logger


class BaseAgent(ABC):
    """
    Abstract base class for agents in the freight environment.
    """

    def __init__(self, agent_id: str):
        """
        Initialize agent.
        
        Args:
            agent_id: Unique agent identifier
        """
        self.agent_id = agent_id
        self.episode_rewards = []
        logger.info(f"Agent {agent_id} initialized")

    @abstractmethod
    def select_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select action based on current state.
        
        Args:
            state: Current environment state
            
        Returns:
            Action dictionary
        """
        pass

    def record_reward(self, reward: float) -> None:
        """
        Record reward for current step.
        
        Args:
            reward: Reward value
        """
        self.episode_rewards.append(reward)

    def reset(self) -> None:
        """Reset agent for new episode."""
        self.episode_rewards = []


class RandomAgent(BaseAgent):
    """
    Baseline agent that takes random actions.
    """

    def __init__(self, agent_id: str = "random_agent"):
        """Initialize random agent."""
        super().__init__(agent_id)

    def select_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select random action.
        
        Args:
            state: Current environment state
            
        Returns:
            Random action dictionary
        """
        import random
        
        # Placeholder: implement random action selection
        action = {"type": "random", "value": random.random()}
        return action


class GreedyAgent(BaseAgent):
    """
    Baseline agent that uses greedy strategy.
    """

    def __init__(self, agent_id: str = "greedy_agent"):
        """Initialize greedy agent."""
        super().__init__(agent_id)

    def select_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select greedy action.
        
        Args:
            state: Current environment state
            
        Returns:
            Greedy action dictionary
        """
        # Placeholder: implement greedy action selection
        action = {"type": "greedy", "value": 0.5}
        return action
