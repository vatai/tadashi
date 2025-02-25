# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import re
import sys

os.mknod("../build/__init__.py").
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../tadashi"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Tadashi"
copyright = "2024, Anonymous org"
author = "Anonymous authors"
release = re.sub("^v", "", os.popen("git describe --tags").read().strip())


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.githubpages",
    "sphinx.ext.ifconfig",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    # "sphinx_autodoc_typehints",  # did't work when I tried :(
    "sphinx_rtd_theme",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
# autoclass_content = "both"
default_role = "py:obj"
todo_include_todos = True
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
autodoc_member_order = "bysource"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = "alabaster"
html_theme = "sphinx_rtd_theme"
# html_static_path = ["_static"]
