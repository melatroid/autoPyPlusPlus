# -- Path setup --------------------------------------------------------------
import os
import sys
sys.path.insert(0, os.path.abspath('..'))  # Projekthauptverzeichnis zum Importieren

# -- Project information -----------------------------------------------------
project = 'Mein Projekt'
copyright = '2025, Mein Name'
author = 'Mein Name'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',         # Doku aus Docstrings
    'sphinx.ext.napoleon',        # Google/Numpy-Style Docstrings
    'sphinx.ext.viewcode',        # Quellcode-Ansicht
    'sphinx.ext.autosummary',     # Modulübersichten
    'sphinx_autodoc_typehints',   # Typ-Hints in API-Doku (pip install sphinx-autodoc-typehints)
    'myst_parser',                # Markdown-Unterstützung (pip install myst-parser)
]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'   # ReadTheDocs-Theme (pip install sphinx_rtd_theme)
html_static_path = ['_static']

# -- Autodoc settings --------------------------------------------------------
autodoc_member_order = 'bysource'
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}
autosummary_generate = True

# -- Napoleon settings (für Google/Numpy Style Docstrings) -------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True

# -- Myst Parser (Markdown) --------------------------------------------------
myst_enable_extensions = [
    "deflist",
    "colon_fence",
]
