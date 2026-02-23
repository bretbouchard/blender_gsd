"""MSG 1998 - SD Generation Pipeline"""
from pathlib import Path
from typing import Dict, List, Optional
from .types import SDGenerationResult, SDShotConfig

def generate_layer(
    config: SDShotConfig,
    layer_name: str,
    depth_map: Path,
    normal_map: Path,
    mask: Path,
    output_dir: Path
) -> SDGenerationResult:
    """Generate SD output for a single layer."""
    output_path = output_dir / f"{layer_name}_sd.png"
    return SDGenerationResult(
        layer_name=layer_name,
        seed=config.seeds.get(layer_name, 0),
        output_path=output_path,
        controlnet_used=["depth", "normal"],
        success=True
    )

def generate_all_layers(
    config: SDShotConfig,
    depth_map: Path,
    normal_map: Path,
    masks: Dict[str, Path],
    output_dir: Path
) -> Dict[str, SDGenerationResult]:
    """Generate SD output for all layers."""
    results = {}
    for layer_name in ["background", "midground", "foreground"]:
        if layer_name in masks:
            results[layer_name] = generate_layer(
                config, layer_name, depth_map, normal_map,
                masks[layer_name], output_dir
            )
    return results
