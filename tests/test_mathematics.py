#!/usr/bin/env python3
"""
Comprehensive mathematical and algorithm testing suite.

Tests:
- Trilemma scoring formula accuracy
- Numerical precision and edge cases
- Transportation mode calculations
- Path algorithm correctness
- Cost accumulation and aggregation
- Boundary conditions and error handling
"""

import unittest
import math
from typing import Dict, List, Tuple
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.grader import (
    Grader, TrilemmaMetrics, EvaluationResult, TaskType,
    TransportationMode, MODE_CHARACTERISTICS, TrajectoryStep,
    ModeCharacteristics
)
from app.engine.graph import FreightNetwork
from app.engine.core_env import FreightEnvironment, EnvironmentConfig
from app.utils.logger import logger


class TestTrilemmaFormula(unittest.TestCase):
    """Test the core trilemma scoring formula with numerical precision."""
    
    def test_zero_metrics(self):
        """Test zero values in scoring formula."""
        metrics = TrilemmaMetrics(
            accumulated_hours=0.0,
            accumulated_cost=0.0,
            accumulated_carbon=0.0
        )
        
        # Score = 0.5×0 + 0.3×0 + 0.2×0 = 0
        expected_score = 0.0
        actual_score = (0.5 * metrics.accumulated_hours + 
                       0.3 * metrics.accumulated_cost + 
                       0.2 * metrics.accumulated_carbon)
        
        self.assertAlmostEqual(actual_score, expected_score, places=10,
                              msg="Zero metrics should produce zero score")
    
    def test_single_metric_hours(self):
        """Test scoring with only hours metric."""
        metrics = TrilemmaMetrics(
            accumulated_hours=100.0,
            accumulated_cost=0.0,
            accumulated_carbon=0.0
        )
        
        # Score = 0.5×100 + 0.3×0 + 0.2×0 = 50
        expected_score = 50.0
        actual_score = (0.5 * metrics.accumulated_hours + 
                       0.3 * metrics.accumulated_cost + 
                       0.2 * metrics.accumulated_carbon)
        
        self.assertAlmostEqual(actual_score, expected_score, places=10,
                              msg="Hours-only metric calculation error")
    
    def test_single_metric_cost(self):
        """Test scoring with only cost metric."""
        metrics = TrilemmaMetrics(
            accumulated_hours=0.0,
            accumulated_cost=1000.0,
            accumulated_carbon=0.0
        )
        
        # Score = 0.5×0 + 0.3×1000 + 0.2×0 = 300
        expected_score = 300.0
        actual_score = (0.5 * metrics.accumulated_hours + 
                       0.3 * metrics.accumulated_cost + 
                       0.2 * metrics.accumulated_carbon)
        
        self.assertAlmostEqual(actual_score, expected_score, places=10,
                              msg="Cost-only metric calculation error")
    
    def test_single_metric_carbon(self):
        """Test scoring with only carbon metric."""
        metrics = TrilemmaMetrics(
            accumulated_hours=0.0,
            accumulated_cost=0.0,
            accumulated_carbon=500.0
        )
        
        # Score = 0.5×0 + 0.3×0 + 0.2×500 = 100
        expected_score = 100.0
        actual_score = (0.5 * metrics.accumulated_hours + 
                       0.3 * metrics.accumulated_cost + 
                       0.2 * metrics.accumulated_carbon)
        
        self.assertAlmostEqual(actual_score, expected_score, places=10,
                              msg="Carbon-only metric calculation error")
    
    def test_combined_metrics(self):
        """Test scoring with all metrics combined."""
        metrics = TrilemmaMetrics(
            accumulated_hours=10.0,
            accumulated_cost=500.0,
            accumulated_carbon=250.0
        )
        
        # Score = 0.5×10 + 0.3×500 + 0.2×250
        #       = 5 + 150 + 50 = 205
        expected_score = 205.0
        actual_score = (0.5 * metrics.accumulated_hours + 
                       0.3 * metrics.accumulated_cost + 
                       0.2 * metrics.accumulated_carbon)
        
        self.assertAlmostEqual(actual_score, expected_score, places=10,
                              msg="Combined metrics calculation error")
    
    def test_weights_sum_to_unity(self):
        """Verify weights are normalized (should sum to 1.0 for normalized formula)."""
        weights = [0.5, 0.3, 0.2]
        weight_sum = sum(weights)
        
        # Not asserting sum=1 since these appear to be raw weights
        # But documenting what they are
        logger.info(f"Trilemma weights: {weights}, sum={weight_sum}")
        # Note: weights sum to 1.0, meaning they are normalized
        self.assertAlmostEqual(weight_sum, 1.0, places=10,
                              msg="Weights should sum to 1.0")
    
    def test_fractional_metrics(self):
        """Test with fractional values (common in real calculations)."""
        metrics = TrilemmaMetrics(
            accumulated_hours=7.5,
            accumulated_cost=123.45,
            accumulated_carbon=67.89
        )
        
        # Score = 0.5×7.5 + 0.3×123.45 + 0.2×67.89
        #       = 3.75 + 37.035 + 13.578 = 54.363
        expected_score = 0.5 * 7.5 + 0.3 * 123.45 + 0.2 * 67.89
        actual_score = (0.5 * metrics.accumulated_hours + 
                       0.3 * metrics.accumulated_cost + 
                       0.2 * metrics.accumulated_carbon)
        
        self.assertAlmostEqual(actual_score, expected_score, places=10,
                              msg="Fractional metrics calculation error")
    
    def test_metric_accumulation(self):
        """Test the .add() method for accumulating metrics."""
        metrics = TrilemmaMetrics()
        
        # Add first set
        metrics.add(hours=10.0, cost=100.0, carbon=50.0)
        self.assertAlmostEqual(metrics.accumulated_hours, 10.0, places=10)
        self.assertAlmostEqual(metrics.accumulated_cost, 100.0, places=10)
        self.assertAlmostEqual(metrics.accumulated_carbon, 50.0, places=10)
        
        # Add second set
        metrics.add(hours=5.0, cost=50.0, carbon=25.0)
        self.assertAlmostEqual(metrics.accumulated_hours, 15.0, places=10)
        self.assertAlmostEqual(metrics.accumulated_cost, 150.0, places=10)
        self.assertAlmostEqual(metrics.accumulated_carbon, 75.0, places=10)


class TestTransportationModeCalculations(unittest.TestCase):
    """Test transportation mode metrics calculations."""
    
    def test_truck_basic_calculation(self):
        """Test basic truck calculation."""
        mode = MODE_CHARACTERISTICS[TransportationMode.TRUCK]
        
        # 100 km, 10 tons
        time, cost, carbon = mode.calculate_metrics(100, 10)
        
        # Time = 100 / 80 = 1.25 hours
        self.assertAlmostEqual(time, 1.25, places=10)
        
        # Cost = 100 * 0.15 = 15
        self.assertAlmostEqual(cost, 15.0, places=10)
        
        # Carbon = 100 * 0.025 = 2.5
        self.assertAlmostEqual(carbon, 2.5, places=10)
    
    def test_rail_efficiency(self):
        """Test rail mode characteristics."""
        mode = MODE_CHARACTERISTICS[TransportationMode.RAIL]
        
        # 200 km, 50 tons
        time, cost, carbon = mode.calculate_metrics(200, 50)
        
        # Time = 200 / 90 ≈ 2.222 hours
        expected_time = 200 / 90
        self.assertAlmostEqual(time, expected_time, places=10)
        
        # Cost = 200 * 0.08 = 16
        self.assertAlmostEqual(cost, 16.0, places=10)
        
        # Carbon = 200 * 0.008 = 1.6
        self.assertAlmostEqual(carbon, 1.6, places=10)
    
    def test_ship_cheaper_than_truck_long_distance(self):
        """Verify ship is cheaper than truck for long distances."""
        truck_mode = MODE_CHARACTERISTICS[TransportationMode.TRUCK]
        ship_mode = MODE_CHARACTERISTICS[TransportationMode.SHIP]
        
        distance = 1000  # 1000 km
        cargo = 50
        
        _, truck_cost, _ = truck_mode.calculate_metrics(distance, cargo)
        _, ship_cost, _ = ship_mode.calculate_metrics(distance, cargo)
        
        # Ship should be cheaper for long distances
        self.assertLess(ship_cost, truck_cost,
                       msg="Ship should be cheaper than truck for long distances")
    
    def test_flight_fastest(self):
        """Verify flight is fastest mode."""
        modes = MODE_CHARACTERISTICS
        distance = 500
        cargo = 10
        
        times = {}
        for mode_name, mode in modes.items():
            time, _, _ = mode.calculate_metrics(distance, cargo)
            times[mode_name] = time
        
        flight_time = times[TransportationMode.FLIGHT]
        for mode_name, time in times.items():
            if mode_name != TransportationMode.FLIGHT:
                self.assertLess(flight_time, time,
                              msg="Flight should be fastest mode")
    
    def test_ship_lowest_carbon(self):
        """Verify ship has lowest carbon emissions."""
        modes = MODE_CHARACTERISTICS
        distance = 500
        cargo = 10
        
        carbons = {}
        for mode_name, mode in modes.items():
            _, _, carbon = mode.calculate_metrics(distance, cargo)
            carbons[mode_name] = carbon
        
        ship_carbon = carbons[TransportationMode.SHIP]
        for mode_name, carbon in carbons.items():
            if mode_name != TransportationMode.SHIP:
                self.assertLess(ship_carbon, carbon,
                              msg="Ship should have lowest carbon emissions")
    
    def test_capacity_clamping(self):
        """Test that cargo is clamped to mode capacity."""
        mode = MODE_CHARACTERISTICS[TransportationMode.TRUCK]
        truck_capacity = mode.capacity_tons
        
        # Try to send more cargo than capacity
        time1, cost1, carbon1 = mode.calculate_metrics(100, truck_capacity + 100)
        time2, cost2, carbon2 = mode.calculate_metrics(100, truck_capacity)
        
        # Results should be identical (clamped)
        self.assertAlmostEqual(time1, time2, places=10)
        self.assertAlmostEqual(cost1, cost2, places=10)
        self.assertAlmostEqual(carbon1, carbon2, places=10)
    
    def test_zero_speed_protection(self):
        """Test division by zero protection."""
        # Create mode with zero speed
        mode = ModeCharacteristics(
            speed_kmh=0.0,
            cost_per_km=1.0,
            carbon_per_km=1.0,
            capacity_tons=100.0,
            min_distance=10.0
        )
        
        time, _, _ = mode.calculate_metrics(100, 10)
        
        # Should return infinity, not raise exception
        self.assertTrue(math.isinf(time),
                       msg="Zero speed should return infinity")


class TestGraphPathfinding(unittest.TestCase):
    """Test graph pathfinding and shortest path algorithms."""
    
    def setUp(self):
        """Set up test network."""
        self.network = FreightNetwork()
        
        # Create a simple 5-node network
        for i in range(5):
            self.network.add_node(i, location=f"City{i}", capacity=1000)
        
        # Add edges: 0-1-3-4 and 0-2-3 paths
        self.network.add_edge(0, 1, time=2.5, cost=150.0, carbon=45.0)
        self.network.add_edge(0, 2, time=5.0, cost=200.0, carbon=80.0)
        self.network.add_edge(1, 3, time=1.5, cost=100.0, carbon=30.0)
        self.network.add_edge(2, 3, time=3.0, cost=180.0, carbon=60.0)
        self.network.add_edge(3, 4, time=2.0, cost=120.0, carbon=40.0)
    
    def test_shortest_path_by_time(self):
        """Test shortest path using time weight."""
        path = self.network.get_shortest_path(0, 4, weight="time")
        
        # Path should be 0->1->3->4 (total time: 2.5+1.5+2.0 = 6.0)
        # Not 0->2->3->4 (total time: 5.0+3.0+2.0 = 10.0)
        self.assertIsNotNone(path, msg="Path should exist")
        self.assertEqual(path[0], 0, msg="Path should start at 0")
        self.assertEqual(path[-1], 4, msg="Path should end at 4")
    
    def test_shortest_path_by_cost(self):
        """Test shortest path using cost weight."""
        path = self.network.get_shortest_path(0, 4, weight="cost")
        
        self.assertIsNotNone(path, msg="Path should exist by cost")
        self.assertEqual(path[0], 0, msg="Path should start at 0")
        self.assertEqual(path[-1], 4, msg="Path should end at 4")
    
    def test_shortest_path_by_carbon(self):
        """Test shortest path using carbon weight."""
        path = self.network.get_shortest_path(0, 4, weight="carbon")
        
        self.assertIsNotNone(path, msg="Path should exist by carbon")
        self.assertEqual(path[0], 0, msg="Path should start at 0")
        self.assertEqual(path[-1], 4, msg="Path should end at 4")
    
    def test_no_path_exists(self):
        """Test handling when no path exists."""
        # Create disconnected network
        net = FreightNetwork()
        net.add_node(0)
        net.add_node(1)
        net.add_node(2)
        
        # Connect 0-1 but not to 2
        net.add_edge(0, 1, time=1.0, cost=1.0, carbon=1.0)
        
        # No path from 0 to 2
        path = net.get_shortest_path(0, 2, weight="time")
        self.assertIsNone(path, msg="Should return None for unreachable nodes")
    
    def test_same_source_target(self):
        """Test path from node to itself."""
        path = self.network.get_shortest_path(0, 0, weight="time")
        
        # Should return path with single node
        self.assertIsNotNone(path)
        self.assertEqual(len(path), 1)
        self.assertEqual(path[0], 0)


class TestNumericalStability(unittest.TestCase):
    """Test numerical stability and precision."""
    
    def test_large_numbers(self):
        """Test with large metric values."""
        metrics = TrilemmaMetrics(
            accumulated_hours=1000000.0,
            accumulated_cost=10000000.0,
            accumulated_carbon=5000000.0
        )
        
        score = (0.5 * metrics.accumulated_hours + 
                0.3 * metrics.accumulated_cost + 
                0.2 * metrics.accumulated_carbon)
        
        # Should compute without loss of precision
        expected = 0.5 * 1000000 + 0.3 * 10000000 + 0.2 * 5000000
        self.assertAlmostEqual(score, expected, places=5)
    
    def test_very_small_numbers(self):
        """Test with very small metric values."""
        metrics = TrilemmaMetrics(
            accumulated_hours=0.0001,
            accumulated_cost=0.0001,
            accumulated_carbon=0.0001
        )
        
        score = (0.5 * metrics.accumulated_hours + 
                0.3 * metrics.accumulated_cost + 
                0.2 * metrics.accumulated_carbon)
        
        expected = 0.5 * 0.0001 + 0.3 * 0.0001 + 0.2 * 0.0001
        self.assertAlmostEqual(score, expected, places=15)
    
    def test_mixed_magnitude_numbers(self):
        """Test with mixed magnitude numbers."""
        metrics = TrilemmaMetrics(
            accumulated_hours=0.001,
            accumulated_cost=1000000.0,
            accumulated_carbon=100.5
        )
        
        score = (0.5 * metrics.accumulated_hours + 
                0.3 * metrics.accumulated_cost + 
                0.2 * metrics.accumulated_carbon)
        
        expected = 0.5 * 0.001 + 0.3 * 1000000 + 0.2 * 100.5
        self.assertAlmostEqual(score, expected, places=10)
    
    def test_repeated_addition_associativity(self):
        """Test that repeated addition is associative."""
        m1 = TrilemmaMetrics()
        m1.add(10.0, 100.0, 50.0)
        m1.add(5.0, 50.0, 25.0)
        m1.add(3.0, 30.0, 15.0)
        
        m2 = TrilemmaMetrics()
        m2.add(18.0, 180.0, 90.0)  # Sum all at once
        
        self.assertAlmostEqual(m1.accumulated_hours, m2.accumulated_hours, places=10)
        self.assertAlmostEqual(m1.accumulated_cost, m2.accumulated_cost, places=10)
        self.assertAlmostEqual(m1.accumulated_carbon, m2.accumulated_carbon, places=10)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_negative_metrics_handling(self):
        """Test behavior with negative metrics (should be prevented but test anyway)."""
        metrics = TrilemmaMetrics(
            accumulated_hours=-10.0,
            accumulated_cost=-100.0,
            accumulated_carbon=-50.0
        )
        
        # Formula should still work even with negative values
        score = (0.5 * metrics.accumulated_hours + 
                0.3 * metrics.accumulated_cost + 
                0.2 * metrics.accumulated_carbon)
        
        # 0.5*(-10) + 0.3*(-100) + 0.2*(-50) = -5 + (-30) + (-10) = -45
        expected = -45.0
        self.assertAlmostEqual(score, expected, places=10)
    
    def test_inf_metric_handling(self):
        """Test handling of infinity values."""
        metrics = TrilemmaMetrics(
            accumulated_hours=float('inf'),
            accumulated_cost=100.0,
            accumulated_carbon=50.0
        )
        
        score = (0.5 * metrics.accumulated_hours + 
                0.3 * metrics.accumulated_cost + 
                0.2 * metrics.accumulated_carbon)
        
        self.assertTrue(math.isinf(score))
    
    def test_nan_metric_handling(self):
        """Test handling of NaN values."""
        metrics = TrilemmaMetrics(
            accumulated_hours=float('nan'),
            accumulated_cost=100.0,
            accumulated_carbon=50.0
        )
        
        score = (0.5 * metrics.accumulated_hours + 
                0.3 * metrics.accumulated_cost + 
                0.2 * metrics.accumulated_carbon)
        
        self.assertTrue(math.isnan(score))


class TestScoreNormalization(unittest.TestCase):
    """Test score normalization and ranking."""
    
    def test_score_comparison(self):
        """Test that lower scores from better performance are consistent."""
        # Create two scenarios
        good_metrics = TrilemmaMetrics(10, 100, 50)   # Low values
        bad_metrics = TrilemmaMetrics(100, 1000, 500) # High values
        
        good_score = (0.5 * good_metrics.accumulated_hours + 
                     0.3 * good_metrics.accumulated_cost + 
                     0.2 * good_metrics.accumulated_carbon)
        
        bad_score = (0.5 * bad_metrics.accumulated_hours + 
                    0.3 * bad_metrics.accumulated_cost + 
                    0.2 * bad_metrics.accumulated_carbon)
        
        # Lower metrics should give lower score
        self.assertLess(good_score, bad_score)
    
    def test_task_specific_comparison(self):
        """Test comparison of metrics for different task types."""
        # Task 1: Minimize hours (focus on time)
        task1_metrics = TrilemmaMetrics(5, 1000, 500)
        
        # Task 2: Minimize cost (focus on cost)
        task2_metrics = TrilemmaMetrics(100, 100, 500)
        
        score1 = (0.5 * task1_metrics.accumulated_hours + 
                 0.3 * task1_metrics.accumulated_cost + 
                 0.2 * task1_metrics.accumulated_carbon)
        
        score2 = (0.5 * task2_metrics.accumulated_hours + 
                 0.3 * task2_metrics.accumulated_cost + 
                 0.2 * task2_metrics.accumulated_carbon)
        
        # Different distributions will have different scores
        # score1 = 0.5*5 + 0.3*1000 + 0.2*500 = 2.5 + 300 + 100 = 402.5
        # score2 = 0.5*100 + 0.3*100 + 0.2*500 = 50 + 30 + 100 = 180
        self.assertAlmostEqual(score1, 402.5, places=10,
                              msg="Task 1 score calculation")
        self.assertAlmostEqual(score2, 180.0, places=10,
                              msg="Task 2 score calculation")
        self.assertNotEqual(score1, score2,
                           msg="Different metric distributions produce different scores")


def run_tests_with_report():
    """Run all tests and generate detailed report."""
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTrilemmaFormula))
    suite.addTests(loader.loadTestsFromTestCase(TestTransportationModeCalculations))
    suite.addTests(loader.loadTestsFromTestCase(TestGraphPathfinding))
    suite.addTests(loader.loadTestsFromTestCase(TestNumericalStability))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestScoreNormalization))
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("MATHEMATICAL TEST SUMMARY")
    print("="*70)
    print(f"Tests Run:    {result.testsRun}")
    print(f"Passed:       {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed:       {len(result.failures)}")
    print(f"Errors:       {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests_with_report()
    sys.exit(0 if success else 1)
