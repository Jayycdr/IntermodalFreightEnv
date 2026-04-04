#!/usr/bin/env python3
"""
Test script for core systems: graph and environment.

Demonstrates:
- Network setup with trilemma attributes (time, cost, carbon)
- Cargo creation, splitting, and routing
- State machine and trilemma tracking
- Disruption engine
"""

from app.engine.graph import FreightNetwork, EdgeData
from app.engine.core_env import FreightEnvironment, EnvironmentConfig
from app.utils.logger import logger


def test_graph():
    """Test graph structure and operations."""
    logger.info("=" * 60)
    logger.info("TESTING GRAPH STRUCTURE")
    logger.info("=" * 60)
    
    # Create network
    net = FreightNetwork()
    
    # Add nodes
    for i in range(5):
        net.add_node(i, location=f"City{i}", capacity=1000)
    
    # Add edges with trilemma attributes
    edges = [
        (0, 1, {"time": 2.5, "cost": 150.0, "carbon": 45.0}),
        (0, 2, {"time": 5.0, "cost": 200.0, "carbon": 80.0}),
        (1, 3, {"time": 1.5, "cost": 100.0, "carbon": 30.0}),
        (2, 3, {"time": 3.0, "cost": 180.0, "carbon": 60.0}),
        (3, 4, {"time": 2.0, "cost": 120.0, "carbon": 40.0}),
    ]
    
    for source, target, attrs in edges:
        net.add_edge(source, target, **attrs)
    
    logger.info(f"Network created with {len(net.get_all_nodes())} nodes and {len(net.get_all_edges())} edges")
    
    # Test shortest path by time
    path_time = net.get_shortest_path(0, 4, weight="time")
    logger.info(f"Shortest path (by time) 0->4: {path_time}")
    
    # Test shortest path by cost
    path_cost = net.get_shortest_path(0, 4, weight="cost")
    logger.info(f"Shortest path (by cost) 0->4: {path_cost}")
    
    # Test shortest path by carbon
    path_carbon = net.get_shortest_path(0, 4, weight="carbon")
    logger.info(f"Shortest path (by carbon) 0->4: {path_carbon}")
    
    # Test disruption engine
    logger.info("\nTesting disruption engine...")
    net.disable_node(2)
    net.disable_edge(1, 3)
    
    logger.info(f"Available nodes: {net.get_available_nodes()}")
    logger.info(f"Available edges: {len(net.get_available_edges())}")
    
    # Try path with disruptions
    path_disrupted = net.get_shortest_path(0, 4, weight="time")
    logger.info(f"Path 0->4 with disruptions: {path_disrupted}")


def test_environment():
    """Test environment state machine and cargo management."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING CORE ENVIRONMENT")
    logger.info("=" * 60)
    
    # Create environment
    config = EnvironmentConfig(
        num_nodes=6,
        max_steps=10,
        disruption_probability=0.1,
        seed=42,
    )
    env = FreightEnvironment(config)
    
    # Setup network
    network_config = {
        "nodes": [
            {"id": 0, "location": "Warehouse"},
            {"id": 1, "location": "Port1"},
            {"id": 2, "location": "Port2"},
            {"id": 3, "location": "Rail Station"},
            {"id": 4, "location": "Terminal"},
            {"id": 5, "location": "Destination"},
        ],
        "edges": [
            {"source": 0, "target": 1, "time": 2.0, "cost": 100., "carbon": 30.},
            {"source": 0, "target": 3, "time": 1.5, "cost": 80., "carbon": 20.},
            {"source": 1, "target": 4, "time": 3.0, "cost": 150., "carbon": 50.},
            {"source": 3, "target": 4, "time": 2.5, "cost": 120., "carbon": 40.},
            {"source": 4, "target": 5, "time": 1.0, "cost": 50., "carbon": 15.},
            {"source": 2, "target": 4, "time": 4.0, "cost": 180., "carbon": 60.},
        ],
    }
    
    env.setup_network(network_config)
    logger.info(f"Network setup complete")
    
    # Reset environment (applies disruptions)
    state = env.reset()
    logger.info(f"Environment reset")
    logger.info(f"Disabled nodes: {env.network.disabled_nodes}")
    logger.info(f"Disabled edges: {env.network.disabled_edges}")
    
    # Test cargo creation
    logger.info("\nCreating cargos...")
    cargo1 = env.add_cargo(origin=0, destination=5, quantity=100., weight=5000., priority=2)
    cargo2 = env.add_cargo(origin=0, destination=5, quantity=50., weight=2500., priority=3)
    
    logger.info(f"Created cargo {cargo1.cargo_id} and {cargo2.cargo_id}")
    
    # Test cargo splitting
    logger.info("\nSplitting cargo...")
    splits = env.split_cargo(cargo2.cargo_id, [20., 30.])
    logger.info(f"Cargo {cargo2.cargo_id} split into {len(splits)} parts")
    
    # Find paths and route cargos
    logger.info("\nRouting cargos...")
    
    # Route main cargo
    path1 = env.network.get_shortest_path(0, 5, weight="time")
    if path1:
        env.route_cargo(cargo1.cargo_id, path1)
        logger.info(f"Cargo {cargo1.cargo_id} routed on path: {path1}")
    
    # Route split cargos
    for split in splits:
        path = env.network.get_shortest_path(0, 5, weight="cost")
        if path:
            env.route_cargo(split.cargo_id, path)
            logger.info(f"Cargo {split.cargo_id} routed on path: {path}")
    
    # Run simulation steps
    logger.info("\nRunning simulation steps...")
    for step in range(3):
        state, reward, done, info = env.step({})
        logger.info(f"Step {step + 1}: active={info['active_cargos']}, "
                   f"completed={info['completed_cargos']}, "
                   f"trilemma={info['trilemma']}")
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("FINAL STATE")
    logger.info("=" * 60)
    logger.info(f"Total completed cargos: {len(env.completed_cargos)}")
    logger.info(f"Total active cargos: {len(env.active_cargos)}")
    logger.info(f"Final trilemma: {env.get_trilemma().to_dict()}")


def test_trilemma_optimization():
    """Test different pathfinding strategies based on trilemma."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING TRILEMMA OPTIMIZATION")
    logger.info("=" * 60)
    
    # Create network
    net = FreightNetwork()
    nodes = [
        (0, {"name": "Start"}),
        (1, {"name": "Route1"}),
        (2, {"name": "Route2"}),
        (3, {"name": "End"}),
    ]
    
    edges = [
        (0, 1, {"time": 10., "cost": 50., "carbon": 100.}),  # Fast, cheap, high carbon
        (0, 2, {"time": 5., "cost": 200., "carbon": 20.}),   # Slow, expensive, low carbon
        (1, 3, {"time": 5., "cost": 100., "carbon": 50.}),
        (2, 3, {"time": 10., "cost": 100., "carbon": 30.}),
    ]
    
    for node_id, attrs in nodes:
        net.add_node(node_id, **attrs)
    
    for source, target, attrs in edges:
        net.add_edge(source, target, **attrs)
    
    # Find paths optimizing for different objectives
    path_time = net.get_shortest_path(0, 3, weight="time")
    path_cost = net.get_shortest_path(0, 3, weight="cost")
    path_carbon = net.get_shortest_path(0, 3, weight="carbon")
    
    logger.info(f"Fastest path (0->3): {path_time}")
    logger.info(f"Cheapest path (0->3): {path_cost}")
    logger.info(f"Greenest path (0->3): {path_carbon}")
    
    # Show the trilemma tradeoff
    for weight, path in [("time", path_time), ("cost", path_cost), ("carbon", path_carbon)]:
        total_time = 0
        total_cost = 0
        total_carbon = 0
        
        for i in range(len(path) - 1):
            edge = net.get_edge(path[i], path[i+1])
            if edge:
                total_time += edge.time
                total_cost += edge.cost
                total_carbon += edge.carbon
        
        logger.info(f"Path optimized for {weight:6s}: "
                   f"time={total_time:6.1f}h, cost=${total_cost:7.1f}, carbon={total_carbon:6.1f}kg")


if __name__ == "__main__":
    test_graph()
    test_environment()
    test_trilemma_optimization()
    
    logger.info("\n" + "=" * 60)
    logger.info("ALL TESTS COMPLETED")
    logger.info("=" * 60)
