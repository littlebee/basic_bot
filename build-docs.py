#!/usr/bin/env python3
import os
import shutil

from typing import List, Tuple

src_dir = os.path.join(os.path.dirname(__file__), "src", "basic_bot")
docs_dir = os.path.join(os.path.dirname(__file__), "docs")
api_docs_dir = os.path.join(docs_dir, "Api Docs")
shutil.rmtree(api_docs_dir, ignore_errors=True)
os.makedirs(api_docs_dir, exist_ok=True)


FILE_BANNER = """
#
#      WARNING: this file is added by build-docs.py in the project root.
#
#              YOUR CHANGES HERE WILL BE OVERWRITTEN
"""
with open("./README.md", "r") as f_readme:
    with open(os.path.join(docs_dir, "index.md"), "w") as f_docs:
        f_docs.write(f"---\ntitle: Getting Started\n\n{FILE_BANNER}\n---\n")
        f_docs.write(f_readme.read())


# (src_dir, docs_dir)
doc_dirs: List[Tuple[str, str]] = [
    ("", "scripts"),
    ("services", "services"),
    ("commons", "commons"),
    ("debug", "debug"),
    ("test_helpers", "test_helpers"),
]

for src, dest in doc_dirs:
    this_src_dir = os.path.join(src_dir, src)
    dest_dir = os.path.join(api_docs_dir, dest)
    os.makedirs(dest_dir, exist_ok=True)

    readme_file = os.path.join(this_src_dir, "README.md")
    if os.path.isfile(readme_file):
        os.link(readme_file, os.path.join(dest_dir, "README.md"))

    for file in os.listdir(this_src_dir):
        if file.endswith(".py") and not file.startswith("__"):
            file_name = file[:-3]
            doc_file = f"{dest_dir}/{file_name}.md"
            with open(doc_file, "w") as f:
                # without the title, the mkdocs TOC entry will be stripped of
                # underscores and capitalized
                f.write(f"---\ntitle: {file_name}")
                f.write(FILE_BANNER)
                f.write("\n---\n")
            dot_parts = "" if src == "" else f".{src}"
            cmd = f'pydoc-markdown -m basic_bot{dot_parts}.{file_name} >> "{doc_file}"'
            print(f"running: {cmd}")
            os.system(cmd)
