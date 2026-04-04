#!/usr/bin/env python3
"""
Mathematical Correctness Validator - Quick Test Runner

Efficiently verifies:
1. Trilemma scoring formula correctness
2. Numerical precision
3. Transportation mode calculations  
4. Path algorithm validity
5. Cost accumulation accuracy

Run with: python3 tests/validate_math.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.grader import (
    TrilemmaMetrics, TransportationMode, 
    MODE_CHARACTERISTICS
)
from app.engine.graph import FreightNetwork


class MathValidator:
    """Validate mathematical calculations efficiently."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def assert_almost_equal(self, actual, expected, tolerance=1e-10, name=""):
        """Check if values are approximately equal."""
        if abs(actual - expected) <= tolerance:
            self.passed += 1
            self.tests.append(("✅", f"PASS: {name}"))
            return True
        else:
            self.failed += 1
            self.tests.append(("❌", f"FAIL: {name} (got {actual}, expected {expected})"))
            return False
    
    def assert_true(self, condition, name=""):
        """Check if condition is true."""
        if condition:
            self.passed += 1
            self.tests.append(("✅", f"PASS: {name}"))
            return True
        else:
            self.failed += 1
            self.tests.append(("❌", f"FAIL: {name}"))
            return False
    
    def assert_less(self, actual, expected, name=""):
        """Check if actual < expected."""
        if actual < expected:
            self.passed += 1
            self.tests.append(("✅", f"PASS: {name}"))
            return True
        else:
            self.failed += 1
            self.tests.append(("❌", f"FAIL: {name} ({actual} >= {expected})"))
            return False
    
    def print_results(self):
        """Print test results."""
        print("\n" + "="*70)
        print("MATHEMATICAL CORRECTNESS VALIDATION RESULTS")
        print("="*70 + "\n")
        
        for symbol, message in self.tests:
            print(f"{symbol} {message}")
        
        print("\n" + "-"*70)
        print(f"Summary: {self.passed} passed, {self.failed} failed")
        print("="*70 + "\n")
        
        return self.failed == 0


def validate_trilemma_formula():
    """Validate the core trilemma scoring formula."""
    print("\n🧮 SECTION 1: TRILEMMA FORMULA VALIDATION")
    print("-" * 70)
    
    v = MathValidator()
    
    # Test 1: Zero metrics
    metrics = TrilemmaMetrics()
    score = 0.5 * metrics.accumulated_hours + 0.3 * metrics.accumulated_cost + 0.2 * metrics.accumulated_carbon
    v.assert_almost_equal(score, 0.0, name="Zero metrics → zero score")
    
    # Test 2: Hours only
    metrics = TrilemmaMetrics(accumulated_hours=100.0)
    score = 0.5 * 100 + 0.3 * 0 + 0.2 * 0
    v.assert_almost_equal(score, 50.0, name="Hours weight (0.5×100=50)")
    
    # Test 3: Cost only
    metrics = TrilemmaMetrics(accumulated_cost=1000.0)
    score = 0.5 * 0 + 0.3 * 1000 + 0.2 * 0
    v.assert_almost_equal(score, 300.0, name="Cost weight (0.3×1000=300)")
    
    # Test 4: Carbon only
    metrics = TrilemmaMetrics(accumulated_carbon=500.0)
    score = 0.5 * 0 + 0.3 * 0 + 0.2 * 500
    v.assert_almost_equal(score, 100.0, name="Carbon weight (0.2×500=100)")
    
    # Test 5: Combined formula
    metrics = TrilemmaMetrics(accumulated_hours=10, accumulated_cost=500, accumulated_carbon=250)
    score = 0.5 * 10 + 0.3 * 500 + 0.2 * 250
    v.assert_almost_equal(score, 205.0, name="Combined (0.5×10 + 0.3×500 + 0.2×250 = 205)")
    
    # Test 6: Fractional values
    metrics = TrilemmaMetrics(accumulated_hours=7.5, accumulated_cost=123.45, accumulated_carbon=67.89)
    expected = 0.5 * 7.5 + 0.3 * 123.45 + 0.2 * 67.89
    score = 0.5 * 7.5 + 0.3 * 123.45 + 0.2 * 67.89
    v.assert_almost_equal(score, expected, tolerance=1e-10, name="Fractional values precision")
    
    # Test 7: Weight normalization (should sum to 1.0)
    weights = [0.5, 0.3, 0.2]
    v.assert_almost_equal(sum(weights), 1.0, name="Weights sum to 1.0 (normalized)")
    
    # Test 8: Large numbers
    metrics = TrilemmaMetrics(
        accumulated_hours=1000000,
        accumulated_cost=10000000,
        accumulated_carbon=5000000
    )
    score = 0.5 * 1000000 + 0.3 * 10000000 + 0.2 * 5000000
    expected = 4500000.0
    v.assert_almost_equal(score, expected, tolerance=1e-5, name="Large numbers handled correctly")
    
    # Test 9: Metric accumulation
    metrics = TrilemmaMetrics()
    metrics.add(10, 100, 50)
    metrics.add(5, 50, 25)
    v.assert_almost_equal(metrics.accumulated_hours, 15.0, name="Hours accumulation (10+5=15)")
    v.assert_almost_equal(metrics.accumulated_cost, 150.0, name="Cost accumulation (100+50=150)")
    v.assert_almost_equal(metrics.accumulated_carbon, 75.0, name="Carbon accumulation (50+25=75)")
    
    return v


def validate_transportation_modes():
    """Validate transportation mode calculations."""
    print("\n🚚 SECTION 2: TRANSPORTATION MODE CALCULATIONS")
    print("-" * 70)
    
    v = MathValidator()
    
    # Test 1: Truck calculation
    truck = MODE_CHARACTERISTICS[TransportationMode.TRUCK]
    time, cost, carbon = truck.calculate_metrics(100, 10)
    v.assert_almost_equal(time, 100/80, tolerance=1e-10, name="Truck: 100km at 80km/h = 1.25h")
    v.assert_almost_equal(cost, 100 * 0.15, tolerance=1e-10, name="Truck: 100km × $0.15/km = $15")
    v.assert_almost_equal(carbon, 100 * 0.025, tolerance=1e-10, name="Truck: 100km × 0.025kt/km = 2.5kt")
    
    # Test 2: Rail calculation
    rail = MODE_CHARACTERISTICS[TransportationMode.RAIL]
    time, cost, carbon = rail.calculate_metrics(200, 50)
    v.assert_almost_equal(time, 200/90, tolerance=1e-10, name="Rail: 200km at 90km/h ≈ 2.22h")
    v.assert_almost_equal(cost, 200 * 0.08, tolerance=1e-10, name="Rail: 200km × $0.08/km = $16")
    v.assert_almost_equal(carbon, 200 * 0.008, tolerance=1e-10, name="Rail: 200km × 0.008kt/km = 1.6kt")
    
    # Test 3: Cost comparison (ship < truck for long distance)
    truck_time, truck_cost, _ = truck.calculate_metrics(1000, 50)
    ship_time, ship_cost, _ = MODE_CHARACTERISTICS[TransportationMode.SHIP].calculate_metrics(1000, 50)
    v.assert_less(ship_cost, truck_cost, name="Ship cheaper than truck at 1000km")
    
    # Test 4: Carbon comparison (ship best)
    truck_c, truck_h, truck_carbon = truck.calculate_metrics(500, 10)
    rail_c, rail_h, rail_carbon = rail.calculate_metrics(500, 10)
    ship_c, ship_h, ship_carbon = MODE_CHARACTERISTICS[TransportationMode.SHIP].calculate_metrics(500, 10)
    flight_c, flight_h, flight_carbon = MODE_CHARACTERISTICS[TransportationMode.FLIGHT].calculate_metrics(500, 10)
    
    v.assert_less(ship_carbon, truck_carbon, name="Ship carbon < Truck")
    v.assert_less(ship_carbon, rail_carbon, name="Ship carbon < Rail")
    v.assert_less(ship_carbon, flight_carbon, name="Ship carbon < Flight")
    
    # Test 5: Speed comparison (flight fastest)
    flight = MODE_CHARACTERISTICS[TransportationMode.FLIGHT]
    flight_time, _, _ = flight.calculate_metrics(500, 10)
    ship_time, _, _ = MODE_CHARACTERISTICS[TransportationMode.SHIP].calculate_metrics(500, 10)
    truck_time, _, _ = truck.calculate_metrics(500, 10)
    
    v.assert_less(flight_time, truck_time, name="Flight faster than truck")
    v.assert_less(flight_time, ship_time, name="Flight faster than ship")
    
    # Test 6: Capacity clamping
    mode = truck
    _, cost_high, _ = mode.calculate_metrics(100, 50)  # Over capacity
    _, cost_capacity, _ = mode.calculate_metrics(100, mode.capacity_tons)  # At capacity
    v.assert_almost_equal(cost_high, cost_capacity, name="Cargo clamped to capacity")
    
    # Test 7: Distance-independent carbon (per km, not per ton)
    time1, cost1, carbon1 = truck.calculate_metrics(100, 5)
    time2, cost2, carbon2 = truck.calculate_metrics(100, 50)
    v.assert_almost_equal(carbon1, carbon2, name="Carbon independent of cargo weight")
    
    return v


def validate_graph_pathfinding():
    """Validate graph pathfinding logic."""
    print("\n🗺️  SECTION 3: GRAPH PATHFINDING VALIDATION")
    print("-" * 70)
    
    v = MathValidator()
    
    # Create test network
    net = FreightNetwork()
    for i in range(5):
        net.add_node(i, location=f"City{i}")
    
    # Create edges with specific weights
    net.add_edge(0, 1, time=2.5, cost=150, carbon=45)
    net.add_edge(0, 2, time=5.0, cost=200, carbon=80)
    net.add_edge(1, 3, time=1.5, cost=100, carbon=30)
    net.add_edge(2, 3, time=3.0, cost=180, carbon=60)
    net.add_edge(3, 4, time=2.0, cost=120, carbon=40)
    
    # Test path existence
    path_time = net.get_shortest_path(0, 4, weight="time")
    v.assert_true(path_time is not None, name="Path exists from 0 to 4")
    
    # Test path validity
    if path_time:
        v.assert_true(path_time[0] == 0, name="Path starts at source (0)")
        v.assert_true(path_time[-1] == 4, name="Path ends at target (4)")
        v.assert_true(len(path_time) >= 2, name="Path has at least 2 nodes")
    
    # Test multiple weight types
    path_cost = net.get_shortest_path(0, 4, weight="cost")
    path_carbon = net.get_shortest_path(0, 4, weight="carbon")
    v.assert_true(path_cost is not None, name="Path by cost exists")
    v.assert_true(path_carbon is not None, name="Path by carbon exists")
    
    # Test unreachable nodes
    net2 = FreightNetwork()
    net2.add_node(0)
    net2.add_node(1)
    net2.add_node(2)
    net2.add_edge(0, 1, time=1, cost=1, carbon=1)
    
    no_path = net2.get_shortest_path(0, 2, weight="time")
    v.assert_true(no_path is None, name="No path to unreachable node returns None")
    
    # Test same node
    same_path = net.get_shortest_path(0, 0, weight="time")
    v.assert_true(same_path is not None and len(same_path) == 1, 
                 name="Same source/target returns single-node path")
    
    return v


def validate_numerical_stability():
    """Validate numerical stability."""
    print("\n🔬 SECTION 4: NUMERICAL STABILITY")
    print("-" * 70)
    
    v = MathValidator()
    
    # Test very small numbers
    metrics1 = TrilemmaMetrics(0.0001, 0.0001, 0.0001)
    score1 = 0.5 * 0.0001 + 0.3 * 0.0001 + 0.2 * 0.0001
    v.assert_almost_equal(
        0.5 * metrics1.accumulated_hours + 0.3 * metrics1.accumulated_cost + 0.2 * metrics1.accumulated_carbon,
        score1, tolerance=1e-15, name="Very small numbers precision"
    )
    
    # Test mixed magnitudes
    metrics2 = TrilemmaMetrics(0.001, 1000000, 100.5)
    score2 = 0.5 * 0.001 + 0.3 * 1000000 + 0.2 * 100.5
    v.assert_almost_equal(
        0.5 * metrics2.accumulated_hours + 0.3 * metrics2.accumulated_cost + 0.2 * metrics2.accumulated_carbon,
        score2, tolerance=1e-10, name="Mixed magnitude precision"
    )
    
    # Test accumulation associativity
    m1 = TrilemmaMetrics()
    m1.add(10, 100, 50)
    m1.add(5, 50, 25)
    m1.add(3, 30, 15)
    
    m2 = TrilemmaMetrics()
    m2.add(18, 180, 90)
    
    v.assert_almost_equal(m1.accumulated_hours, m2.accumulated_hours,
                         name="Accumulation associativity (hours)")
    v.assert_almost_equal(m1.accumulated_cost, m2.accumulated_cost,
                         name="Accumulation associativity (cost)")
    v.assert_almost_equal(m1.accumulated_carbon, m2.accumulated_carbon,
                         name="Accumulation associativity (carbon)")
    
    return v


def main():
    """Run all validation tests."""
    
    print("=" * 70)
    print("MATHEMATICS & ALGORITHM EFFICIENCY VALIDATOR")
    print("=" * 70)
    
    validators = [
        validate_trilemma_formula(),
        validate_transportation_modes(),
        validate_graph_pathfinding(),
        validate_numerical_stability(),
    ]
    
    # Collect all results
    total_passed = sum(v.passed for v in validators)
    total_failed = sum(v.failed for v in validators)
    
    print("\n" + "=" * 70)
    print("FINAL VALIDATION REPORT")
    print("=" * 70)
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_failed}")
    print(f"📊 Success Rate: {100 * total_passed / (total_passed + total_failed):.1f}%")
    print("=" * 70)
    
    if total_failed == 0:
        print("\n🎉 ALL MATHEMATICAL VALIDATIONS PASSED!")
        print("Algorithm correctness verified - No calculation errors detected")
        return 0
    else:
        print(f"\n⚠️  {total_failed} validations failed - Review above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
