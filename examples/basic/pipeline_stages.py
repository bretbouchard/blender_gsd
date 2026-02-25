"""
Example: Pipeline Stages

Demonstrates:
- The 5-stage Universal Stage Pipeline
- Stage-specific operations
- Stage chaining

Usage:
    blender --python examples/basic/pipeline_stages.py
"""

from __future__ import annotations


def main():
    """Demonstrate the 5-stage pipeline."""
    print("Pipeline Stages Example")
    print("=" * 40)

    from lib.pipeline import StagePipeline, StageConfig

    # Define stage configurations
    stages = {
        "normalize": StageConfig(
            name="normalize",
            description="Parameter canonicalization and validation",
            enabled=True,
        ),
        "primary": StageConfig(
            name="primary",
            description="Base geometry generation",
            enabled=True,
        ),
        "secondary": StageConfig(
            name="secondary",
            description="Modifications and secondary elements",
            enabled=True,
        ),
        "detail": StageConfig(
            name="detail",
            description="Surface effects and fine details",
            enabled=True,
        ),
        "output": StageConfig(
            name="output",
            description="Cleanup and export preparation",
            enabled=True,
        ),
    }

    # Create pipeline
    pipeline = StagePipeline(stages=stages)

    print("\n5-Stage Pipeline:")
    print("-" * 40)

    stage_descriptions = [
        ("NORMALIZE", "Validate parameters, set defaults, resolve references"),
        ("PRIMARY", "Generate base geometry (cube, cylinder, custom mesh)"),
        ("SECONDARY", "Add modifications (cutouts, bevels, boolean ops)"),
        ("DETAIL", "Apply surface effects (knurling, text, indicators)"),
        ("OUTPUT", "Cleanup attributes, prepare for export"),
    ]

    for i, (stage, desc) in enumerate(stage_descriptions, 1):
        print(f"\n  Stage {i}: {stage}")
        print(f"    {desc}")

    # Simulate pipeline execution
    print("\n" + "-" * 40)
    print("Simulating Pipeline Execution:")
    print("-" * 40)

    test_params = {
        "diameter": 0.025,
        "height": 0.030,
        "style": "neve_1073",
    }

    print(f"\nInput parameters: {test_params}")

    # Stage 1: Normalize
    normalized = pipeline.normalize(test_params)
    print(f"\n1. NORMALIZE: {normalized}")

    # Stage 2: Primary
    primary_result = {"geometry": "cylinder", "vertices": 32}
    print(f"2. PRIMARY: Generated {primary_result['geometry']} ({primary_result['vertices']} vertices)")

    # Stage 3: Secondary
    secondary_result = {"cutouts": 1, "bevel": True}
    print(f"3. SECONDARY: Added {secondary_result['cutouts']} cutout(s), bevel={secondary_result['bevel']}")

    # Stage 4: Detail
    detail_result = {"knurling": "diamond", "indicator": "pointer"}
    print(f"4. DETAIL: {detail_result['knurling']} knurling, {detail_result['indicator']} indicator")

    # Stage 5: Output
    output_result = {"cleanup": True, "export_ready": True}
    print(f"5. OUTPUT: Cleanup={output_result['cleanup']}, Export ready={output_result['export_ready']}")

    print("\n✓ Pipeline complete!")


if __name__ == "__main__":
    main()
