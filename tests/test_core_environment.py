#!/usr/bin/env python3
"""
Comprehensive tests for the FreightEnvironment core functionality.

Tests:
- Environment initialization and configuration
- Cargo management (add, get, complete)
- Network setup and topology
- Path validation
- State management
- Reward calculation using trilemma metrics
- Episode mechanics
"""

import pytest

from app.engine.core_env import (
    FreightEnvironment,
    EnvironmentConfig,
    TrilemmaMetrics,
)
from app.constants import (
    TRILEMMA_WEIGHT_TIME,
    TRILEMMA_WEIGHT_COST,
    TRILEMMA_WEIGHT_CARBON,
)


class TestEnvironmentInitialization:
    """Test environment setup and initialization."""

    def test_default_initialization(self):
        """Test creating environment with default config."""
        env = FreightEnvironment()
        assert env.current_step == 0
        assert env.cargo_counter == 0
        assert len(env.active_cargos) == 0
        assert len(env.completed_cargos) == 0
        assert isinstance(env.trilemma, TrilemmaMetrics)

    def test_custom_config(self):
        """Test creating environment with custom config."""
        config = EnvironmentConfig(
            num_nodes=10,
            max_steps=500,
            seed=42
        )
        env = FreightEnvironment(config)
        assert env.config.num_nodes == 10
        assert env.config.max_steps == 500
        assert env.config.seed == 42

    def test_network_setup(self):
        """Test network configuration."""
        env = FreightEnvironment()
        network = {
            "nodes": [
                {"id": 0, "location": "A"},
                {"id": 1, "location": "B"},
                {"id": 2, "location": "C"},
            ],
            "edges": [
                {"source": 0, "target": 1, "time": 1.0, "cost": 100.0, "carbon": 50.0},
                {"source": 1, "target": 2, "time": 2.0, "cost": 200.0, "carbon": 100.0},
            ]
        }
        
        env.setup_network(network)
        assert len(env.nodes) == 3
        assert len(env.edges) == 2
        assert env.config.num_nodes == 3


class TestCargoManagement:
    """Test cargo creation, tracking, and completion."""

    def setup_method(self):
        """Setup test environment."""
        self.env = FreightEnvironment()
        self.network = {
            "nodes": [
                {"id": 0, "location": "Origin"},
                {"id": 1, "location": "Middle"},
                {"id": 2, "location": "Destination"},
            ],
            "edges": [
                {"source": 0, "target": 1, "time": 1.5, "cost": 150.0, "carbon": 75.0},
                {"source": 1, "target": 2, "time": 2.0, "cost": 200.0, "carbon": 100.0},
                {"source": 0, "target": 2, "time": 3.0, "cost": 300.0, "carbon": 150.0},
            ]
        }
        self.env.setup_network(self.network)

    def test_add_cargo(self):
        """Test adding cargo."""
        cargo = self.env.add_cargo(origin=0, destination=2, quantity=100.0)
        
        assert cargo.cargo_id == 0
        assert cargo.origin == 0
        assert cargo.destination == 2
        assert cargo.quantity == 100.0
        assert len(self.env.active_cargos) == 1

    def test_add_multiple_cargos(self):
        """Test adding multiple cargos."""
        cargo1 = self.env.add_cargo(origin=0, destination=1)
        cargo2 = self.env.add_cargo(origin=1, destination=2)
        cargo3 = self.env.add_cargo(origin=0, destination=2)
        
        assert cargo1.cargo_id == 0
        assert cargo2.cargo_id == 1
        assert cargo3.cargo_id == 2
        assert len(self.env.active_cargos) == 3

    def test_get_cargo(self):
        """Test retrieving cargo by ID."""
        cargo = self.env.add_cargo(origin=0, destination=2)
        retrieved = self.env.get_cargo(cargo.cargo_id)
        
        assert retrieved is not None
        assert retrieved.cargo_id == cargo.cargo_id
        assert retrieved.origin == cargo.origin

    def test_complete_cargo(self):
        """Test completing cargo and metrics update."""
        cargo = self.env.add_cargo(origin=0, destination=1)
        
        # Complete cargo with metrics
        self.env.complete_cargo(
            cargo_id=cargo.cargo_id,
            path=[0, 1],
            time_hours=1.5,
            cost=150.0,
            carbon=75.0
        )
        
        # Verify cargo state
        assert cargo.completed is True
        assert cargo.path_taken == [0, 1]
        assert cargo.time_hours == 1.5
        
        # Verify metrics accumulated
        assert self.env.trilemma.accumulated_hours == 1.5
        assert self.env.trilemma.accumulated_cost == 150.0
        assert self.env.trilemma.accumulated_carbon == 75.0
        
        # Verify cargo moved to completed
        assert cargo not in self.env.active_cargos
        assert cargo in self.env.completed_cargos

    def test_cargos_property_backward_compat(self):
        """Test backward compatibility cargos property."""
        cargo1 = self.env.add_cargo(origin=0, destination=1)
        cargo2 = self.env.add_cargo(origin=1, destination=2)
        
        cargos_dict = self.env.cargos
        assert isinstance(cargos_dict, dict)
        assert cargo1.cargo_id in cargos_dict
        assert cargo2.cargo_id in cargos_dict


class TestPathValidation:
    """Test path validation and route cargo."""

    def setup_method(self):
        """Setup test environment."""
        self.env = FreightEnvironment()
        # Create a simple 3-node network
        self.network = {
            "nodes": [
                {"id": 0, "location": "A"},
                {"id": 1, "location": "B"},
                {"id": 2, "location": "C"},
            ],
            "edges": [
                {"source": 0, "target": 1, "time": 1.0, "cost": 100.0, "carbon": 50.0},
                {"source": 1, "target": 2, "time": 2.0, "cost": 200.0, "carbon": 100.0},
                {"source": 0, "target": 2, "time": 2.5, "cost": 250.0, "carbon": 125.0},
            ]
        }
        self.env.setup_network(self.network)

    def test_valid_path_direct(self):
        """Test path validation for direct edge."""
        assert self.env._validate_path([0, 1]) is True
        assert self.env._validate_path([1, 2]) is True
        assert self.env._validate_path([0, 2]) is True

    def test_valid_path_multi_hop(self):
        """Test path validation for multi-hop paths."""
        assert self.env._validate_path([0, 1, 2]) is True

    def test_invalid_path_missing_edge(self):
        """Test path validation fails for non-existent edges."""
        # No edge from 2 to 0 or 2 to 1
        assert self.env._validate_path([2, 0]) is False
        assert self.env._validate_path([2, 1]) is False

    def test_invalid_path_single_node(self):
        """Test path validation fails for single node."""
        assert self.env._validate_path([0]) is False
        assert self.env._validate_path([]) is False

    def test_route_cargo_valid_path(self):
        """Test route_cargo with valid path."""
        cargo = self.env.add_cargo(origin=0, destination=2)
        path = [0, 2]
        
        success = self.env.route_cargo(cargo.cargo_id, path)
        
        assert success is True
        assert cargo.completed is True
        assert cargo.path_taken == path
        # Direct path 0→2 should have time=2.5
        assert cargo.time_hours == 2.5

    def test_route_cargo_invalid_cargo(self):
        """Test route_cargo with non-existent cargo."""
        success = self.env.route_cargo(999, [0, 1])
        assert success is False

    def test_route_cargo_invalid_path(self):
        """Test route_cargo with invalid path."""
        cargo = self.env.add_cargo(origin=0, destination=1)
        success = self.env.route_cargo(cargo.cargo_id, [2, 0])  # Invalid path
        
        assert success is False
        assert cargo.completed is False  # Cargo shouldn't be completed


class TestRewardCalculation:
    """Test reward calculation using trilemma metrics."""

    def setup_method(self):
        """Setup test environment."""
        self.env = FreightEnvironment()
        self.network = {
            "nodes": [
                {"id": 0, "location": "A"},
                {"id": 1, "location": "B"},
            ],
            "edges": [
                {"source": 0, "target": 1, "time": 1.0, "cost": 100.0, "carbon": 50.0},
            ]
        }
        self.env.setup_network(self.network)

    def test_reward_zero_metrics(self):
        """Test reward when metrics are zero."""
        action = {}
        reward = self.env._calculate_reward(action)
        
        assert reward == 0.0  # -0.0 negative weighted cost

    def test_reward_with_metrics(self):
        """Test reward calculation with known metrics."""
        # Manually set trilemma metrics
        self.env.trilemma.accumulated_hours = 1.0
        self.env.trilemma.accumulated_cost = 100.0
        self.env.trilemma.accumulated_carbon = 50.0
        
        reward = self.env._calculate_reward({})
        
        # Expected: -(0.5*1.0 + 0.3*100.0 + 0.2*50.0) = -(0.5 + 30.0 + 10.0) = -40.5
        expected = -(TRILEMMA_WEIGHT_TIME * 1.0 +
                     TRILEMMA_WEIGHT_COST * 100.0 +
                     TRILEMMA_WEIGHT_CARBON * 50.0)
        
        assert abs(reward - expected) < 1e-6

    def test_reward_negative(self):
        """Test that reward is negative when metrics are positive."""
        self.env.trilemma.accumulated_hours = 5.0
        self.env.trilemma.accumulated_cost = 500.0
        self.env.trilemma.accumulated_carbon = 250.0
        
        reward = self.env._calculate_reward({})
        assert reward < 0  # Minimizing cost means negative reward


class TestStateManagement:
    """Test environment state building and management."""

    def setup_method(self):
        """Setup test environment."""
        self.env = FreightEnvironment()
        self.network = {
            "nodes": [
                {"id": 0, "location": "A"},
                {"id": 1, "location": "B"},
            ],
            "edges": [
                {"source": 0, "target": 1, "time": 1.0, "cost": 100.0, "carbon": 50.0},
            ]
        }
        self.env.setup_network(self.network)

    def test_reset_state(self):
        """Test environment reset."""
        self.env.add_cargo(origin=0, destination=1)
        self.env.trilemma.accumulated_hours = 5.0
        
        state = self.env.reset()
        
        assert self.env.current_step == 0
        assert len(self.env.active_cargos) >= 0  # May have generated cargos
        assert self.env.trilemma.accumulated_hours == 0.0

    def test_state_structure(self):
        """Test that state has required structure."""
        state = self.env.reset()
        
        required_keys = ["step", "active_cargos", "completed_cargos", "trilemma", "network"]
        for key in required_keys:
            assert key in state, f"Missing key: {key}"

    def test_state_trilemma_structure(self):
        """Test trilemma metrics in state."""
        state = self.env.reset()
        trilemma = state["trilemma"]
        
        required = ["accumulated_hours", "accumulated_cost", "accumulated_carbon"]
        for key in required:
            assert key in trilemma, f"Missing key in trilemma: {key}"

    def test_state_network_structure(self):
        """Test network data in state."""
        state = self.env.reset()
        network = state["network"]
        
        assert "nodes" in network
        assert "edges" in network
        assert len(network["nodes"]) == 2  # Two nodes in our test network


class TestEpisodeMechanics:
    """Test episode completion and step mechanics."""

    def setup_method(self):
        """Setup test environment."""
        config = EnvironmentConfig(max_steps=10)
        self.env = FreightEnvironment(config)
        self.network = {
            "nodes": [
                {"id": 0, "location": "A"},
                {"id": 1, "location": "B"},
            ],
            "edges": [
                {"source": 0, "target": 1, "time": 1.0, "cost": 100.0, "carbon": 50.0},
            ]
        }
        self.env.setup_network(self.network)
        self.env.reset()

    def test_step_increments_counter(self):
        """Test that step increments the step counter."""
        initial_step = self.env.current_step
        state, reward, done, info = self.env.step({})
        
        assert self.env.current_step == initial_step + 1

    def test_step_return_values(self):
        """Test step returns correct values."""
        state, reward, done, info = self.env.step({})
        
        assert isinstance(state, dict)
        assert isinstance(reward, (int, float))
        assert isinstance(done, bool)
        assert isinstance(info, dict)

    def test_episode_ends_at_max_steps(self):
        """Test episode ends when max steps reached."""
        # Run until max steps
        done = False
        steps = 0
        while not done and steps < 100:
            state, reward, done, info = self.env.step({})
            steps += 1
        
        assert done is True
        assert self.env.current_step > 0

    def test_invalid_action_handling(self):
        """Test step handles invalid action gracefully."""
        invalid_actions = [
            None,
            {},
            {"cargo_id": 999},
            {"path": [999, 998]},
        ]
        
        for action in invalid_actions:
            state, reward, done, info = self.env.step(action)
            assert isinstance(state, dict)
            assert isinstance(reward, (int, float))


class TestMetricsAccumulation:
    """Test that metrics accumulate correctly across steps."""

    def setup_method(self):
        """Setup test environment."""
        self.env = FreightEnvironment()
        self.network = {
            "nodes": [
                {"id": 0, "location": "A"},
                {"id": 1, "location": "B"},
                {"id": 2, "location": "C"},
            ],
            "edges": [
                {"source": 0, "target": 1, "time": 1.0, "cost": 100.0, "carbon": 50.0},
                {"source": 1, "target": 2, "time": 2.0, "cost": 200.0, "carbon": 100.0},
            ]
        }
        self.env.setup_network(self.network)
        self.env.reset()

    def test_metrics_accumulate_from_multiple_cargos(self):
        """Test metrics accumulate from multiple cargo completions."""
        # Complete first cargo
        cargo1 = self.env.add_cargo(origin=0, destination=1)
        self.env.complete_cargo(
            cargo_id=cargo1.cargo_id,
            path=[0, 1],
            time_hours=1.0,
            cost=100.0,
            carbon=50.0
        )
        
        # Complete second cargo
        cargo2 = self.env.add_cargo(origin=1, destination=2)
        self.env.complete_cargo(
            cargo_id=cargo2.cargo_id,
            path=[1, 2],
            time_hours=2.0,
            cost=200.0,
            carbon=100.0
        )
        
        # Check accumulated metrics
        assert self.env.trilemma.accumulated_hours == 3.0
        assert self.env.trilemma.accumulated_cost == 300.0
        assert self.env.trilemma.accumulated_carbon == 150.0

    def test_trilemma_to_dict(self):
        """Test trilemma to_dict conversion."""
        self.env.trilemma.accumulated_hours = 1.5
        self.env.trilemma.accumulated_cost = 150.0
        self.env.trilemma.accumulated_carbon = 75.0
        
        trilemma_dict = self.env.trilemma.to_dict()
        
        assert trilemma_dict["accumulated_hours"] == 1.5
        assert trilemma_dict["accumulated_cost"] == 150.0
        assert trilemma_dict["accumulated_carbon"] == 75.0


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_episode(self):
        """Test a complete episode with cargo delivery."""
        env = FreightEnvironment(EnvironmentConfig(max_steps=100))
        network = {
            "nodes": [
                {"id": 0, "location": "Origin"},
                {"id": 1, "location": "Destination"},
            ],
            "edges": [
                {"source": 0, "target": 1, "time": 2.0, "cost": 200.0, "carbon": 100.0},
            ]
        }
        env.setup_network(network)
        env.reset()
        
        # Get initial cargo
        assert len(env.active_cargos) >= 0
        
        if env.active_cargos:
            cargo = env.active_cargos[0]
            action = {
                "task_type": "task_1_time",
                "cargo_id": cargo.cargo_id,
                "path": [cargo.origin, cargo.destination]
            }
            
            state, reward, done, info = env.step(action)
            
            assert reward is not None
            assert state is not None
            assert "trilemma" in state

    def test_multiple_episodes(self):
        """Test running multiple episodes."""
        env = FreightEnvironment(EnvironmentConfig(max_steps=5))
        network = {
            "nodes": [
                {"id": i, "location": f"Node{i}"}
                for i in range(3)
            ],
            "edges": [
                {"source": 0, "target": 1, "time": 1.0, "cost": 100.0, "carbon": 50.0},
                {"source": 1, "target": 2, "time": 1.0, "cost": 100.0, "carbon": 50.0},
            ]
        }
        env.setup_network(network)
        
        # Run multiple episodes
        for episode in range(3):
            env.reset()
            assert env.current_step == 0
            
            # Run some steps
            for _ in range(3):
                state, reward, done, info = env.step({})
                if done:
                    break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
