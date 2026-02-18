# Claude Prompt Pack for Blender GSD

This document provides ready-to-use prompts for working with the Blender GSD Framework using Claude.

## Quick Reference

### Creating a New Project

```
I want to create a new artifact project called [PROJECT_NAME] that generates [DESCRIPTION].

The artifact should:
- [Feature 1]
- [Feature 2]
- [Feature 3]

Please:
1. Create the project structure under projects/[PROJECT_NAME]/
2. Implement the artifact builder script
3. Create example task YAML files
4. Add documentation
```

### Adding a New Style/Variant

```
Add a new variant to the [PROJECT_NAME] project with these parameters:

- Parameter 1: [value]
- Parameter 2: [value]
- Parameter 3: [value]

Create a task YAML file at projects/[PROJECT_NAME]/tasks/[variant_name].yaml
```

### Debugging Geometry Issues

```
I'm seeing [ISSUE_DESCRIPTION] when generating [ARTIFACT_NAME].

The task file is at: projects/[PROJECT_NAME]/tasks/[task_file].yaml

Please:
1. Analyze the geometry generation code
2. Identify the issue
3. Propose a fix
4. Test the fix with the task file
```

### Optimizing Performance

```
The generation of [ARTIFACT_NAME] is taking too long (current: [X] seconds).

Please:
1. Profile the generation pipeline
2. Identify bottlenecks
3. Suggest optimizations
4. Implement the optimizations
```

## Workflow Prompts

### Starting Fresh

```
I'm starting a new session with the Blender GSD Framework. Please:

1. Check the current state of the project
2. Review any uncommitted changes
3. Show me what tasks are available to run
4. Suggest next steps based on .planning/STATE.md
```

### Running Tasks

```
Run all 5 Neve knob export tasks and verify the outputs.

For each task:
1. Execute the task
2. Check the output file exists
3. Verify file size is reasonable
4. Report any issues
```

### Exporting Assets

```
Export the following assets from the [PROJECT_NAME] project:

- [Asset 1]
- [Asset 2]
- [Asset 3]

Use the [FORMAT] export profile with these settings:
- Setting 1: [value]
- Setting 2: [value]
```

## Debugging Prompts

### Visual Debugging

```
I need to debug the geometry generation for [ARTIFACT_NAME].

Please:
1. Add debug visualization nodes to show [MASK/ATTRIBUTE/EFFECT]
2. Render a preview image
3. Save to build/debug_[name].png
4. Explain what I'm seeing
```

### Parameter Exploration

```
I want to explore different parameter values for [PARAMETER_NAME] in [ARTIFACT_NAME].

Create a batch of task files with these values:
- [value1]
- [value2]
- [value3]

Generate all variants and create a comparison grid image.
```

### Node Tree Inspection

```
The node tree for [ARTIFACT_NAME] is getting complex. Please:

1. Analyze the current node layout
2. Identify opportunities for:
   - Grouping related nodes
   - Simplifying calculations
   - Removing redundant operations
3. Propose a cleaner organization
```

## Documentation Prompts

### Writing Specs

```
Create a technical specification for the [FEATURE_NAME] in [PROJECT_NAME].

Include:
- Overview and purpose
- Parameter definitions
- Implementation details
- Usage examples
- Visual reference images
```

### Updating README

```
Update the README.md to reflect the new [FEATURE/PROJECT] addition.

Include:
- Quick start example
- Parameter table
- Feature list
- Link to detailed documentation
```

### Creating Tutorials

```
Write a step-by-step tutorial for creating a [ARTIFACT_TYPE] using the framework.

Target audience: [BEGINNER/INTERMEDIATE/ADVANCED]

Cover:
1. Setting up the task file
2. Understanding parameters
3. Running generation
4. Exporting results
5. Troubleshooting common issues
```

## Analysis Prompts

### Code Review

```
Review the [SCRIPT_NAME] script for:

- Code quality
- Performance issues
- Determinism violations
- Documentation completeness
- Error handling

Provide specific suggestions for improvement.
```

### Parameter Audit

```
Audit the parameter usage in [PROJECT_NAME]:

1. List all parameters used
2. Identify unused parameters
3. Find hardcoded values that should be parameters
4. Suggest parameter groupings
5. Check for duplicate/overlapping parameters
```

### Dependency Analysis

```
Analyze the dependencies in the [PROJECT_NAME] project:

1. List all Python imports
2. Identify Blender API calls
3. Find external dependencies
4. Suggest ways to reduce coupling
5. Document the dependency graph
```

## Integration Prompts

### Adding Export Formats

```
Add support for [FORMAT] export to the framework.

Requirements:
- Support modifier application
- Handle materials/textures
- Optimize for [USE_CASE]
- Add to export profiles

Create the necessary code in lib/exports.py and document the usage.
```

### Creating Presets

```
Create a preset library for [CATEGORY] artifacts.

Categories:
- [Subcategory 1]
- [Subcategory 2]
- [Subcategory 3]

Each preset should define sensible defaults for common use cases.
```

### Building Utilities

```
Create a utility script that:

- [Function 1]
- [Function 2]
- [Function 3]

Place it in scripts/ and add documentation.
```

## Testing Prompts

### Regression Testing

```
Create a regression test suite for [PROJECT_NAME]:

1. Define test cases for each variant
2. Include parameter edge cases
3. Test export functionality
4. Verify determinism (same output on repeated runs)
5. Add visual comparison tests
```

### Performance Benchmarking

```
Benchmark the generation of [ARTIFACT_NAME]:

1. Measure generation time
2. Profile memory usage
3. Identify performance trends with different parameter values
4. Create a benchmark report
```

## Best Practices

### When asking Claude to help with Blender GSD:

1. **Be Specific** - Provide exact file paths and parameter values
2. **Show Context** - Reference existing code/patterns when possible
3. **Verify Determinism** - Ask Claude to ensure outputs are reproducible
4. **Request Documentation** - Ask for inline comments and README updates
5. **Test Incrementally** - Build and test step by step

### Example Good Prompt:

```
Add a new knurling profile to the Neve knobs project called "sharp_triangular"
that creates sharp V-shaped ridges.

Implementation:
- Add knurl_profile parameter support to neve_knob_gn.py
- Create task file at projects/neve_knobs/tasks/knob_style6_sharp_triangular.yaml
- Set knurl_profile=1.0 for maximum sharpness
- Export as GLB

Please test the generation and verify the ridges are sharp, not rounded.
```

### Example Bad Prompt:

```
Make the knobs look better.
```

## Tips

- Use `projects/[name]/tasks/*.yaml` for task files
- Use `projects/[name]/scripts/*.py` for artifact builders
- Use `lib/*.py` for framework code
- Always test with `blender --background --python scripts/run_task.py -- [task_file]`
- Check outputs in `projects/[name]/build/`

## Common Tasks Quick Reference

| Task | Command |
|------|---------|
| Export single artifact | `blender -b -P scripts/run_task.py -- tasks/example.yaml` |
| Inspect interactively | `blender -P scripts/run_task.py -- tasks/example.yaml` |
| Check git status | `git status` |
| View planning state | `cat .planning/STATE.md` |
| List available tasks | `find projects -name "*.yaml" -path "*/tasks/*"` |
