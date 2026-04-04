"""
Script to run baseline agents and evaluate performance.

Supports multiple agent types (Random, Greedy, Dijkstra) with trajectory
collection and weighted scoring via the Grader.
"""

import argparse
import json
from typing import Dict, List, Any, Optional
import requests

from baseline.agent import RandomAgent, GreedyAgent, DijkstraAgent, BaseAgent
from app.api.grader import Grader
from app.api.schemas import TaskType
from app.utils.logger import logger


class BaselineRunner:
    """
    Orchestrates baseline agent evaluation with trajectory collection and grading.
    """

    def __init__(self, api_url: str = "http://localhost:8000"):
        """
        Initialize runner.
        
        Args:
            api_url: Base URL for the API
        """
        self.api_url = api_url
        self.grader = Grader()
        self.trajectories: Dict[str, List[Dict[str, Any]]] = {}
        logger.info(f"BaselineRunner initialized with API at {api_url}")

    def _verify_api_connection(self) -> bool:
        """
        Verify connection to the API.
        
        Returns:
            True if API is reachable
        """
        try:
            response = requests.get(f"{self.api_url}/health", timeout=2)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Cannot reach API at {self.api_url}: {e}")
            return False

    def run_episode(
        self,
        agent: BaseAgent,
        max_steps: int = 100,
        num_cargos: int = 3,
    ) -> tuple[List[Dict[str, Any]], float]:
        """
        Run a single episode with an agent.
        
        Args:
            agent: Agent instance
            max_steps: Maximum steps per episode
            num_cargos: Number of cargos to create
            
        Returns:
            Tuple of (trajectory, cumulative_reward)
        """
        try:
            # Reset environment
            response = requests.post(f"{self.api_url}/reset")
            response.raise_for_status()
            state = response.json()
            
            agent.reset()
            
            # Create cargos
            for i in range(num_cargos):
                cargo_data = {
                    "cargo_id": i,
                    "origin": "Warehouse",
                    "destination": "Destination",
                    "requires_refrigeration": False,
                }
                response = requests.post(f"{self.api_url}/cargo/add", json=cargo_data)
                if not response.ok:
                    logger.warning(f"Failed to add cargo {i}")
            
            # Run steps
            for step in range(max_steps):
                # Get current state
                response = requests.get(f"{self.api_url}/state")
                response.raise_for_status()
                state = response.json()
                
                # Agent selects action
                action = agent.select_action(state)
                
                # Execute action
                if action.get("task_type") == "task_1_time":
                    response = requests.post(
                        f"{self.api_url}/task1/route",
                        json=action
                    )
                elif action.get("task_type") == "task_2_cost":
                    response = requests.post(
                        f"{self.api_url}/task2/route",
                        json=action
                    )
                elif action.get("task_type") == "task_3_multimodal":
                    response = requests.post(
                        f"{self.api_url}/task3/route",
                        json=action
                    )
                else:
                    # Default to task 1
                    response = requests.post(
                        f"{self.api_url}/task1/route",
                        json=action
                    )
                
                if response.ok:
                    result = response.json()
                    reward = result.get("reward", 0.0)
                    done = result.get("done", False)
                    info = result.get("info", {})
                else:
                    reward = 0.0
                    done = False
                    info = {}
                
                # Record step
                agent.record_step(
                    step=step,
                    state=state,
                    action=action,
                    reward=reward,
                    done=done,
                    info=info,
                )
                
                if done:
                    logger.info(f"Episode ended at step {step}")
                    break
            
            trajectory = agent.get_trajectory()
            logger.info(
                f"Episode completed: {len(trajectory)} steps, "
                f"reward={agent.cumulative_reward:.2f}"
            )
            
            return trajectory, agent.cumulative_reward
            
        except Exception as e:
            logger.error(f"Error running episode: {e}")
            return [], 0.0

    def run_agent(
        self,
        agent: BaseAgent,
        agent_name: str,
        num_episodes: int = 3,
        max_steps: int = 50,
        num_cargos: int = 2,
    ) -> Dict[str, Any]:
        """
        Run multiple episodes with a single agent.
        
        Args:
            agent: Agent instance
            agent_name: Name for the agent
            num_episodes: Number of episodes to run
            max_steps: Maximum steps per episode
            num_cargos: Number of cargos per episode
            
        Returns:
            Summary statistics
        """
        logger.info(f"Running {num_episodes} episodes for {agent_name}")
        
        episode_trajectories = []
        episode_rewards = []
        
        for ep in range(num_episodes):
            logger.info(f"  Episode {ep + 1}/{num_episodes}")
            trajectory, reward = self.run_episode(
                agent,
                max_steps=max_steps,
                num_cargos=num_cargos
            )
            episode_trajectories.append(trajectory)
            episode_rewards.append(reward)
        
        # Combine trajectories
        combined_trajectory = []
        for traj in episode_trajectories:
            combined_trajectory.extend(traj)
        
        self.trajectories[agent_name] = combined_trajectory
        
        # Evaluate trajectory
        self.grader.load_trajectory(combined_trajectory)
        evaluation = self.grader.evaluate(task_type=TaskType.TASK_3_MULTIMODAL)
        
        summary = {
            "agent_name": agent_name,
            "num_episodes": num_episodes,
            "num_steps_total": len(combined_trajectory),
            "episode_rewards": episode_rewards,
            "avg_reward": sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0,
            "max_reward": max(episode_rewards) if episode_rewards else 0,
            "min_reward": min(episode_rewards) if episode_rewards else 0,
            "evaluation": evaluation.to_dict(),
        }
        
        logger.info(f"Completed {agent_name}: efficiency={evaluation.efficiency_score:.1f}")
        return summary

    def run_comparison(
        self,
        agent_configs: List[Dict[str, Any]],
        num_episodes: int = 3,
        max_steps: int = 50,
    ) -> Dict[str, Any]:
        """
        Run baseline comparison across multiple agents.
        
        Args:
            agent_configs: List of agent config dicts
                          {"type": "random|greedy|dijkstra", "name": "...", "kwargs": {...}}
            num_episodes: Number of episodes per agent
            max_steps: Maximum steps per episode
            
        Returns:
            Comparison results
        """
        logger.info(f"Starting baseline comparison with {len(agent_configs)} agents")
        
        results = {}
        
        for config in agent_configs:
            agent_type = config.get("type", "random")
            agent_name = config.get("name", f"{agent_type}_agent")
            agent_kwargs = config.get("kwargs", {})
            
            # Create agent
            if agent_type == "random":
                agent = RandomAgent(agent_id=agent_name, api_url=self.api_url)
            elif agent_type == "greedy":
                weight_type = agent_kwargs.get("weight_type", "cost")
                agent = GreedyAgent(
                    agent_id=agent_name,
                    api_url=self.api_url,
                    weight_type=weight_type
                )
            elif agent_type == "dijkstra":
                weight_type = agent_kwargs.get("weight_type", "cost")
                agent = DijkstraAgent(
                    agent_id=agent_name,
                    api_url=self.api_url,
                    weight_type=weight_type
                )
            else:
                logger.warning(f"Unknown agent type: {agent_type}")
                continue
            
            # Run agent
            summary = self.run_agent(
                agent,
                agent_name=agent_name,
                num_episodes=num_episodes,
                max_steps=max_steps,
            )
            
            results[agent_name] = summary
        
        # Generate comparison report
        comparison = self._generate_comparison_report(results)
        
        return comparison

    def _generate_comparison_report(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a comparison report across agents.
        
        Args:
            results: Results dict from run_comparison
            
        Returns:
            Comparison report
        """
        # Sort by efficiency score
        agent_scores = [
            (name, res["evaluation"]["efficiency_score"])
            for name, res in results.items()
        ]
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        report = {
            "num_agents": len(results),
            "agent_results": results,
            "rankings": [
                {
                    "rank": i + 1,
                    "agent": name,
                    "efficiency_score": score,
                    "avg_reward": results[name]["avg_reward"],
                }
                for i, (name, score) in enumerate(agent_scores)
            ],
            "best_agent": agent_scores[0][0] if agent_scores else None,
            "best_score": agent_scores[0][1] if agent_scores else 0,
        }
        
        return report

    def print_comparison_report(self, report: Dict[str, Any]) -> None:
        """
        Print a formatted comparison report.
        
        Args:
            report: Comparison report
        """
        print("\n" + "=" * 80)
        print("BASELINE COMPARISON REPORT")
        print("=" * 80)
        
        print(f"\nTotal Agents: {report['num_agents']}")
        print(f"Best Agent: {report['best_agent']} (Score: {report['best_score']:.1f})")
        
        print("\nRankings:")
        print("-" * 80)
        print(f"{'Rank':<6} {'Agent':<30} {'Efficiency':<15} {'Avg Reward':<15}")
        print("-" * 80)
        
        for ranking in report["rankings"]:
            print(
                f"{ranking['rank']:<6} "
                f"{ranking['agent']:<30} "
                f"{ranking['efficiency_score']:<15.1f} "
                f"{ranking['avg_reward']:<15.2f}"
            )
        
        print("\nDetailed Results:")
        print("-" * 80)
        
        for agent_name, result in report["agent_results"].items():
            print(f"\n{agent_name}:")
            print(f"  Episodes: {result['num_episodes']}")
            print(f"  Total Steps: {result['num_steps_total']}")
            print(f"  Avg Reward: {result['avg_reward']:.2f}")
            print(f"  Max Reward: {result['max_reward']:.2f}")
            
            eval_data = result["evaluation"]
            print(f"  Efficiency Score: {eval_data['efficiency_score']:.1f}")
            print(f"  Weighted Score: {eval_data['weighted_score']:.2f}")
            print(f"  Deliveries: {eval_data['cargos_delivered']}")
            print(f"  Metrics:")
            print(f"    - Time: {eval_data['raw_metrics']['accumulated_hours']:.2f}h")
            print(f"    - Cost: ${eval_data['raw_metrics']['accumulated_cost']:.2f}")
            print(f"    - Carbon: {eval_data['raw_metrics']['accumulated_carbon']:.2f}kg")
        
        print("\n" + "=" * 80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run baseline agents and compare performance"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL for API",
        dest="base_url",
    )
    parser.add_argument(
        "--agent_type",
        type=str,
        choices=["random", "greedy", "dijkstra", "all"],
        default="all",
        help="Agent type to run",
    )
    parser.add_argument(
        "--num_episodes",
        type=int,
        default=3,
        help="Number of episodes per agent",
    )
    parser.add_argument(
        "--max_steps",
        type=int,
        default=50,
        help="Maximum steps per episode",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file for results (JSON)",
    )
    
    args = parser.parse_args()
    
    runner = BaselineRunner(api_url=args.base_url)
    
    # Verify API connection
    if not runner._verify_api_connection():
        logger.error(f"Cannot connect to API at {args.base_url}")
        logger.info("Please ensure the API is running: python -m uvicorn app.main:app --reload")
        return
    
    # Define agent configurations
    if args.agent_type == "all":
        agent_configs = [
            {"type": "random", "name": "RandomAgent", "kwargs": {}},
            {"type": "greedy", "name": "GreedyCost", "kwargs": {"weight_type": "cost"}},
            {"type": "greedy", "name": "GreedyTime", "kwargs": {"weight_type": "time"}},
            {"type": "dijkstra", "name": "DijkstraCost", "kwargs": {"weight_type": "cost"}},
            {"type": "dijkstra", "name": "DijkstraTime", "kwargs": {"weight_type": "time"}},
        ]
    else:
        agent_configs = [
            {"type": args.agent_type, "name": f"{args.agent_type}_agent", "kwargs": {}}
        ]
    
    # Run comparison
    logger.info(f"Running baseline comparison with {len(agent_configs)} agents")
    report = runner.run_comparison(
        agent_configs,
        num_episodes=args.num_episodes,
        max_steps=args.max_steps,
    )
    
    # Print report
    runner.print_comparison_report(report)
    
    # Save results if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    
    # Exit successfully
    import sys
    sys.exit(0)


if __name__ == "__main__":
    main()
