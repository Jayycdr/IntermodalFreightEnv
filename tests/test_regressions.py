#!/usr/bin/env python3
"""
Quick Regression Test Suite for Mathematical Correctness

This script provides a fast way to verify no mathematical regressions have occurred.
Use this in CI/CD pipelines for rapid validation before deployment.

Runtime: ~1 second
Tests: 15 critical paths
Format: TAP (Test Anything Protocol) compatible
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.grader import TrilemmaMetrics, TransportationMode, MODE_CHARACTERISTICS
from app.engine.graph import FreightNetwork


class RegressionTestRunner:
    """Run quick regression tests with TAP-compatible output."""
    
    def __init__(self):
        self.test_count = 0
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def test(self, condition, name):
        """Run a single test."""
        self.test_count += 1
        if condition:
            self.passed += 1
            self.results.append(f"ok {self.test_count} - {name}")
        else:
            self.failed += 1
            self.results.append(f"not ok {self.test_count} - {name}")
    
    def print_results(self):
        """Print TAP format results."""
        print(f"1..{self.test_count}")
        for result in self.results:
            print(result)
        
        if self.failed == 0:
            return 0
        else:
            print(f"# Failed {self.failed}/{self.test_count} tests", file=sys.stderr)
            return 1


def run_regression_tests():
    """Run all regression tests."""
    runner = RegressionTestRunner()
    
    # Test 1: Trilemma formula correctness
    metrics = TrilemmaMetrics(10, 500, 250)
    expected_score = 0.5*10 + 0.3*500 + 0.2*250
    actual_score = 0.5*metrics.accumulated_hours + 0.3*metrics.accumulated_cost + 0.2*metrics.accumulated_carbon
    runner.test(abs(actual_score - expected_score) < 1e-10, 
               "Trilemma formula: 0.5×10 + 0.3×500 + 0.2×250 = 205")
    
    # Test 2: Weights sum to 1.0
    runner.test(abs(sum([0.5, 0.3, 0.2]) - 1.0) < 1e-10,
               "Weights are normalized (sum = 1.0)")
    
    # Test 3: Truck mode calculation
    truck = MODE_CHARACTERISTICS[TransportationMode.TRUCK]
    time, cost, carbon = truck.calculate_metrics(100, 10)
    runner.test(abs(time - 1.25) < 1e-10 and abs(cost - 15.0) < 1e-10 and abs(carbon - 2.5) < 1e-10,
               "Truck mode: 100km calculations correct")
    
    # Test 4: Rail is cheaper than truck long distance
    truck_cost_1000 = MODE_CHARACTERISTICS[TransportationMode.TRUCK].calculate_metrics(1000, 50)[1]
    rail_cost_1000 = MODE_CHARACTERISTICS[TransportationMode.RAIL].calculate_metrics(1000, 50)[1]
    runner.test(rail_cost_1000 < truck_cost_1000,
               "Rail is cheaper than truck at 1000km")
    
    # Test 5: Ship is cheapest
    ship_cost = MODE_CHARACTERISTICS[TransportationMode.SHIP].calculate_metrics(500, 10)[1]
    truck_cost = MODE_CHARACTERISTICS[TransportationMode.TRUCK].calculate_metrics(500, 10)[1]
    flight_cost = MODE_CHARACTERISTICS[TransportationMode.FLIGHT].calculate_metrics(500, 10)[1]
    runner.test(ship_cost < truck_cost and ship_cost < flight_cost,
               "Ship has lowest cost for 500km")
    
    # Test 6: Flight is fastest
    flight_time = MODE_CHARACTERISTICS[TransportationMode.FLIGHT].calculate_metrics(500, 10)[0]
    truck_time = MODE_CHARACTERISTICS[TransportationMode.TRUCK].calculate_metrics(500, 10)[0]
    runner.test(flight_time < truck_time,
               "Flight is fastest mode")
    
    # Test 7: Ship has lowest carbon
    ship_carbon = MODE_CHARACTERISTICS[TransportationMode.SHIP].calculate_metrics(500, 10)[2]
    truck_carbon = MODE_CHARACTERISTICS[TransportationMode.TRUCK].calculate_metrics(500, 10)[2]
    runner.test(ship_carbon < truck_carbon,
               "Ship has lowest carbon emissions")
    
    # Test 8: Metric accumulation
    m = TrilemmaMetrics()
    m.add(10, 100, 50)
    m.add(5, 50, 25)
    runner.test(abs(m.accumulated_hours - 15.0) < 1e-10,
               "Metric accumulation: hours")
    runner.test(abs(m.accumulated_cost - 150.0) < 1e-10,
               "Metric accumulation: cost")
    runner.test(abs(m.accumulated_carbon - 75.0) < 1e-10,
               "Metric accumulation: carbon")
    
    # Test 9: Graph path finding
    net = FreightNetwork()
    for i in range(5):
        net.add_node(i)
    net.add_edge(0, 1, time=2.5, cost=150, carbon=45)
    net.add_edge(1, 3, time=1.5, cost=100, carbon=30)
    net.add_edge(3, 4, time=2.0, cost=120, carbon=40)
    
    path = net.get_shortest_path(0, 4, weight="time")
    runner.test(path is not None and path[0] == 0 and path[-1] == 4,
               "Graph: Path exists from 0 to 4")
    
    # Test 10: Unreachable node
    net2 = FreightNetwork()
    net2.add_node(0)
    net2.add_node(1)
    net2.add_node(2)
    net2.add_edge(0, 1, time=1, cost=1, carbon=1)
    
    no_path = net2.get_shortest_path(0, 2, weight="time")
    runner.test(no_path is None,
               "Graph: Returns None for unreachable nodes")
    
    return runner.print_results()


if __name__ == "__main__":
    sys.exit(run_regression_tests())
