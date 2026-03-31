"""
Graph structures for representing the freight network.

Implements graph operations for the transportation network topology.
"""

from typing import List, Dict, Any, Optional, Tuple
import networkx as nx

from app.utils.logger import logger


class FreightNetwork:
    """
    Represents the transportation network as a directed graph.
    
    Nodes represent locations, edges represent transportation routes.
    """

    def __init__(self):
        """Initialize the freight network."""
        self.graph = nx.DiGraph()
        logger.info("FreightNetwork initialized")

    def add_node(self, node_id: int, **attributes) -> None:
        """
        Add a node to the network.
        
        Args:
            node_id: Unique node identifier
            **attributes: Node attributes (location, capacity, etc.)
        """
        self.graph.add_node(node_id, **attributes)
        logger.debug(f"Node {node_id} added to network")

    def add_edge(self, source: int, target: int, **attributes) -> None:
        """
        Add an edge (route) to the network.
        
        Args:
            source: Source node
            target: Target node
            **attributes: Edge attributes (distance, cost, time, etc.)
        """
        self.graph.add_edge(source, target, **attributes)
        logger.debug(f"Edge {source}->{target} added to network")

    def get_shortest_path(self, source: int, target: int, weight: str = "distance") -> Optional[List[int]]:
        """
        Get shortest path between two nodes.
        
        Args:
            source: Source node
            target: Target node
            weight: Weight attribute to minimize
            
        Returns:
            List of nodes in shortest path, or None if no path exists
        """
        try:
            path = nx.shortest_path(self.graph, source, target, weight=weight)
            return path
        except nx.NetworkXNoPath:
            logger.warning(f"No path found between {source} and {target}")
            return None

    def get_neighbors(self, node_id: int) -> List[int]:
        """
        Get neighboring nodes.
        
        Args:
            node_id: Node identifier
            
        Returns:
            List of neighboring node IDs
        """
        return list(self.graph.neighbors(node_id))

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert graph to dictionary representation.
        
        Returns:
            Dictionary with nodes and edges
        """
        return {
            "nodes": list(self.graph.nodes(data=True)),
            "edges": list(self.graph.edges(data=True)),
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Load graph from dictionary representation.
        
        Args:
            data: Dictionary with nodes and edges
        """
        self.graph.clear()
        
        for node_id, attrs in data.get("nodes", []):
            self.add_node(node_id, **attrs)
        
        for source, target, attrs in data.get("edges", []):
            self.add_edge(source, target, **attrs)
        
        logger.info("Graph loaded from dictionary")
