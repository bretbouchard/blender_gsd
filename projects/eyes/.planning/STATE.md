# Eyes Project State

## Current Position

**Phase**: Phase 1 Complete
**Status**: Ready for Phase 2 Planning
**Last Updated**: 2026-02-25

## Session Memory

### 2026-02-25 - Phase 1 Complete
- Implemented eye_geometry.py with nested sphere node group
- Implemented eye_distribution.py with point distribution
- Implemented generate_eyes.py with Blender UI panel
- Implemented benchmark_eyes.py for performance testing
- Tested in Blender 5.0 - working correctly
- Created test_eye.blend verification file

### 2026-02-25 - Project Initialization
- Created project structure at `/projects/eyes/`
- Defined PROJECT.md with vision and core concepts
- Created REQUIREMENTS.md with 12 requirements across P0-P2
- Built ROADMAP.md with 5 phases for v0.1 milestone

## Key Decisions

1. **Instance-Based Architecture**: Using Geometry Nodes instances for performance at scale (millions of eyes)

2. **Three-Layer Eye Structure**: Outer (cornea) → Middle (iris) → Inner (pupil) for visual depth

3. **Size-Speed Correlation**: Smaller eyes rotate faster, creating "wheels within wheels" effect

4. **Separate Material System**: Reflection and emission as independent, composable systems

5. **Phase-Based Delivery**: Core geometry first, then animation, materials, effects, polish

## Active Context

### Immediate Next Steps
1. Run `/gsd:plan-phase 2` for animation system
2. Implement blink-into-existence animation
3. Add size-based rotation system
4. Run performance benchmarks

### Open Questions
- Should we use OSL shaders for heat wave effects, or pure node-based?
- What's the optimal instance count before performance degrades?
- How to handle reflection at "space" distance - cubemap or procedural?

## Dependencies

### External
- Blender 5.0+ (Geometry Nodes, Shader Nodes)
- Eevee/Cycles for rendering

### Internal
- Parent project: blender_gsd framework
- Potential reuse: lib/geometry_nodes/ utilities

## Notes for Future Sessions

- User vision is highly poetic/abstract - translate to concrete parameters
- "Wheels within wheels" is key visual metaphor
- Performance at scale is critical (12 to millions)
- Atmospheric effects (heat, condensation) are important for final look
