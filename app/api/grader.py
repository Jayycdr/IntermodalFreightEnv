"""
Grading and evaluation logic for the freight environment.

Evaluates agent performance against the trajectory using the weighted formula:
    Score = 0.5×time + 0.3×cost + 0.2×carbon
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.utils.logger import logger


class TaskType(str, Enum):
    """Task types for evaluation."""
    TASK_1_TIME = "task_1_time"
    TASK_2_COST = "task_2_cost"
    TASK_3_MULTIMODAL = "task_3_multimodal"


class TransportationMode(str, Enum):
    """Supported transportation modes with realistic characteristics."""
    TRUCK = "truck"
    SHIP = "ship"
    RAIL = "rail"
    FLIGHT = "flight"


@dataclass
class ModeCharacteristics:
    """Characteristics of each transportation mode per 100 km."""
    
    speed_kmh: float          # Average speed in km/h
    cost_per_km: float       # Cost in $100s per km
    carbon_per_km: float     # Carbon in tons per km
    capacity_tons: float     # Max cargo capacity in tons
    min_distance: float      # Minimum viable distance
    
    def calculate_metrics(self, distance_km: float, cargo_tons: float) -> tuple:
        """
        Calculate time, cost, carbon for a shipment.
        
        Returns: (hours, cost, carbon)
        """
        # Clamp cargo to capacity
        cargo = min(cargo_tons, self.capacity_tons)
        
        # Time = distance / speed
        time_hours = distance_km / self.speed_kmh if self.speed_kmh > 0 else float('inf')
        
        # Cost = distance * cost_per_km (scales with distance)
        cost = distance_km * self.cost_per_km
        
        # Carbon = distance * carbon_per_km (per km, not per ton)
        carbon = distance_km * self.carbon_per_km
        
        return time_hours, cost, carbon


# Mode characteristics (per 100 km, realistic data)
MODE_CHARACTERISTICS: Dict[TransportationMode, ModeCharacteristics] = {
    TransportationMode.TRUCK: ModeCharacteristics(
        speed_kmh=80.0,           # Average highway speed
        cost_per_km=0.15,         # $15 per 100 km
        carbon_per_km=0.025,      # High emissions
        capacity_tons=25.0,       # Typical truck capacity
        min_distance=50.0,
    ),
    TransportationMode.RAIL: ModeCharacteristics(
        speed_kmh=90.0,           # Average rail speed
        cost_per_km=0.08,         # $8 per 100 km (cheaper than truck)
        carbon_per_km=0.008,      # Much better emissions
        capacity_tons=100.0,      # High capacity
        min_distance=200.0,       # Needs longer distances
    ),
    TransportationMode.SHIP: ModeCharacteristics(
        speed_kmh=40.0,           # Slow but steady
        cost_per_km=0.05,         # $5 per 100 km (cheapest!)
        carbon_per_km=0.003,      # Best carbon footprint
        capacity_tons=500.0,      # Huge capacity
        min_distance=500.0,       # For long distances only
    ),
    TransportationMode.FLIGHT: ModeCharacteristics(
        speed_kmh=900.0,          # Very fast
        cost_per_km=1.0,          # $100 per 100 km (most expensive!)
        carbon_per_km=0.15,       # Worst carbon footprint
        capacity_tons=50.0,       # Medium capacity
        min_distance=300.0,       # For long intercontinental routes
    ),
}


@dataclass
class TrajectoryStep:
    """Single step in an agent trajectory."""
    
    step: int
    cargo_id: int
    action: Dict[str, Any]
    state: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]
    
    # Transportation mode (new field)
    mode: TransportationMode = TransportationMode.TRUCK
    distance_km: float = 0.0
    cargo_tons: float = 0.0


@dataclass
class TrilemmaMetrics:
    """Accumulates trilemma (time, cost, carbon) metrics."""
    
    accumulated_hours: float = 0.0
    accumulated_cost: float = 0.0
    accumulated_carbon: float = 0.0
    
    def add(self, hours: float = 0.0, cost: float = 0.0, carbon: float = 0.0) -> None:
        """Add metrics."""
        self.accumulated_hours += hours
        self.accumulated_cost += cost
        self.accumulated_carbon += carbon
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "accumulated_hours": self.accumulated_hours,
            "accumulated_cost": self.accumulated_cost,
            "accumulated_carbon": self.accumulated_carbon,
        }


@dataclass
class EvaluationResult:
    """Complete evaluation result."""
    
    task_type: TaskType
    weighted_score: float  # 0.5×time + 0.3×cost + 0.2×carbon
    raw_metrics: TrilemmaMetrics
    task_specific_score: float  # Time for Task1, Cost for Task2, etc.
    cargos_delivered: int
    num_steps: int
    trajectory_length: int
    efficiency_score: float  # 0-100 normalized
    feedback: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_type": self.task_type.value,
            "weighted_score": self.weighted_score,
            "raw_metrics": self.raw_metrics.to_dict(),
            "task_specific_score": self.task_specific_score,
            "cargos_delivered": self.cargos_delivered,
            "num_steps": self.num_steps,
            "trajectory_length": self.trajectory_length,
            "efficiency_score": self.efficiency_score,
            "feedback": self.feedback,
        }


class Grader:
    """
    Evaluates agent performance based on trajectory.
    
    Weighted scoring formula:
        Score = 0.5×accumulated_hours + 0.3×accumulated_cost + 0.2×accumulated_carbon
    
    This balances all three trilemma objectives.
    """

    def __init__(self):
        """Initialize the grader."""
        self.trajectory: List[TrajectoryStep] = []
        logger.info("Grader initialized")

    def add_step(self, step: TrajectoryStep) -> None:
        """
        Add a step to the trajectory.
        
        Args:
            step: TrajectoryStep to add
        """
        self.trajectory.append(step)

    def load_trajectory(self, steps: List[Dict[str, Any]]) -> None:
        """
        Load a complete trajectory from list of dicts.
        
        Args:
            steps: List of step dictionaries
        """
        self.trajectory.clear()
        for i, step_dict in enumerate(steps):
            # Extract mode and distance/cargo from action or info
            mode_str = step_dict.get("action", {}).get("mode")
            if not mode_str:
                mode_str = step_dict.get("info", {}).get("mode", "truck")
            
            try:
                mode = TransportationMode(mode_str)
            except (ValueError, TypeError):
                mode = TransportationMode.TRUCK
            
            distance_km = step_dict.get("action", {}).get("distance", 0.0)
            if not distance_km:
                distance_km = step_dict.get("info", {}).get("distance", 0.0)
            
            cargo_tons = step_dict.get("action", {}).get("cargo_tons", 0.0)
            if not cargo_tons:
                cargo_tons = step_dict.get("info", {}).get("cargo_tons", 0.0)
            
            step = TrajectoryStep(
                step=step_dict.get("step", i),
                cargo_id=step_dict.get("cargo_id", 0),
                action=step_dict.get("action", {}),
                state=step_dict.get("state", {}),
                reward=step_dict.get("reward", 0.0),
                done=step_dict.get("done", False),
                info=step_dict.get("info", {}),
                mode=mode,
                distance_km=float(distance_km),
                cargo_tons=float(cargo_tons),
            )
            self.trajectory.append(step)
        logger.info(f"Trajectory loaded with {len(self.trajectory)} steps")

    def evaluate(
        self,
        task_type: TaskType = TaskType.TASK_3_MULTIMODAL,
    ) -> EvaluationResult:
        """
        Evaluate the trajectory using the weighted formula.
        
        Formula: Score = 0.5×time + 0.3×cost + 0.2×carbon
        
        Args:
            task_type: Type of task being evaluated
            
        Returns:
            EvaluationResult with complete metrics
        """
        if not self.trajectory:
            logger.warning("Empty trajectory provided for evaluation")
            return EvaluationResult(
                task_type=task_type,
                weighted_score=0.0,
                raw_metrics=TrilemmaMetrics(),
                task_specific_score=0.0,
                cargos_delivered=0,
                num_steps=0,
                trajectory_length=0,
                efficiency_score=0.0,
                feedback="Empty trajectory",
            )

        # Extract trilemma metrics from trajectory
        metrics = self._extract_metrics()
        
        # Calculate weighted score
        weighted_score = self._calculate_weighted_score(metrics)
        
        # Calculate task-specific score
        task_score = self._calculate_task_specific_score(task_type, metrics)
        
        # Count deliveries
        cargos_delivered = self._count_deliveries()
        
        # Calculate efficiency
        efficiency_score = self._calculate_efficiency(
            weighted_score,
            task_type,
            cargos_delivered,
            len(self.trajectory)
        )
        
        # Generate feedback
        feedback = self._generate_feedback(
            task_type,
            metrics,
            cargos_delivered,
            efficiency_score
        )
        
        result = EvaluationResult(
            task_type=task_type,
            weighted_score=weighted_score,
            raw_metrics=metrics,
            task_specific_score=task_score,
            cargos_delivered=cargos_delivered,
            num_steps=len(self.trajectory),
            trajectory_length=len(self.trajectory),
            efficiency_score=efficiency_score,
            feedback=feedback,
        )
        
        logger.info(f"Trajectory evaluated: score={efficiency_score:.1f}, "
                   f"deliveries={cargos_delivered}, task={task_type.value}")
        
        return result

    def _extract_metrics(self) -> TrilemmaMetrics:
        """
        Extract trilemma metrics from trajectory.
        
        Uses transportation mode characteristics if available,
        otherwise falls back to explicit metrics in step info.
        
        Returns:
            TrilemmaMetrics with accumulated values
        """
        metrics = TrilemmaMetrics()
        
        for step in self.trajectory:
            # Try to get mode-based metrics first
            if step.distance_km > 0 or step.cargo_tons > 0:
                # Use mode characteristics to calculate metrics
                characteristics = MODE_CHARACTERISTICS[step.mode]
                hours, cost, carbon = characteristics.calculate_metrics(
                    step.distance_km,
                    step.cargo_tons
                )
                metrics.add(hours=hours, cost=cost, carbon=carbon)
            elif "trilemma" in step.info:
                # Fallback: use explicit metrics from step info
                trilemma = step.info["trilemma"]
                metrics.add(
                    hours=trilemma.get("accumulated_hours", 0.0),
                    cost=trilemma.get("accumulated_cost", 0.0),
                    carbon=trilemma.get("accumulated_carbon", 0.0),
                )
            # else: step has no metrics, skip (contributes 0)
        
        return metrics

    def _calculate_weighted_score(self, metrics: TrilemmaMetrics) -> float:
        """
        Calculate weighted score using the formula:
        Score = 0.5×time + 0.3×cost + 0.2×carbon
        
        Args:
            metrics: TrilemmaMetrics
            
        Returns:
            Weighted score (lower is better)
        """
        score = (
            0.5 * metrics.accumulated_hours +
            0.3 * metrics.accumulated_cost +
            0.2 * metrics.accumulated_carbon
        )
        return score

    def _calculate_task_specific_score(
        self,
        task_type: TaskType,
        metrics: TrilemmaMetrics,
    ) -> float:
        """
        Calculate task-specific score.
        
        Args:
            task_type: Type of task
            metrics: TrilemmaMetrics
            
        Returns:
            Task-specific score
        """
        if task_type == TaskType.TASK_1_TIME:
            # Task 1: Time minimization
            return metrics.accumulated_hours
        elif task_type == TaskType.TASK_2_COST:
            # Task 2: Cost minimization
            return metrics.accumulated_cost
        else:  # TASK_3_MULTIMODAL
            # Task 3: Carbon minimization (environmental focus)
            return metrics.accumulated_carbon

    def _count_deliveries(self) -> int:
        """
        Count successful cargo deliveries from trajectory.
        
        Returns:
            Number of deliveries
        """
        deliveries = 0
        for step in self.trajectory:
            if "completed_cargos" in step.info:
                deliveries = step.info["completed_cargos"]
        return deliveries

    def _calculate_efficiency(
        self,
        weighted_score: float,
        task_type: TaskType,
        deliveries: int,
        num_steps: int,
    ) -> float:
        """
        Calculate efficiency score (0-100 normalized).
        
        Rewards:
        - Low weighted score (cost/time/carbon)
        - High delivery count
        - Low step count
        
        Args:
            weighted_score: Raw weighted score
            task_type: Type of task
            deliveries: Number of delivered cargos
            num_steps: Number of steps taken
            
        Returns:
            Efficiency score 0-100
        """
        # Base score from weighted metrics (penalize high cost)
        metric_score = max(0, 100 - (weighted_score / 10))
        
        # Bonus for deliveries
        delivery_bonus = deliveries * 10
        
        # Penalty for excess steps
        step_penalty = max(0, (num_steps - 10) * 0.5)
        
        # Combine
        efficiency = metric_score + delivery_bonus - step_penalty
        
        # Clamp to 0-100
        return max(0, min(100, efficiency))

    def _generate_feedback(
        self,
        task_type: TaskType,
        metrics: TrilemmaMetrics,
        deliveries: int,
        efficiency: float,
    ) -> str:
        """
        Generate human-readable feedback.
        
        Args:
            task_type: Type of task
            metrics: TrilemmaMetrics
            deliveries: Number of deliveries
            efficiency: Efficiency score
            
        Returns:
            Feedback string
        """
        feedback_parts = [
            f"Task: {task_type.value}",
            f"Efficiency: {efficiency:.1f}/100",
            f"Deliveries: {deliveries}",
            f"Time: {metrics.accumulated_hours:.1f}h",
            f"Cost: ${metrics.accumulated_cost:.0f}",
            f"Carbon: {metrics.accumulated_carbon:.1f}kg",
        ]
        
        # Add specific feedback
        if efficiency >= 80:
            feedback_parts.append("Status: Excellent performance!")
        elif efficiency >= 60:
            feedback_parts.append("Status: Good performance")
        elif efficiency >= 40:
            feedback_parts.append("Status: Fair performance")
        else:
            feedback_parts.append("Status: Needs improvement")
        
        return " | ".join(feedback_parts)

    def evaluate_multiple_trajectories(
        self,
        trajectories: Dict[str, List[Dict[str, Any]]],
        task_type: TaskType = TaskType.TASK_3_MULTIMODAL,
    ) -> Dict[str, EvaluationResult]:
        """
        Evaluate multiple trajectories (e.g., from different agents).
        
        Args:
            trajectories: Dict of {agent_name: trajectory_steps}
            task_type: Type of task
            
        Returns:
            Dict of {agent_name: EvaluationResult}
        """
        results = {}
        
        for agent_name, trajectory_steps in trajectories.items():
            self.load_trajectory(trajectory_steps)
            result = self.evaluate(task_type)
            results[agent_name] = result
            logger.info(f"Evaluated agent '{agent_name}': score={result.efficiency_score:.1f}")
        
        return results

    def compare_agents(
        self,
        trajectories: Dict[str, List[Dict[str, Any]]],
        task_type: TaskType = TaskType.TASK_3_MULTIMODAL,
    ) -> Dict[str, Any]:
        """
        Compare performance across multiple agents.
        
        Args:
            trajectories: Dict of {agent_name: trajectory_steps}
            task_type: Type of task
            
        Returns:
            Comparison summary
        """
        results = self.evaluate_multiple_trajectories(trajectories, task_type)
        
        # Rank agents by efficiency
        ranked = sorted(
            results.items(),
            key=lambda x: x[1].efficiency_score,
            reverse=True
        )
        
        comparison = {
            "task_type": task_type.value,
            "num_agents": len(results),
            "rankings": [
                {
                    "rank": i + 1,
                    "agent": name,
                    "efficiency_score": result.efficiency_score,
                    "weighted_score": result.weighted_score,
                    "deliveries": result.cargos_delivered,
                }
                for i, (name, result) in enumerate(ranked)
            ],
            "best_agent": ranked[0][0] if ranked else None,
            "worst_agent": ranked[-1][0] if ranked else None,
        }
        
        return comparison

    def reset(self) -> None:
        """Reset grader state."""
        self.trajectory.clear()
        logger.info("Grader reset")
    
    @staticmethod
    def get_mode_characteristics() -> Dict[str, Dict[str, Any]]:
        """
        Get characteristics of all transportation modes.
        
        Returns:
            Dict with mode characteristics for reference
        """
        result = {}
        for mode, chars in MODE_CHARACTERISTICS.items():
            result[mode.value] = {
                "speed_kmh": chars.speed_kmh,
                "cost_per_km": chars.cost_per_km,
                "carbon_per_km": chars.carbon_per_km,
                "capacity_tons": chars.capacity_tons,
                "min_distance": chars.min_distance,
            }
        return result
    
    @staticmethod
    def example_trajectory(mode: str, distance_km: float, cargo_tons: float) -> Dict[str, Any]:
        """
        Generate an example trajectory for a specific mode.
        
        Args:
            mode: Transportation mode (truck, rail, ship, flight)
            distance_km: Distance to travel
            cargo_tons: Cargo weight
            
        Returns:
            Example trajectory step
        """
        try:
            transport_mode = TransportationMode(mode)
        except ValueError:
            transport_mode = TransportationMode.TRUCK
        
        characteristics = MODE_CHARACTERISTICS[transport_mode]
        hours, cost, carbon = characteristics.calculate_metrics(distance_km, cargo_tons)
        
        return {
            "action": {
                "mode": mode,
                "distance": distance_km,
                "cargo_tons": cargo_tons,
            },
            "info": {
                "mode": mode,
                "distance": distance_km,
                "cargo_tons": cargo_tons,
                "calculated_metrics": {
                    "hours": hours,
                    "cost": cost,
                    "carbon": carbon,
                }
            }
        }
