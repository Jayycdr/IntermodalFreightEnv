"""
Core environment class for the freight simulation.

Manages the state, dynamics, and rules of the intermodal freight environment.
"""

from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass, field
import numpy as np
from datetime import datetime

from app.utils.logger import logger


@dataclass
class Cargo:
    """Represents a cargo shipment."""
    cargo_id: int
    origin: int
    destination: int
    quantity: float = 100.0
    weight: float = 50.0
    priority: str = "normal"
    deadline: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    path_taken: List[int] = field(default_factory=list)
    time_hours: float = 0.0
    cost: float = 0.0
    carbon: float = 0.0
    completed: bool = False


@dataclass
class TrilemmaMetrics:
    """Tracks optimization metrics."""
    accumulated_hours: float = 0.0
    accumulated_cost: float = 0.0
    accumulated_carbon: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dict for API responses."""
        return {
            "accumulated_hours": self.accumulated_hours,
            "accumulated_cost": self.accumulated_cost,
            "accumulated_carbon": self.accumulated_carbon,
        }
    
    def reset(self):
        """Reset all metrics to 0."""
        self.accumulated_hours = 0.0
        self.accumulated_cost = 0.0
        self.accumulated_carbon = 0.0


@dataclass
class EnvironmentConfig:
    """Configuration for the freight environment."""
    
    num_nodes: int = 6  # Match actual network size
    max_steps: int = 1000
    initial_demand: int = 100
    seed: Optional[int] = None
    disruption_probability: float = 0.1


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
        self.node_ids = set()  # Set for O(1) node lookups
        self.edges = {}  # Dict keyed by (source, target) tuple for O(1) lookup
        self.edges_list = []  # Keep list for iteration when needed for API responses
        
        # Cargo management (critical for learning)
        self.active_cargos: List[Cargo] = []
        self.completed_cargos: List[Cargo] = []
        self.cargo_counter = 0
        
        # Metrics tracking (essential for reward)
        self.trilemma = TrilemmaMetrics()
        
        # Disruption tracking
        self.disabled_nodes: set = set()
        self.disabled_edges: set = set()
        
        if self.config.seed is not None:
            np.random.seed(self.config.seed)
        
        logger.info(f"FreightEnvironment initialized with config: {self.config}")

    def reset(self) -> Dict[str, Any]:
        """
        Reset the environment to initial state.
        
        Returns:
            Initial environment state
        """
        self.current_step = 0
        self.active_cargos.clear()
        self.completed_cargos.clear()
        self.cargo_counter = 0
        self.trilemma.reset()
        self.disabled_nodes.clear()
        self.disabled_edges.clear()
        
        # Initialize with some random cargos
        self._generate_initial_cargos()
        
        # Initialize state with proper structure
        self.state = self._initialize_state()
        logger.info("Environment reset")
        return self.state

    def setup_network(self, network_config: Dict[str, Any]) -> None:
        """
        Setup the network configuration.
        
        Args:
            network_config: Dictionary with nodes and edges
        """
        self.network_config = network_config
        
        # Setup nodes: dict for data access, set for O(1) lookup
        self.nodes = {node["id"]: node for node in network_config.get("nodes", [])}
        self.node_ids = set(self.nodes.keys())  # For O(1) node existence checks
        
        # Setup edges: dict keyed by (source, target) for O(1) lookup
        edges_list = network_config.get("edges", [])
        self.edges_list = edges_list  # Keep for API responses
        self.edges = {
            (edge["source"], edge["target"]): edge 
            for edge in edges_list
        }
        
        # Update config num_nodes to match actual network
        self.config.num_nodes = len(self.nodes)
        
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
        
        # Process action (this updates state and metrics)
        self._process_action(action)
        
        # Update state with current metrics
        self.state = self._build_state()
        
        # Calculate reward based on updated metrics
        reward = self._calculate_reward(action)
        
        # Check if episode is done
        done = self._check_done()
        
        # Additional info
        info = {
            "step": self.current_step,
            "done": done,
            "cargos_active": len(self.active_cargos),
            "cargos_completed": len(self.completed_cargos),
            "reward": reward,
        }
        
        return self.state, reward, done, info

    # ============================================================================
    # Cargo Management Methods
    # ============================================================================

    def add_cargo(self, origin: int, destination: int, quantity: float = 100.0,
                  weight: float = 50.0, priority: str = "normal",
                  deadline: Optional[int] = None) -> Cargo:
        """
        Add a new cargo shipment.
        
        Args:
            origin: Source node
            destination: Destination node
            quantity: Cargo quantity
            weight: Cargo weight
            priority: Priority level
            deadline: Delivery deadline (steps)
            
        Returns:
            Created Cargo object
        """
        cargo = Cargo(
            cargo_id=self.cargo_counter,
            origin=origin,
            destination=destination,
            quantity=quantity,
            weight=weight,
            priority=priority,
            deadline=deadline
        )
        self.cargo_counter += 1
        self.active_cargos.append(cargo)
        logger.debug(f"Cargo {cargo.cargo_id} added: {origin} → {destination}")
        return cargo

    def complete_cargo(self, cargo_id: int, path: List[int], 
                      time_hours: float, cost: float, carbon: float):
        """
        Mark cargo as completed and accumulate metrics.
        
        Args:
            cargo_id: ID of cargo to complete
            path: Path taken
            time_hours: Time taken
            cost: Cost incurred
            carbon: Carbon emitted
        """
        # Find and remove from active
        cargo = None
        for c in self.active_cargos:
            if c.cargo_id == cargo_id:
                cargo = c
                self.active_cargos.remove(c)
                break
        
        if cargo:
            # Mark as completed
            cargo.completed = True
            cargo.completed_at = datetime.now()
            cargo.path_taken = path
            cargo.time_hours = time_hours
            cargo.cost = cost
            cargo.carbon = carbon
            
            # Move to completed
            self.completed_cargos.append(cargo)
            
            # Accumulate metrics
            self.trilemma.accumulated_hours += time_hours
            self.trilemma.accumulated_cost += cost
            self.trilemma.accumulated_carbon += carbon
            
            logger.debug(f"Cargo {cargo_id} completed: "
                        f"time={time_hours:.2f}h, cost=${cost:.2f}, carbon={carbon:.2f}t")

    def get_cargo(self, cargo_id: int) -> Optional[Cargo]:
        """Get cargo by ID."""
        for cargo in self.active_cargos + self.completed_cargos:
            if cargo.cargo_id == cargo_id:
                return cargo
        return None

    def _generate_initial_cargos(self):
        """Generate random initial cargos."""
        num_cargos = np.random.randint(1, 5)  # 1-4 cargos per episode
        for _ in range(num_cargos):
            origin = np.random.randint(0, self.config.num_nodes)
            destination = np.random.randint(0, self.config.num_nodes)
            if origin != destination:
                self.add_cargo(
                    origin=origin,
                    destination=destination,
                    quantity=np.random.randint(50, 200),
                    weight=np.random.randint(30, 100)
                )

    # ============================================================================
    # State Management Methods
    # ============================================================================

    def _initialize_state(self) -> Dict[str, Any]:
        """
        Initialize the environment state with proper structure.
        
        Returns:
            Initial state dictionary
        """
        return self._build_state()

    def _build_state(self) -> Dict[str, Any]:
        """
        Build current state snapshot.
        
        Returns:
            Current state dict
        """
        return {
            "step": self.current_step,
            "active_cargos": len(self.active_cargos),
            "completed_cargos": len(self.completed_cargos),
            "trilemma": self.trilemma.to_dict(),
            "network": {
                "nodes": self._get_network_nodes(),
                "edges": self._get_network_edges(),
            }
        }

    def _get_network_nodes(self) -> List[Dict]:
        """Get network nodes for state."""
        nodes = []
        for node_id, node_data in self.nodes.items():
            nodes.append({
                "id": node_id,
                "location": node_data.get("location", f"Node{node_id}"),
                "capacity": node_data.get("capacity", 1000.0),
                "disabled": node_id in self.disabled_nodes,
            })
        return nodes

    def _get_network_edges(self) -> List[Dict]:
        """Get network edges for state."""
        edges = []
        for edge in self.edges_list:
            source = edge.get("source")
            target = edge.get("target")
            edge_key = (source, target)
            
            edges.append({
                "source": source,
                "target": target,
                "time": edge.get("time", 1.0),
                "cost": edge.get("cost", 100.0),
                "carbon": edge.get("carbon", 50.0),
                "disabled": edge_key in self.disabled_edges,
            })
        return edges

    def _process_action(self, action: Dict[str, Any]):
        """
        Process agent action.
        
        This is where task-specific logic happens:
        - Validate action
        - Calculate metrics for path
        - Update cargo status
        - Simulate delivery
        """
        if not action or not isinstance(action, dict):
            return
        
        task_type = action.get("task_type", "task_1_time")
        cargo_id = action.get("cargo_id", 0)
        path = action.get("path", [])
        
        # Validate cargo exists
        cargo = self.get_cargo(cargo_id)
        if not cargo:
            return  # Invalid cargo
        
        # Validate path
        if not self._validate_path(path):
            return  # Invalid path
        
        # Calculate metrics based on task and path
        time_hours, cost, carbon = self._calculate_path_metrics(path, task_type)
        
        # Complete the cargo with these metrics
        self.complete_cargo(cargo_id, path, time_hours, cost, carbon)

    def _validate_path(self, path: List[int]) -> bool:
        """
        Validate that path is valid (all nodes and edges exist).
        Fast O(n) implementation using dict lookups.
        
        Args:
            path: List of node IDs
            
        Returns:
            True if valid, False otherwise
        """
        if not path or len(path) < 2:
            return False
        
        # Check all nodes exist (O(n) where n is path length)
        for node_id in path:
            if node_id not in self.node_ids:  # O(1) set lookup
                return False
        
        # Check all edges exist (O(n) where n is path length)
        for i in range(len(path) - 1):
            source, target = path[i], path[i + 1]
            edge_key = (source, target)
            
            # O(1) dict lookup instead of O(m) list iteration
            if edge_key not in self.edges:
                return False
            
            # Check if not disabled
            if edge_key in self.disabled_edges:
                return False
        
        return True

    def _calculate_path_metrics(self, path: List[int], task_type: str) -> Tuple[float, float, float]:
        """
        Calculate time, cost, and carbon for a path.
        Fast O(n) implementation using dict lookups.
        
        Args:
            path: List of node IDs
            task_type: Type of task (affects optimization)
            
        Returns:
            Tuple of (time_hours, cost, carbon)
        """
        total_time = 0.0
        total_cost = 0.0
        total_carbon = 0.0
        
        # Sum metrics for all edges in path (O(n) with O(1) lookups)
        for i in range(len(path) - 1):
            source, target = path[i], path[i + 1]
            edge_key = (source, target)
            
            # O(1) dict lookup instead of O(m) list iteration
            if edge_key in self.edges:
                edge = self.edges[edge_key]
                total_time += edge.get("time", 1.0)
                total_cost += edge.get("cost", 100.0)
                total_carbon += edge.get("carbon", 50.0)
        
        return total_time, total_cost, total_carbon

    def _check_done(self) -> bool:
        """
        Check if episode is done.
        
        Returns:
            True if episode should end
        """
        # Done if max steps reached
        if self.current_step >= self.config.max_steps:
            return True
        
        # Done if all cargos delivered
        if len(self.active_cargos) == 0 and len(self.completed_cargos) > 0:
            return True
        
        return False

    # ============================================================================
    # Reward Calculation
    # ============================================================================

    def _calculate_reward(self, action: Dict[str, Any]) -> float:
        """
        Calculate reward using trilemma metrics.
        
        Formula: reward = -(0.5×time + 0.3×cost + 0.2×carbon)
        
        This negative reward encourages agents to minimize metrics.
        
        Returns:
            float: Reward signal for learning
        """
        from app.constants import (
            TRILEMMA_WEIGHT_TIME,
            TRILEMMA_WEIGHT_COST,
            TRILEMMA_WEIGHT_CARBON,
        )
        
        # Get accumulated metrics
        time_hours = self.trilemma.accumulated_hours
        cost_dollars = self.trilemma.accumulated_cost
        carbon_tons = self.trilemma.accumulated_carbon
        
        # Calculate weighted cost
        weighted_cost = (
            TRILEMMA_WEIGHT_TIME * time_hours +
            TRILEMMA_WEIGHT_COST * cost_dollars +
            TRILEMMA_WEIGHT_CARBON * carbon_tons
        )
        
        # Return negative cost as reward (minimize cost = maximize reward)
        reward = -weighted_cost
        
        logger.debug(
            f"Step {self.current_step}: "
            f"time={time_hours:.2f}h, cost=${cost_dollars:.2f}, "
            f"carbon={carbon_tons:.2f}t → reward={reward:.4f}"
        )
        
        return reward

    # ============================================================================
    # Metrics and Access Methods
    # ============================================================================

    def get_state(self) -> Dict[str, Any]:
        """Get current state."""
        return self.state

    def get_trilemma(self) -> TrilemmaMetrics:
        """Get trilemma metrics object."""
        return self.trilemma

    def render(self) -> None:
        """Render the current environment state."""
        logger.info(
            f"Step {self.current_step}: "
            f"Active={len(self.active_cargos)}, "
            f"Completed={len(self.completed_cargos)}, "
            f"Time={self.trilemma.accumulated_hours:.2f}h, "
            f"Cost=${self.trilemma.accumulated_cost:.2f}, "
            f"Carbon={self.trilemma.accumulated_carbon:.2f}t"
        )

    # ============================================================================
    # Backward Compatibility with Existing API
    # ============================================================================

    @property
    def cargos(self) -> Dict[int, Cargo]:
        """
        Backward compatibility: Get all cargos as a dictionary by ID.
        Includes both active and completed cargos.
        
        Returns:
            Dict mapping cargo_id to Cargo object
        """
        result = {}
        for cargo in self.active_cargos + self.completed_cargos:
            result[cargo.cargo_id] = cargo
        return result

    def route_cargo(self, cargo_id: int, path: List[int]) -> bool:
        """
        Route a cargo along a specific path (backward compatibility).
        
        Args:
            cargo_id: ID of cargo to route
            path: List of node IDs representing the path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate cargo exists
            cargo = self.get_cargo(cargo_id)
            if not cargo:
                logger.error(f"Cargo {cargo_id} not found")
                return False
            
            # Validate path
            if not self._validate_path(path):
                logger.error(f"Invalid path for cargo {cargo_id}: {path}")
                return False
            
            # Calculate metrics for the path
            time_hours, cost, carbon = self._calculate_path_metrics(path, "task_1_time")
            
            # Complete the cargo
            self.complete_cargo(cargo_id, path, time_hours, cost, carbon)
            
            logger.debug(f"Cargo {cargo_id} routed successfully: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error routing cargo {cargo_id}: {e}")
            return False
