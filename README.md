# Tadashi

Tadashi is a Python library for program optimization and transformation using the ISL and PET libraries. It provides an interface to work with SCoPs (Static Control Parts) and enables program transformations like tiling, interchange, fusion, and more.

## Installation

### From PyPI

```bash
pip install tadashi
```

### From Source (Development)

```bash
git clone https://github.com/vatai/tadashi
cd tadashi
# Install system dependencies (Linux)
sudo third_party/install.sh
# Install Python package in editable mode
pip install -e .
# Build extensions in-place
python setup.py build_ext -i
```

### Using Docker

Alternatively, you can use the provided Dockerfiles in `deps/docker/`.

## Quick Start

An end-to-end example is provided in `examples/end2end.py`. This example demonstrates how to obtain loop nests (SCoPs) from a simple application, select a transformation, verify its legality, and measure performance.

```python
from pathlib import Path
from random import choice, seed
import tadashi
from tadashi.apps import Simple

# Initialize a simple application from a C file
app = Simple("examples/inputs/depnodep.c")

# Select a node (loop band) from the schedule tree
node = app.scops[0].schedule_tree[1]
print(f"Selected node: {node}")

# Choose a random available transformation
tr = choice(node.available_transformations)
print(f"Applying transformation: {tr}")

# Get valid arguments for the transformation
args = choice(node.get_args(tr, -10, 10))

# Perform the transformation and check legality
legal = node.transform(tr, *args)
print(f"Is transformation legal? {legal}")

# Compile and measure performance
app.compile()
print(f"Original execution time: {app.measure()}")

# Generate transformed code and measure again
transformed_app = app.generate_code()
transformed_app.compile()
print(f"Transformed execution time: {transformed_app.measure()}")
```

## Advanced Usage

### Using PET Backend (Default)

```python
from tadashi import TrEnum
from tadashi.translators import Pet

# Create a translator for C code using PET backend
translator = Pet()
translator.set_source('./examples/inputs/hello.c', [])

# Get the schedule tree
schedule_tree = translator.scops[0].schedule_tree

# Perform transformations
for node in schedule_tree:
    if node.node_type == 'BAND':
        # Apply transformations
        node.transform(TrEnum.TILE_1D, 4)
```

### Using Polly Backend

```python
from tadashi import TrEnum
from tadashi.translators import Polly

# Create a translator for C code using Polly backend
translator = Polly('clang')
translator.set_source('./examples/inputs/depnodep.c', [])

# Get the schedule tree
schedule_tree = translator.scops[0].schedule_tree

# Perform transformations
for node in schedule_tree:
    if node.node_type == 'BAND':
        # Apply transformations
        node.transform(TrEnum.INTERCHANGE, 0, 1)
```

## Available Transformations

- `TrEnum.TILE_1D` - 1D loop tiling
- `TrEnum.TILE_2D` - 2D loop tiling
- `TrEnum.TILE_3D` - 3D loop tiling
- `TrEnum.INTERCHANGE` - Loop interchange
- `TrEnum.FULL_FUSE` - Full loop fusion
- `TrEnum.FUSE` - Loop fusion
- `TrEnum.SPLIT` - Loop splitting
- `TrEnum.SCALE` - Loop scaling
- `TrEnum.SET_PARALLEL` - Set parallel execution
- `TrEnum.SET_LOOP_OPT` - Set loop optimization options

## Components

- `ccScop` - C++ class representing SCoP
- `Scop` - Python wrapper for SCoP operations
- `Node` - Schedule tree node representation
- `Translators` - Input format parsers:
  - `Pet` - Uses PET library
  - `Polly` - Uses LLVM Polly
- `Apps` - High-level abstractions for end-to-end workflows

## Dependencies

### System Dependencies

To build Tadashi from source, you need:

- LLVM & Clang (version 20 or 21 recommended)
- GMP (GNU Multiple Precision Arithmetic Library)
- Build tools (gcc, autoconf, pkg-config, libtool)

On Debian/Ubuntu, you can install these via:

```bash
sudo apt-get install git build-essential autoconf pkg-config libtool llvm-17-dev clang-17 libclang-17-dev libgmp-dev libomp-dev
```

Alternatively, use the provided script: `sudo third_party/install.sh`.

### Python Dependencies

- Python 3.8+
- Cython
- ISL (Integer Set Library) - bundled or linked
- PET (Program Transformation) - bundled or linked

## Documentation

Detailed API documentation is available at [https://tadashi.readthedocs.io/](https://tadashi.readthedocs.io/).

## Development

Run all tests:

```bash
python -m unittest discover tests
```

Run a specific test:

```bash
python -m unittest tests.test_apps.TestSimple.test_end2end_polly_flang
```

## License

MIT License
