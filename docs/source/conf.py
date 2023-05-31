# Copyright (c) 2022, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/

# -- Path setup --------------------------------------------------------------

import datetime
import os
import sys

autoclass_content = "both"

sys.path.insert(0, os.path.abspath("../../"))

import oci_mlflow

version = oci_mlflow.__version__
release = version


# -- Project information -----------------------------------------------------

project = "OCI MLflow"
copyright = (
    f"2022, {datetime.datetime.now().year} Oracle and/or its affiliates. "
    f"Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/"
)
author = "Oracle Data Science"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "nbsphinx",
    "sphinx_code_tabs",
    "sphinx_rtd_theme",
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx.ext.todo",
    "sphinx_design",
    "sphinx.ext.extlinks",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# Get version
import oci_mlflow

version = oci_mlflow.__version__
release = version

# Unless we want to expose real buckets and namespaces
nbsphinx_allow_errors = True

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["build", "**.ipynb_checkpoints", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"
language = "en"

html_theme_options = {
    "light_logo": "logo-light-mode.png",
    "dark_logo": "logo-dark-mode.png",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
