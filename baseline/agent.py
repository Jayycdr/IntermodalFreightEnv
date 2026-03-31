"""
Baseline agents for the freight environment.

Agents query the API for state, identify disrupted_nodes, and pick available edges
using different strategies (random, greedy, dijkstra).
"""

import random
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import requests

from app.utils.logger import logger


class BaseAgent(ABC):
    """
    Abstract base agent for freight optimization.
    
    Agents interact with the API to observe state, identify disruptions,
    and select actions.
    """

    def __init__(self, agent_id: str, api_url: str = "http://localhost:8000"):
        """
        Initialize agent.
        
        Args:
            agent_id: Unique agent identifier
            api_url: Base URL for API endpoint
        """
        self.agent_id = agent_id
        self.api_url = api_url
        self.trajectory = []
        self.cumulative_reward = 0.0
        logger.info(f"Agent '{agent_id}' initialized with API at {api_url}")

    @abstractmethod
    def select_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select an action based on current state.
        
        Args:
            state: Current environment state
            
        Returns:
            Action dictionary (task-specific action)
        """
        pass

    def record_step(
        self,
        step: int,
        state: Dict[str, Any],
        action: Dict[str, Any],
        reward: float,
        done: bool,
        info: Dict[str, Any],
    ) -> None:
        """
        Record a step in the trajectory.
        
        Args:
            step: Step number
            state: Environment state
            action: Action taken
            reward: Reward received
            done: Whether episode ended
            info: Additional info
        """
        self.trajectory.append({
            "step": step,
            "state": state,
            "action": action,
            "reward": reward,
            "done": done,
            "info": info,
        })
        self.cumulative_reward += reward

    def get_trajectory(self) -> List[Dict[str, Any]]:
        """Get current trajectory."""
        return self.trajectory

    def reset(self) -> None:
        """Reset agent state."""
        self.trajectory.clear()
        self.cumulative_reward = 0.0

    def _get_state_from_api(self) -> Dict[str, Any]:
        """
        Fetch environment state from API.
        
        Returns:
            State dictionary with network, disabled nodes, etc.
        """
        try:
            response = requests.get(f"{self.api_url}/state")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch state from API: {e}")
            return {}

    def _get_available_edges(self, state: Dict[str, Any]) -> List[Tuple[str, str, Dict]]:
        """
        Extract available edges from state (not disabled).
        
        Args:
            state: Environment state
            
        Returns:
            List of (from_node, to_node, edge_data) tuples
        """
        disabled_edges = set(state.get("disabled_edges", []))
        disabled_nodes = set(state.get("disabled_nodes", []))
        
        available_edges = []
        
        # Iterate through network edges
        network = state.get("network", {})
        if "edges" in network:
            for edge in network["edges"]:
                from_node = edge.get("from")
                to_node = edge.get("to")
                
                # Check if edge or its endpoints are disabled
                if (from_node not in disabled_nodes and
                    to_node not in disabled_nodes and
                    (from_node, to_node) not in disabled_edges):
                    available_edges.append((from_node, to_node, edge))
        
        return available_edges

    def _get_edge_weight(
        self,
        edge: Dict[str, Any],
        weight_type: str = "time"
    ) -> float:
        """
        Get edge weight for a specific optimization objective.
        
        Args:
            edge: Edge dictionary
            weight_type: One of 'time', 'cost', 'carbon'
            
        Returns:
            Edge weight value
        """
        if weight_type == "time":
            return edge.get("time", 1.0)
        elif weight_type == "cost":
            return edge.get("cost", 1.0)
        elif weight_type == "carbon":
            return edge.get("carbon", 1.0)
        else:
            return edge.get("time", 1.0)


class RandomAgent(BaseAgent):
    """
    Agent that selects random available edges.
    
    Strategy: Among all available (non-disrupted) edges,
    randomly select one for cargo routing.
    """

    def select_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select a random available action.
        
        Args:
            state: Current environment state
            
        Returns:
            Task1Action with random available path
        """
        available_edges = self._get_available_edges(state)
        
        if not available_edges:
            logger.warning(f"No available edges for agent {self.agent_id}")
            return {"task_type": "task_1_time", "cargo_id": 0, "path": []}
        
        # Randomly select an edge
        from_node, to_node, edge = random.choice(available_edges)
        
        # Create a simple path
        path = [from_node, to_node]
        
        action = {
            "task_type": "task_1_time",
            "cargo_id": 0,  # Default cargo
            "path": path,
        }
        
        logger.debug(f"RandomAgent {self.agent_id} selected edge {from_node}->{to_node}")
        return action


class GreedyAgent(BaseAgent):
    """
    Agent that greedily selects the cheapest/fastest available edge.
    
    Strategy: Among all available edges, select the one with minimum
    cost/time based on the task objective.
    """

    def __init__(
        self,
        agent_id: str,
        api_url: str = "http://localhost:8000",
        weight_type: str = "cost"
    ):
        """
        Initialize greedy agent.
        
        Args:
            agent_id: Unique agent identifier
            api_url: Base URL for API
            weight_type: Optimization objective: 'time', 'cost', or 'carbon'
        """
        super().__init__(agent_id, api_url)
        self.weight_type = weight_type
        logger.info(f"GreedyAgent {agent_id} optimizing for: {weight_type}")

    def select_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select the edge with minimum cost/time/carbon.
        
        Args:
            state: Current environment state
            
        Returns:
            Task action with greedy optimal edge
        """
        available_edges = self._get_available_edges(state)
        
        if not available_edges:
            logger.warning(f"No available edges for agent {self.agent_id}")
            return {"task_type": "task_1_time", "cargo_id": 0, "path": []}
        
        # Find edge with minimum weight
        best_edge = min(
            available_edges,
            key=lambda x: self._get_edge_weight(x[2], self.weight_type)
        )
        
        from_node, to_node, edge = best_edge
        path = [from_node, to_node]
        
        # Map weight_type to task type
        task_map = {
            "time": "task_1_time",
            "cost": "task_2_cost",
            "carbon": "task_3_multimodal",
        }
        
        action = {
            "task_type": task_map.get(self.weight_type, "task_1_time"),
            "cargo_id": 0,
            "path": path,
        }
        
        weight_value = self._get_edge_weight(edge, self.weight_type)
        logger.debug(
            f"GreedyAgent {self.agent_id} selected {from_node}->{to_node} "
            f"({self.weight_type}={weight_value:.2f})"
        )
        return action


class DijkstraAgent(BaseAgent):
    """
    Agent that uses Dijkstra's algorithm to find optimal paths avoiding disruptions.
    
    Strategy: Build route using shortest path algorithm that avoids disabled nodes/edges
    and optimizes for the objective (time/cost/carbon).
    """

    def __init__(
        self,
        agent_id: str,
        api_url: str = "http://localhost:8000",
        weight_type: str = "cost",
    ):
        """
        Initialize Dijkstra agent.
        
        Args:
            agent_id: Unique agent identifier
            api_url: Base URL for API
            weight_type: Optimization objective
        """
        super().__init__(agent_id, api_url)
        self.weight_type = weight_type
        logger.info(f"DijkstraAgent {agent_id} optimizing for: {weight_type}")

    def select_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Dijkstra to find optimal path avoiding disruptions.
        
        Args:
            state: Current environment state
            
        Returns:
            Task action with Dijkstra-optimal path
        """
        # Build graph from available edges
        graph = self._build_available_graph(state)
        
        if not graph:
            logger.warning(f"Cannot build graph for agent {self.agent_id}")
            return {"task_type": "task_1_time", "cargo_id": 0, "path": []}
        
        # Try to find path from start to end
        nodes = list(graph.keys())
        if len(nodes) < 2:
            return {"task_type": "task_1_time", "cargo_id": 0, "path": nodes}
        
        start_node = nodes[0]
        end_node = nodes[-1]
        
        path = self._dijkstra(graph, start_node, end_node)
        
        if not path:
            # Fallback to random available edge
            available_edges = self._get_available_edges(state)
            if available_edges:
                from_node, to_node, _ = random.choice(available_edges)
                path = [from_node, to_node]
            else:
                path = []
        
        task_map = {
            "time": "task_1_time",
            "cost": "task_2_cost",
            "carbon": "task_3_multimodal",
        }
        
        action = {
            "task_type": task_map.get(self.weight_type, "task_1_time"),
            "cargo_id": 0,
            "path": path,
        }
        
        logger.debug(f"DijkstraAgent {self.agent_id} computed path: {' -> '.join(path)}")
        return action

    def _build_available_graph(self, state: Dict[str, Any]) -> Dict[str, List[Tuple[str, float]]]:
        """
        Build adjacency list graph from available edges.
        
        Args:
            state: Environment state
            
        Returns:
            Dict mapping node -> [(neighbor, weight)]
        """
        graph = {}
        available_edges = self._get_available_edges(state)
        
        for from_node, to_node, edge in available_edges:
            if from_node not in graph:
                graph[from_node] = []
            
            weight = self._get_edge_weight(edge, self.weight_type)
            graph[from_node].append((to_node, weight))
        
        return graph

    def _dijkstra(
        self,
        graph: Dict[str, List[Tuple[str, float]]],
        start: str,
        end: str
    ) -> List[str]:
        """
        Find shortest path from start to end using Dijkstra's algorithm.
        
        Args:
            graph: Adjacency list graph
            start: Start node
            end: End node
            
        Returns:
            Path as list of nodes
        """
        import heapq
        
        # Initialize distances and previous nodes
        distances = {node: float("inf") for node in graph}
        distances[start] = 0
        previous = {node: None for node in graph}
        
        pq = [(0, start)]  # (distance, node)
        visited = set()
        
        while pq:
            current_dist, current_node = heapq.heappop(pq)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            # Early exit if we reached destination
            if current_node == end:
                break
            
            # Explore neighbors
            if current_node in graph:
                for neighbor, weight in graph[current_node]:
                    if neighbor not in visited:
                        new_dist = current_dist + weight
                        
                        if new_dist < distances[neighbor]:
                            distances[neighbor] = new_dist
                            previous[neighbor] = current_node
                            heapq.heappush(pq, (new_dist, neighbor))
        
        # Reconstruct path
        if distances[end] == float("inf"):
            return []  # No path found
        
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]
        
        path.reverse()
        return path
