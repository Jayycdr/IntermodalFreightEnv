"""
Script to run baseline agent in the freight environment.

Trains and evaluates a baseline agent for performance benchmarking.
"""

from typing import Optional
import argparse

from app.engine.core_env import FreightEnvironment, EnvironmentConfig
from app.api.grader import Grader
from baseline.agent import RandomAgent, GreedyAgent
from app.utils.logger import logger


def run_episode(agent, env, grader, max_steps: int = 100):
    """
    Run a single episode.
    
    Args:
        agent: Agent instance
        env: Environment instance
        grader: Grader instance
        max_steps: Maximum steps per episode
        
    Returns:
        Episode return
    """
    state = env.reset()
    agent.reset()
    total_reward = 0
    
    for step in range(max_steps):
        action = agent.select_action(state)
        state, reward, done, info = env.step(action)
        agent.record_reward(reward)
        total_reward += reward
        
        if done:
            break
    
    logger.info(f"Episode completed: total_reward={total_reward}")
    return total_reward


def run_baseline(
    agent_type: str = "random",
    num_episodes: int = 10,
    max_steps: int = 100,
    num_nodes: int = 10,
):
    """
    Run baseline agent training and evaluation.
    
    Args:
        agent_type: Type of agent ("random" or "greedy")
        num_episodes: Number of episodes to run
        max_steps: Maximum steps per episode
        num_nodes: Number of nodes in the environment
    """
    # Initialize environment
    config = EnvironmentConfig(num_nodes=num_nodes, max_steps=max_steps)
    env = FreightEnvironment(config)
    
    # Initialize agent
    if agent_type == "random":
        agent = RandomAgent()
    elif agent_type == "greedy":
        agent = GreedyAgent()
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    # Initialize grader
    grader = Grader()
    
    logger.info(f"Running {num_episodes} episodes of {agent_type} agent")
    
    episode_returns = []
    
    for episode in range(num_episodes):
        logger.info(f"Episode {episode + 1}/{num_episodes}")
        total_reward = run_episode(agent, env, grader, max_steps)
        episode_returns.append(total_reward)
    
    # Print summary
    avg_return = sum(episode_returns) / len(episode_returns)
    logger.info(f"Average episode return: {avg_return:.4f}")
    logger.info(f"Max episode return: {max(episode_returns):.4f}")
    logger.info(f"Min episode return: {min(episode_returns):.4f}")
    
    return episode_returns


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run baseline agent")
    parser.add_argument(
        "--agent_type",
        type=str,
        default="random",
        choices=["random", "greedy"],
        help="Type of baseline agent",
    )
    parser.add_argument(
        "--num_episodes",
        type=int,
        default=10,
        help="Number of episodes to run",
    )
    parser.add_argument(
        "--max_steps",
        type=int,
        default=100,
        help="Maximum steps per episode",
    )
    parser.add_argument(
        "--num_nodes",
        type=int,
        default=10,
        help="Number of nodes in environment",
    )
    
    args = parser.parse_args()
    
    logger.info("Starting baseline run")
    results = run_baseline(
        agent_type=args.agent_type,
        num_episodes=args.num_episodes,
        max_steps=args.max_steps,
        num_nodes=args.num_nodes,
    )
    logger.info("Baseline run completed")


if __name__ == "__main__":
    main()
