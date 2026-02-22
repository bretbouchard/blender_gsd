# MSG 1998 Project

**Period:** 1998 New York City
**Style:** Film noir / Legal thriller
**Output Format:** 1998 film stock aesthetic

## Directory Structure

```
msg-1998/
├── locations/          # 3D location builds
│   ├── LOC-XXX/       # Per-location blend files
│   │   ├── LOC-XXX.blend
│   │   └── render_layers/
├── compositing/        # SD compositing configs
│   ├── prompts/       # Positive/negative prompts
│   ├── controlnet/    # ControlNet configurations
│   └── layers/        # Layer blend configs
├── handoff/           # FDX GSD handoff packages
│   └── from_fdx/      # Received from FDX
└── output/            # Final renders
    ├── exr/           # EXR masters
    └── prores/        # Editorial deliverables
```

## Workflow

1. **Receive Handoff** from FDX GSD
   ```bash
   blender-gsd receive-handoff --from-fdx --scene SCN-XXX
   ```

2. **Build Location** from fSpy
   ```bash
   blender-gsd build-location LOC-XXX --from-fspy
   ```

3. **Render Passes** for compositing
   ```bash
   blender-gsd render-location LOC-XXX --passes all
   ```

4. **Composite with SD**
   ```bash
   blender-gsd composite --shot SHOT-XXX-XXX --with-sd
   ```

5. **Export for Editorial**
   ```bash
   blender-gsd export-editorial --shot SHOT-XXX-XXX --format prores
   ```

## 1998 Film Aesthetic

- **Color:** Kodak Vision 500T color science
- **Grain:** 35mm film grain, 500 ISO equivalent
- **Lens:** Vintage Cooke S4 flare characteristics
- **Resolution:** 2K (2048x1156) for 16:9

## See Also

- [.planning/MSG-1998-INTEGRATION.md](/.planning/MSG-1998-INTEGRATION.md) - Cross-project architecture
- [.planning/phases/09-msg-1998-locations/](/.planning/phases/09-msg-1998-locations/) - Location building phase
- [.planning/phases/12-msg-1998-compositing/](/.planning/phases/12-msg-1998-compositing/) - SD compositing phase
