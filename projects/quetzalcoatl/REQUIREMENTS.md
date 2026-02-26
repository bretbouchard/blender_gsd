# Quetzalcoatl Dragon — Requirements

## Concept

A thin, lanky dragon inspired by Quetzalcoatl (feathered serpent). Greyhound-like proportions — elegant, fast, serpentine.

## Core Attributes

### Body Morphology
- **Proportions**: Thin, lanky, elongated (like greyhounds/afghan hounds)
- **Length**: Very long — must fill cylindrical or spherical space fluidly
- **Motion**: Hypnotic, wave-like movement (motion blur potential)
- **Posture**: Serpentine but with limbs

### Surface Detail
- **Scales**: Lizard-like base
- **Feathers**: Scaly feathers (not fluffy bird feathers)
- **Layering**: Multiple layers of feather-scales
- **Iridescence**: Color-shifting, hypnotic quality
- **Translucency**: Some kind of invisible/translucent style option

### Controllable Features
- [ ] Size (overall scale)
- [ ] **Limbs: 0-4 legs (selectable pairs)**
- [ ] Scales (size, shape, color, density)
- [ ] Feathers (size, shape, color, iridescence)
- [ ] Face structure
- [ ] Snout (length, shape)
- [ ] Teeth (size, shape, count)
- [ ] Whiskers (length, density)
- [ ] Color groups and shifts
- [ ] Translucency/visibility

### Motion Requirements
- Fluid space-filling movement
- Wave propagation along body
- Hypnotic undulation
- Motion blur compatibility

## Technical Approach

### Geometry Nodes
- Procedural body generation with curve-based spine
- Instance-based scale/feather distribution
- Layer system for multiple feather-scale passes
- Attribute-based color grouping

### Shader System
- Iridescent material with viewing-angle color shift
- Translucent SSS for ethereal quality
- Mask-driven variation (color groups)

### Animation
- Wave modifier or procedural wave along spine
- Feather/scale response to body motion
- Secondary motion (whiskers, feather tips)

## Questions to Resolve

1. ~~How many limbs?~~ **SELECTABLE: 0-4 legs (pairs)**
2. ~~Wings?~~ **SELECTABLE: None, feathered, or membrane**
3. ~~Head crest or horns?~~ **SELECTABLE**
4. ~~Tail ending?~~ **SELECTABLE (feather tuft, pointed, rattle, etc.)**
5. Reference images or style targets?
