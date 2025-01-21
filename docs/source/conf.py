# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "CICADA"
copyright = "2024-2025, Peng Ding"
author = "Peng Ding"
html_title = "Project CICADA"
release = "0.1"

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))
print("Current sys.path:", sys.path)
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # 自动生成文档
    "sphinx.ext.viewcode",  # 添加源代码链接
    "sphinx.ext.napoleon",  # 支持 Google 和 NumPy 风格的文档字符串
    "sphinx.ext.autosummary",  # 自动生成摘要
    "myst_parser",  # 支持 Markdown 语法
    "sphinx_multitoc_numbering",  # 自动生成目录
    "sphinx_copybutton",  # 复制代码
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"

html_static_path = ["_static"]
autosummary_generate = True
html_search_options = {"type": "default"}


html_logo = "_static/cicada4.png"
html_short_title = "CICADA"

html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/solid.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/brands.min.css",
]

html_theme_options = {
    "announcement": (
        "Welcome to project CICADA, a growing collaborative agent framework for CAD automation."
    ),
    "source_repository": "https://github.com/Oaklight/cicada",
    "source_branch": "master",
    "source_directory": "docs/source/",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/Oaklight/cicada",
            "html": "",
            "class": "fa-brands fa-solid fa-github fa-2x",
        },
    ],
}
