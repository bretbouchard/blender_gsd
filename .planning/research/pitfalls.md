# Pitfalls Research

**Domain:** Blender Mechanical Platform (Physics Simulation, Geometry Nodes, Tile Placement, Export Pipeline)
**Researched:** 2026-03-04
**Confidence:** HIGH

---

## Critical Pitfalls
### Pitfall 1: Physics Simulation Parameter Mismatch
**What goes wrong:**
Physics simulations produce unstable, jittery, or explosive results. Objects pass through each other, simulations appear to run in slow motion despite adequate hardware.
**Why it happens:**
Developers use default physics parameters (Time Step: 0.04, Solver Iterations: 10) without understanding their impact. Fast-moving objects require higher iterations (50-100), and small objects (<20cm) become inherently unstable with default settings.
**How to avoid:**
- Set Time Step to 0.001-0.01s for most precise simulations
- Increase Solver Iterations to 10-20 for normal, 50-100 for fast-moving objects
- Use Convex Hull or Box collision shapes for objects smaller than 20cm
- Never use Mesh collision for small or fast objects (causes tunneling)
**Warning signs:**
- Objects vibrate or jitter during simulation
- Objects pass through collision boundaries
- Simulation "feels" slow despite simple scenes
- Cloth simulations penetrate collision objects
**Phase to address:**
Phase 1 (Foundation) - Establish physics parameter profiles as part of system configuration
Phase 2 (Core Systems) - Implement physics validation hooks and collision margin verification

---
### Pitfall 2: Geometry Node Over-Complexity
**what goes wrong:**
Geometry Node trees become unmaintainable, perform poorly, and become impossible to debug. Simple changes require tracing through dozens of nodes. Performance degrades exponentially with node count.
**Why it happens:**
Developers create sprawling node trees without modularization. Using Capture Attribute excessively creates auxiliary connection pollution. Not organizing with frames and node groups makes trees unreadable.
**How to avoid:**
- Use Store Named attribute and Named Attribute instead of Capture Attribute to reduce connections
- Organize with frames and meaningful labels
- Create reusable node group libraries
- Maintain left-to-right flow with minimal cross-connections
- Keep node trees under 50 nodes for main operations; use nested groups
**Warning signs:**
- Node tree spreads geometrically with each new feature
- Making changes requires updating multiple disconnected nodes
- Viewport performance degrades with complexity
- Cannot easily identify what a node does
**Phase to address:**
Phase 1 (Foundation) - Establish node group library architecture
Phase 2 (Core Systems) - Create node group style guide and modularity requirements

---
### Pitfall 3: Tile Placement Overlap and Misalignment
**what goes wrong:**
Procedurally placed tiles overlap at grid boundaries, have inconsistent spacing, and textures misalign. Center points accumulate duplicate geometry causing rendering artifacts and intersection errors.
**Why it happens:**
Developers use naive grid placement without accounting for tile dimensions and spacing. Not using position-based selection to remove duplicates. UV mapping not considered during placement calculation.
**how to avoid:**
- Use Position nodes with Vector Math to identify and remove duplicate placements
- Apply Merge by Distance for remaining vertex overlaps
- Calculate tile positions accounting for spacing and margins
- Use curve-based alignment with Index nodes for consistent positioning
- Verify face normals and vertex ordering before placement
**Warning signs:**
- Black flickering artifacts at tile boundaries
- Geometry intersections visible in rendered output
- Texture seams visible at tile edges
**Phase to address:**
Phase 2 (Core Systems) - Generate tiles, check for intersections
Phase 3 (Integration) - Add tile placement to scene

---
### Pitfall 4: Export Format Data Loss
**what goes wrong:**
Exported FBX/glTF/USD files have missing materials, incorrect scale, broken animations, or wrong coordinate systems. Materials that looked correct in Blender don't work in target applications.
**why it happens:**
Developers export directly without format-specific validation. FBX uses Blender's coordinate system (Z-up) while Unity/Unreal use Y-up. GLTF uses different unit systems. USD requires Hydra render delegates and and different world spaces. Material node networks that work in one tool may not work in another.
**How to avoid:**
- Test export with single asset first, validate in target application
- Apply transforms (Ctrl+A) before exporting
- For animations, bake frame range and in NLA and use Blender's NLA system for animation transfer
- Verify coordinate system settings forFBX: Y-up, glTF: Meters, USD: cm)
- For procedural materials, bake textures to PBR maps before exporting
- Ensure materials are embedded or paths are relative
- For glTF, enable Draco compression
- For USD, use USDZ export for for ARKit compatibility
**Warning signs:**
- Materials appear pink/black or or target app
- Models explode apart when imported
- Animations don't play correctly in target application
- Coordinate system is wrong in target app
- UV maps look distorted or stretched
**Phase to address:**
Phase 3 (Integration) - Implement export validation pipeline
Phase 4 (Output/Rendering) - Add format-specific export validation

---
### Pitfall 5: Deterministic Generation Seed Mismatch
**what goes wrong:**
Procedural generation produces different results on different runs. Team members cannot reproduce identical scenes. Batch operations produce inconsistent outputs. Floating-point precision differences across platforms cause subtle variations.
**why it happens:**
Developers forget to set explicit seeds. Random seeds propagate through node networks implicitly. Floating-point precision differences between Blender (x86) and other platforms (ARM) cause different results
**how to avoid:**
- Always set explicit seeds for procedural workflows requiring reproducibility
- Document expected seed values in configuration files
- Test seed propagation through the entire generation chain
- Verify cross-platform consistency if targeting multiple platforms
- Use fixed-point arithmetic where possible, avoid floating-point drift
**Warning signs:**
- Same parameters produce different results on different runs
- Cannot reproduce specific generation results
- Batch operations have inconsistent outputs
- Team members get different results for "identical" setups
**Phase to address:**
Phase 1 (Foundation) - Implement seed management system
Phase 2 (Core Systems) - Add deterministic generation validation

---
### Pitfall 6: Collision Proxy Complexity Neglect
**what goes wrong:**
Physics simulations run extremely slowly or crash when collision detection is enabled. High-poly collision meshes cause memory issues and Simulation becomes unplayable in real-time. Collision proxies are created but never tested with actual physics objects, resulting in wasted time and incorrect physics behavior.
**Why it happens:**
Developers use detailed character/prop meshes as collision bodies without simplification. Not testing collision performance with progressively complex meshes. Collision proxies are created once and then forgotten, leading to inaccurate physics and poor performance.
**How to avoid:**
- Create simplified collision proxies for detailed meshes
- Use Decimate modifier or simplify collision geometry
- Use Box/Sphere/Convex Hull for collision shapes when possible
- Layer collision complexity based on distance (close objects = simpler proxies
- Test collision performance with progressively complex meshes
**Warning signs:**
- Simulation frame rate drops below 10 FPS
- Blender crashes or runs out of memory during simulation
- Collision detection takes noticeably longer than with detailed proxies
- Objects appear to "float" or " jitter when using collision proxies
**Phase to address:**
Phase 2 (Core Systems) - Implement collision proxy system
Phase 3 (Integration) - Add collision complexity validation hooks

---
### Pitfall 7: Non-Manifold Geometry in Physics
**what goes wrong:**
Physics simulations fail or produce incorrect results. Cloth simulations don't drape correctly. Volume-based initialization fails. Collision detection produces artifacts and errors
**Why it happens:**
Developers use open meshes (holes, gaps) as physics collision objects without checking mesh integrity. Not verifying mesh is closed (manifold) before enabling physics. Non-manifold edges cause simulation instability.
**How to avoid:**
- Always verify mesh is manifold before physics simulation
- Use Edit Mode -> Select All -> Recalculate Normals (Shift+N)
- Check for non-manifold geometry with 3D Print Toolbox > Mesh Analysis
- Close holes and fill gaps before simulation
- Use volume-based initialization only with closed meshes
**Warning signs:**
- Cloth passes through mesh instead of draping over
- Simulation produces "explosions" or erratic behavior
- Collision detection misses faces
**Phase to address:**
Phase 2 (Core Systems) - Add mesh validation to system
Phase 3 (Integration) - Implement pre-simulation mesh verification

---
### Pitfall 8: Missing Group Output Connection
**what goes wrong:**
Geometry Node trees execute correctly but generate geometry, but final output is not connected to Group Output node. This breaks the chain, makes debugging difficult and and the output is not visible in the viewport or Users cannot see generated content without entering the node tree.
**why it happens:**
The Group Output node is at the end of the tree, but users forget to connect it. When node trees get complex, the output connection is often not documented. Without connection, the output is doesn't exist.
**How to avoid:**
- Always connect Group Output node to ensure execution
- Add validation in node groups to check for output
- Use meaningful naming for inputs, outputs, and node groups (e.g., "Tile_Placer_Debug", "TileOverlapChecker")
- Check all node trees for output connection before execution
**Warning signs:**
- Geometry generates but doesn't appear in viewport
- Generated content not visible in renders without entering node tree
- Generated output looks different in viewport vs. spreadsheet
- Missing or disconnected nodes in node tree
**Phase to address:**
Phase 1 (Foundation) - Establish output connection standards
Phase 2 (Core Systems) - Add Group Output to all procedural systems

---

## Technical Debt Patterns
| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|-----------------|-----------------|
| Using Mesh collision for all objects | More accurate collision | Performance penalty, harder to debug | Never - Use Box/Sphere/Convex Hull |
| Skipping transform application | Faster iteration | Incorrect scale/rotation in exports | Never - always apply transforms |
| Not baking procedural materials | Saves time, flexible editing | Broken exports, missing materials in target apps | Never for export - always bake first |
| Using default physics parameters | Faster setup | Unstable simulations, poor quality results | Only during prototyping - never for production |
| Hardcoding values in node trees | Quick implementation | Cannot update procedurally, hard to maintain | Never - use node inputs |
| Excessive subdivision at preview | Faster editing | Baked geometry | Memory bloat, hard to revert | Never - use adaptive subdivision |
| Realize Instances/Instances in viewports | Always use adaptive subdivision in modifiers |
| Omitting bake step | Faster simulation | Missing collision detection | Never - skip bake step in simulations |
| Debugging with immediate mode | Hard to iterate | Debug nodes in isolated | Never - use immediate mode for production debug

---

## Integration Gotchas
| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Unity/Unreal Engine | Not applying transforms before export; Use Y-up, check axis orientation | Unity's animation system uses .anim format, export as .fbx |
| glTF | Using Principled BSDF materials | Convert Principled BSDF to PBR textures before exporting |
| glTF | Procedural materials may not work in WebGL renderers | Bake procedural materials to image textures first |
| USD | Complex node networks require Hydra delegates | Scene description | USD | Different world space | USD | Material networks crash if not Hydra-compatible |
| FBX | Complex material networks fail silently | Apply texture bake | Convert to PBR textures before export |
| FBX | Mesh collisions cause tunneling | Use Convex Hull collision shapes for fast objects |
| FBX | Animation frame rate issues | Set consistent frame rate, sample animations |
| FBX | Scale inconsistencies | Apply transforms (Ctrl+A) to fix scale/rotation |
| glTF | Draco compression artifacts | Test compression with simple geometry first |
| glTF | Missing extensions | Verify required extensions are enabled in export settings |
| FBX | Binary format incompatibilities | Use ASCII FBX for compatibility with older software |
| USD | Missing payloads | Export only geometry, check Hydra delegate requirements |

---

## Performance Traps
| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| **Physics simulation explosion** | Frame rate drops below 10 FPS, simulation becomes unplayable | Increase solver iterations, use simpler collision shapes, 100+ objects |
| **Geometry Node evaluation overhead** | Viewport lag when editing node trees | Keep node trees simple, use LOD, bake when possible | 500+ nodes |
| **Tile placement at render time** | Black flickering, Z-fighting | Implement overlap detection, bake tiles, use instancing for distant tiles | 1000+ tiles |
| **Export memory usage** | Blender crashes during batch export | Export in batches, use simplified geometry for export, validate memory before exporting |

---

## Security Mistakes
| Mistake | Risk | Prevention |
|---------|------|------------|
| **Hardcoded absolute paths in Python scripts** | Scripts break when files move | Use relative paths or `pathlib` for asset resolution |
| **Embedded credentials in .blend files** | Security breach if .blend file is shared | Never store secrets in .blend files |
| **Unvalidated external Python libraries** | Malicious code execution | Only use libraries from trusted sources |
| **Missing file permission checks** | Runtime errors on file operations | Check file permissions before read/write operations |

---

## "Looks Done But Isn't" Checklist
- [ ] **Physics Simulation:** Often missing collision margin verification - check for objects pass through each other
- [ ] **Geometry Nodes:** Often missing Group Output connection - verify nodes execute with geometry
- [ ] **Tile Placement:** Often missing overlap detection - zoom to tile boundaries, check for intersection warnings
- [ ] **Export Pipeline:** Often missing material baking - verify materials in target app, test material assignment
- [ ] **Deterministic Generation:** Often missing seed propagation - regenerate twice with same seed, compare outputs
- [ ] **Collision Proxies:** Often missing proxy-visual sync - verify proxies match physics objects visually
- [ ] **Non-manifold Mesh:** Often missing manifold check - run Mesh Analysis before enabling physics
- [ ] **Group Output:** Often missing - check all node trees for Group Output connection

---

## Recovery Strategies
| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Physics Parameter Mismatch | low | Re-bake simulation with correct parameters |
| Geometry Node Complexity | high | Refactor into modular groups, rebuild incrementally |
| Tile Placement Overlap | low | Add overlap removal nodes, re-run generation |
| Export Data Loss | medium | Re-export with verified settings, check target app |
| Seed Mismanagement | low | Set explicit seeds, regenerate |
| Collision Mesh Complexity | medium | Create new proxies, reassign physics |
| Non-manifold Geometry | low | Fix mesh, re-enable physics |
| Missing Group Output | low | Connect output, verify execution |

---

## Pitfall-to-Phase Mapping
| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Physics Parameter Mismatch | Phase 1 | Run test simulation with varied object sizes/speeds |
| Geometry Node Complexity | Phase 1 | Review node tree, ensure modularity |
| Tile Placement Overlap | Phase 2 | Generate tiles, check for intersections |
| Missing Group Output | Phase 1 | Check all node trees for output connection |
| Export Data Loss | Phase 3 | Export single asset, verify in target app |
| Deterministic Seed | Phase 1 | Generate twice with same seed, compare outputs |
| Collision Mesh Complexity | Phase 2 | Create proxies, test performance vs accuracy |
| Non-Manifold Geometry | Phase 2 | Run Mesh Analysis, fix issues |
| Baked Materials | Phase 3 | Export, check target app material appearance |

---

## Sources
- Blender Official Documentation - Physics Simulation Tips (docs.blender.org)
- Blender 4.1 Release Notes - Performance Improvements (blender.org)
- CSDN Community - Geometry Nodes Best Practices (blog.csdn.net)
- Blender Artists Forum - Procedural Generation Discussions (blenderartists.org)
- Hugging Face - BlenderProc Synthetic Data Generation (hugging-face.cn)
- GitHub - Procedural Building Generator (github.com/wojtryb)
- Bilibili - Geometry Nodes Workflows (bilibili.com)
- NC State Extension - Charlotte Grass Maintenance Patterns (ncsu.edu)
- 3D Print Toolbox - Mesh Analysis (docs.blender.org/manual/en/latest/addons/3d_print_toolbox/mesh_analysis.html)

- glTF Specification - Materials (github.com/KhronosGroup/glTF)
- FBX SDK Documentation (docs.autodesk.com)
- USD Documentation (docs.pixar.org)

---
*Pitfalls research for: Blender Mechanical Platform (Physics Simulation, Geometry Nodes, Tile Placement, Export Pipeline)*
*Researched: 2026-03-04*
