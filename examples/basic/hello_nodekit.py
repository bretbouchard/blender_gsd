"""
Example: Hello NodeKit

Demonstrates:
- Creating a node group programmatically
- Adding and connecting nodes
- Defining inputs and outputs

Usage:
    blender --python examples/basic/hello_nodekit.py
"""

from __future__ import annotations


def main():
    """Create a simple cube with material node group."""
    print("Hello NodeKit Example")
    print("=" * 40)

    # Example using mock for demonstration outside Blender
    try:
        import bpy
        HAS_BLENDER = True
    except ImportError:
        HAS_BLENDER = False
        print("Running outside Blender - using mock demonstration")

    if HAS_BLENDER:
        from lib.nodekit import NodeGraph, InputSocket

        # Create a node group for a simple material
        graph = NodeGraph("ExampleMaterial")

        # Add input sockets
        graph.add_input("base_color", "RGBA", default=(0.8, 0.2, 0.2, 1.0))
        graph.add_input("roughness", "VALUE", default=0.5)
        graph.add_input("metallic", "VALUE", default=0.0)

        # Add nodes
        bsdf = graph.add_node("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Base Color"].default_value = (0.8, 0.2, 0.2, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.5

        output = graph.add_node("ShaderNodeOutputMaterial")

        # Connect nodes
        graph.link(bsdf.outputs["BSDF"], output.inputs["Surface"])

        # Define output
        graph.output(surface="BSDF")

        print(f"Created node group: {graph.name}")
        print("  - 1 BSDF node")
        print("  - 1 Output node")
        print("  - 3 inputs (base_color, roughness, metallic)")

    else:
        # Mock demonstration
        print("\nMock Node Group Structure:")
        print("  NodeGroup: ExampleMaterial")
        print("  ├── Inputs:")
        print("  │   ├── base_color (RGBA) = (0.8, 0.2, 0.2, 1.0)")
        print("  │   ├── roughness (VALUE) = 0.5")
        print("  │   └── metallic (VALUE) = 0.0")
        print("  ├── Nodes:")
        print("  │   ├── PrincipledBSDF")
        print("  │   └── MaterialOutput")
        print("  └── Connections:")
        print("      └── BSDF → Surface")

    print("\n✓ Example complete!")


if __name__ == "__main__":
    main()
