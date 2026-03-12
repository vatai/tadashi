# Tadashi

Tadashi is a Python library for program optimization and transformation using the ISL and PET libraries. It provides an interface to work with SCoPs (Single Collection Optimization Problems) and enables program transformations like tiling, interchange, fusion, and more.

## Installation

Install via pip:
```bash
pip install tadashi
```

Or for development:
```bash
pip install -e .
```

## Development Setup

For development, use the provided setup:
```bash
# Build in-place for development
python setup.py build_ext -i

# Run tests
python -m unittest tests.test_apps.TestSimple.test_end2end_polly_flang
```

## Usage

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

## Dependencies

- ISL (Integer Set Library)
- PET (Program Transformation)
- LLVM/Polly (for Polly backend)
- Cython
- Python 3.8+

## License

MIT License
