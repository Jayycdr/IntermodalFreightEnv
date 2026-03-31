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
            step = TrajectoryStep(
                step=step_dict.get("step", i),
                cargo_id=step_dict.get("cargo_id", 0),
                action=step_dict.get("action", {}),
                state=step_dict.get("state", {}),
                reward=step_dict.get("reward", 0.0),
                done=step_dict.get("done", False),
                info=step_dict.get("info", {}),
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
        
        Returns:
            TrilemmaMetrics with accumulated values
        """
        metrics = TrilemmaMetrics()
        
        for step in self.trajectory:
            # Get trilemma from step info if available
            if "trilemma" in step.info:
                trilemma = step.info["trilemma"]
                metrics.add(
                    hours=trilemma.get("accumulated_hours", 0.0),
                    cost=trilemma.get("accumulated_cost", 0.0),
                    carbon=trilemma.get("accumulated_carbon", 0.0),
                )
        
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
