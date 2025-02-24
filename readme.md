- [Breaking changes in v0.2.0](#org7475ca6)
- [Documentation:](#org4405622)
  - [Prerequisites](#orgc7453a6)
  - [Quick start](#org3b77a23)
    - [End-to-end example](#org0ae3bce)
- [Build instructions:](#orgee7dfba)
- [Run from docker](#org19ccccd)



<a id="org7475ca6"></a>

# Breaking changes in v0.2.0

Code generation is different. Code like this

```python
scops.generate_code()
```

should be replace with code like this:

```python
transformed_app = app.generate_code()
```

Now both the old `app`, and new `transformed_app` stay "alive", i.e. the user can compile and measure both of them.


<a id="org4405622"></a>

# Documentation:

After the double blind review and the end of the anonymity requirement, detailed API documentation will be uploaded to <https://tadashi.readthedocs.io/> (or a similar URL).

Until then these API docs can be downloaded (from the root dir of this repo) as:

-   tadashi.pdf (PDF)
-   apidocs.tgz (tgz-ed html)


<a id="orgc7453a6"></a>

## Prerequisites

Compile Tadashi (as described below), and set the `PYTHONPATH` environment variable to point to the repository root.


<a id="org3b77a23"></a>

## Quick start

An [end-to-end](./examples/end2end.py) example is provided below (split into parts with comments and outputs). This example can be run from the repository root with the following command:

```bash
PYTHONPATH=. python examples/end2end.py
```


<a id="org0ae3bce"></a>

### End-to-end example

After importing Tadashi we obtain the loop nests (SCoPs) from a [Simple](./tadashi/apps.py) app.

```python
import tadashi
from tadashi.apps import Simple
app = Simple("examples/depnodep.c")
scops = tadashi.Scops(app)
```

Select a node and a transformation, and check that the transformation is available on the selected node.

```python
node = scops[0].schedule_tree[1]
print(f"{node=}")
tr = tadashi.TrEnum.FULL_SHIFT_VAR
print(f"{tr in node.available_transformations=}")
# output:
```

Check the available arguments for the given node-transformation pair.

```python
print(f"{tr=}")
lu = node.available_args(tr)
print(f"{len(lu)=}")
print(f"{lu[0]=}")
print(f"{lu[1]=}")
# output:
```

Perform the transformation and check legality.

```python
args = [13, 1]
print(f"{node.valid_args(tr, *args)=}")
legal = node.transform(tr, *args)
print(f"{legal=}")
# output:
```

Generate new code, compile it and measure the performance.

```python
scops.generate_code()
app.compile()
print(f"{app.measure()=}")
# output:
```


<a id="orgee7dfba"></a>

# Build instructions:

Before building, install LLVM and other (system) packages (check [dockerfile](./docker/tadashi.dockerfile) for an exact list of `apt-get` packages).

```bash
git clone --recursive https://github.com/vatai/tadashi.git
mkdir tadashi/build
cd tadashi/build
cmake ..
cmake --build .
```


<a id="org19ccccd"></a>

# Run from docker

```bash
mk_dot_env.sh  # create .env file with USER, UID, GROUP, GID
docker compose build tadashi # build images
docker compose run --rm -it tadashi
```

The tadashi binds the host repo to `/workdir` inside the container.

Tadashi should be rebuilt from the container (i.e. these are instructions primarily for developers):

```bash
mkdir /workdir/build
cd /workdir/build
cmake ..
cmake --build .
```

The dependencies are built during the `docker compose build` command under `/tadashi/build/_deps` and the environment is set up that these dependencies are used (i.e. not rebuilt again).
