# Research Summary

## Domain Overview

This research covers Blender mechanical tile platforms systems with physics-simulated arms that fold under the platform and tiles, that are placed and precise coordinates and The arms always reach targets, and are to from physics simulation constraints ensures natural movement while still guaranteeing targets are always reached.

## Key Findings

**High confidence: High**

1. **Architecture**: Modular design with clear component boundaries
   - Physics simulation (separate module or RR system)
   - Geometry nodes (for procedural placement)
   - Armature/Rigging system (separate module)
   - Tile geometry/mesh system (separate module)
   - Animation system (separate module)
   - Export pipeline (separate module,   - Testing framework (separate module)
   - Visual polish tools (node group polishers, procedural pathfinding)

   - Kitbash integration (separate module,   - Configuration management (separate module)

2. **Critical Pitfall**: Physics simulation determinism - parameters need careful tuning, avoid unnatural movement
3. **Another pitfall**: Export format data loss - validate early and format-specific issues
4. **Integration challenges**: Unity/Unreal axis conventions, glTF material compatibility, USD complexity

5. **Success Criteria**:
   - Platform extends smoothly with natural arm motion
   - Arms reach targets correctly
   - Tiles placed at correct coordinates
   - Physics simulation remains stable
   - Retraction animation feels satisfying
   - Visual style is maintained (sleek brutalist)
   - FBX/glTF exports work correctly
   - Animation renders at production quality

## Technology Stack
- Blender 4.x with Python 3.11+ scripting
- Geometry Nodes 4.x for procedural tile placement
- Armature System 4.x for arm rigging
            Physics Engine 4.x for rigid body simulation
            NumPy 1.26+ for math utilities
            BlenderProc 1.0+ for procedural operations (alternative: scripting)
- Visual reference: Kitbash 3D sets (see /Volumes/Storage/3d/Kitbash/Vitaly sets)

- Tutorial videos on Blender geometry nodes, rigging, physics
- Official documentation on Blender API reference

- Blogs/forums on Blender community (BlenderArtists, Stackoverflow)

- GitHub issues (geometry nodes performance, physics stability)

## Installation

```bash
# Core
pip install bpy numpy

# Supporting
pip install pytest pytest-cov

# Dev dependencies
pip install -r requirements.txt  # linting/formatting

```

## Sources
- Context7 for MCP: https://blenderartists.org/manual/animation/physics/
  - Blender docs: https://docs.blender.org/manual/animation/physics.html
  - Context7: https://docs.blender.org/manual/geometry_nodes.html
  - Context7: For Blender rigging best practices: https://blenderartists.org/tutorials/rigging/intro.html
  - YouTube: "Procedural Animation in Blender" - search for procedural animation tutorials
  - BlenderArtists thread on geometry nodes animation: https://blenderartists.org/t/geometry-nodes-animation-t/
      "Working with the curve nodes in Blender is very tedious"
      "Curve nodes are overkill"

- Blender docs: Good starting point,- BlenderArtists: sometimes too tutorial-focused (lacks depth)
  - Community forums: Can feel overwhelming
  - Official docs: comprehensive but sometimes dense

- Kitbash workflow: Learning curve steeper than scripting
  - Start simple, experiment with ready-made kitbash assets
  - Use placeholder meshes for manually
  - Keep armature bone counts low (3-4 for early prototypes)

- Performance: Need to profile at scale
  - Physics simulation: profile early
  - Geometry nodes: Test with simple scenes first
  - Export pipeline: Test with simple cube first
  - Start with end-to-end tests
  - Visual polish: Start simple, refine incrementally

- **Phases 3-4**: Polish, integrate, optimize**
  - Visual style refinement
  - Export format validation
  - Documentation

  - User testing

  - Performance optimization

## Research Phase Recommendations
Phase 1: Research Blender API patterns, kitbash workflow
Phase 2: Build MVP prototype (1-2 arms, basic tile shapes)
Phase 3: Expand to multiple tile shapes, add following system
Phase 4: Add physics simulation (hybrid approach)
Phase 5: Add following target system
Phase 6: Add animation system for smooth arm movement
Phase 7: Build export pipeline
Phase 8: Add visual polish and final touches
Phase 9: Create documentation and tutorials
Phase 10: Integration testing, production validation

## Version Compatibility
- Python 3.11+ / 3.10/ / 3.11+ (latest)
- Blender 4.x (latest LTS)
- NumPy 1.26+ (compatible with BlenderProc, if needed)
- geometry nodes, animation rigging, physics
- Official Blender documentation is comprehensive
- BlenderArtists tutorials are excellent starting to geometry nodes and rigging

- community forums provide valuable insights on physics/animation integration

## Confidence Assessment
- **Core stack**: High confidence
- **Supporting libraries**: medium confidence
- **Geometry Nodes**: high confidence (official docs excellent)
- **Armature system**: medium confidence (good documentation, community resources)
- **Physics Engine**: high confidence (critical to get right, early)
- **Export pipeline**: high confidence (format-specific validation needed)
- **Testing**: medium confidence (start simple, expand incrementally)
