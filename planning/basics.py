import argparse
import os
import sys
from typing import Any, Dict, List, Optional

import pydot

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common.basics import DesignGoal
from common.utils import setup_logging


class TreeNode:
    """Represents a node in a tree structure, where each node holds a DesignGoal."""

    def __init__(self, design_goal: DesignGoal):
        self.design_goal = design_goal  # Core DesignGoal data
        self.parent: Optional[TreeNode] = None  # Parent node
        self.children: List[TreeNode] = []  # Child nodes

        # Automatically decompose if parts exist
        if "decomposition" in self.design_goal.extra:
            self._decompose()

    def _decompose(self):
        """Create child nodes from decomposition parts."""
        parts = self.design_goal.extra["decomposition"].get("parts", [])
        for part_data in parts:
            # Create a new DesignGoal for the part
            part_dg = DesignGoal(
                text=part_data["part_name"],
                extra={
                    "dimensions": part_data["dimensions"],
                    "construction_methods": part_data["construction_methods"],
                    "cad_operations": part_data["cad_operations"],
                    "considerations": part_data["considerations"],
                },
            )
            child_node = TreeNode(part_dg)
            self.add_child(child_node)

    def add_child(self, child_node):
        """Add a child node to the current node."""
        child_node.parent = self
        self.children.append(child_node)

    def remove_child(self, child_node):
        """Remove a child node from the current node."""
        if child_node in self.children:
            child_node.parent = None
            self.children.remove(child_node)

    def __repr__(self, level=0):
        """Generate a string representation of the tree."""
        ret = "\t" * level + repr(self.design_goal) + "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

    def to_dot(self) -> str:
        """Generate a DOT graph representing the tree structure."""
        dot_lines = ["digraph G {"]

        # Add nodes for all parts
        node_ids = {}
        stack = [(self, None)]  # (node, parent_node_id)
        idx = 0

        while stack:
            node, parent_id = stack.pop()
            node_id = f"Node{idx}"
            node_ids[node] = node_id
            dot_lines.append(f'{node_id} [label="{node.design_goal.text}"];')

            if parent_id:
                dot_lines.append(f"{parent_id} -> {node_id};")

            for child in reversed(node.children):
                stack.append((child, node_id))
            idx += 1

        dot_lines.append("}")
        return "\n".join(dot_lines)

    def show(self, format: str = "png", filename: str = "design_plan"):
        """Render the DOT graph as an image using pydot.

        Args:
            format (str): The image format (e.g., "png", "svg").
            filename (str): The name of the output file (without extension).
        """
        dot_str = self.to_dot()
        try:
            # Parse the DOT string into a pydot graph
            graph = pydot.graph_from_dot_data(dot_str)[0]
            # Save the graph as an image
            graph.write(filename + "." + format, format=format)
            print(f"Graph saved as {filename}.{format}")
        except Exception as e:
            print(f"Failed to render graph: {e}")


# Example usage:
if __name__ == "__main__":
    setup_logging()

    parser = argparse.ArgumentParser(description="DOT Language Planner")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts.yaml", help="Path to the prompts YAML file"
    )
    parser.add_argument(
        "design_goal_json",
        type=str,
        help="The design goal in JSON format",
    )
    args = parser.parse_args()
    # Load DesignGoal from JSON
    with open(args.design_goal_json, "r") as f:
        design_goal = DesignGoal.from_json(f.read())

    # Create the tree structure
    root = TreeNode(design_goal)

    # Print the tree structure
    print(root)

    # Generate and save the DOT graph
    root.show(format="png", filename="design_plan")
