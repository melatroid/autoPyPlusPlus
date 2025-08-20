# -- Path setup --------------------------------------------------------------
# Add the src directory to the Python path so Sphinx can find your modules
import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

# -- Project information -----------------------------------------------------
project = 'Hello World'
copyright = '2025, Hello World 2'
author = 'Hello World 3'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',         # Generate documentation from docstrings
    'sphinx.ext.napoleon',        # Support for Google/Numpy style docstrings
    'sphinx.ext.viewcode',        # Add links to highlighted source code
    'sphinx.ext.autosummary',     # Generate summary tables for modules/classes
    #'myst_parser',                # Support for Markdown files (MyST)
    #'sphinx_autodoc_typehints',   # Show type hints in the API docs
    # 'sphinx.ext.intersphinx',   # Cross-references to other projects' documentation
    # 'sphinx.ext.todo',          # Support for todo items
    # 'sphinx.ext.mathjax',       # Render math formulas using MathJax
    # 'sphinx.ext.graphviz',      # Support for Graphviz diagrams
    # 'sphinx_copybutton',        # Adds a "copy" button to code blocks
]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
autosummary_generate = True

# -- Options for HTML output -------------------------------------------------
html_theme = 'alabaster'
html_static_path = ['_static']

# -- HTML theme options (commented examples) ---------------------------------
# html_theme_options = {
#     "collapse_navigation": False,
#     "navigation_depth": 4,
#     "logo_only": True,
# }
# html_logo = '_static/your_logo.png'
# html_favicon = '_static/your_favicon.ico'
# html_sidebars = {}  # Customize the sidebar

# html_show_sourcelink = True  # Show "Show Source" link in pages
# html_last_updated_fmt = "%b %d, %Y"  # Last updated date at the bottom

# -- Autodoc settings --------------------------------------------------------
autodoc_member_order = 'bysource'
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    # 'private-members': True,       # Show private members (underscore-prefixed)
    # 'special-members': '__init__,__str__', # Show special (magic) methods
    # 'inherited-members': True,     # Show inherited members from parent classes
    # 'exclude-members': '',         # Exclude specific members
}
autosummary_generate = True

# -- Napoleon settings (for Google/Numpy style docstrings) -------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True

napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# -- Intersphinx example (cross-project references) --------------------------
# intersphinx_mapping = {
#     'python': ('https://docs.python.org/3', None),
#     'numpy': ('https://numpy.org/doc/stable/', None),
# }

# -- Todo extension options --------------------------------------------------
# todo_include_todos = True

# -- Myst Parser (Markdown) --------------------------------------------------
myst_enable_extensions = [
    "deflist",
    "colon_fence",
    # "linkify",        # Autolink URLs
    # "substitution",   # Substitutions (variables in markdown)
]

# -- Syntax highlighting and code style --------------------------------------
# pygments_style = "sphinx"  # Code highlighting style
# pygments_dark_style = "monokai"  # Dark mode highlighting style (if supported)

# -- Language and localization options ---------------------------------------
# language = 'en'
# locale_dirs = ['locales/']  # Path to translation files

# -- PDF, EPUB, and advanced export formats ----------------------------------
# latex_engine = 'pdflatex'
# epub_show_urls = 'footnote'

# -- Custom static files (CSS/JS) --------------------------------------------
# def setup(app):
#     app.add_css_file('custom.css')
#     app.add_js_file('custom.js')

# >>> SPHINX GUI HOOK (do not remove)
try:
    from conf_autopy import *  # noqa: F401,F403
except Exception:
    pass
# <<< SPHINX GUI HOOK
