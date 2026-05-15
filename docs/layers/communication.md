# Communication layer

## Interface

See `nest_core.layers.communication` for the full Protocol definition.

## Default plugin

See `nest-plugins-reference` for the reference implementation.

## Writing a new communication plugin

1. Implement the Protocol from `nest_sdk`.
2. Register via entry point in your `pyproject.toml`.
3. Run conformance tests: `nest plugins conform <your-package>`.
