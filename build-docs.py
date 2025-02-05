#!/usr/bin/env python3
import os
import shutil

from typing import List, Tuple

FILE_BANNER = """
#
#      WARNING: this file is added by build-docs.py in the project root.
#
#              YOUR CHANGES HERE WILL BE OVERWRITTEN
"""
with open("./README.md", "r") as f_readme:
    with open("./docs/index.md", "w") as f_docs:
        f_docs.write(f"---\ntitle: README.md\n\n{FILE_BANNER}\n---\n")
        f_docs.write(f_readme.read())

doc_dirs: List[Tuple[str, str]] = [
    ("./src/basic_bot", "./docs/scripts"),
    ("./src/basic_bot/services", "./docs/services"),
    ("./src/basic_bot/commons", "./docs/commons"),
    ("./src/basic_bot/debug", "./docs/debug"),
]

for src_dir, dest_dir in doc_dirs:
    shutil.rmtree(dest_dir, ignore_errors=True)
    os.makedirs(dest_dir, exist_ok=True)
    dot_parts = ".".join(src_dir.split("/")[3:])
    if len(dot_parts) > 0:
        dot_parts += "."

    for file in os.listdir(src_dir):
        if file.endswith(".py") and not file.startswith("__"):
            file_name = file[:-3]
            doc_file = f"{dest_dir}/{file_name}.md"
            with open(doc_file, "w") as f:
                # without the title, the mkdocs TOC entry will be stripped of
                # underscores and capitalized
                f.write(f"---\ntitle: {file_name}")
                f.write(FILE_BANNER)
                f.write("\n---\n")

            cmd = f"pydoc-markdown -m basic_bot.{dot_parts}{file_name} >> {doc_file}"
            print(f"running: {cmd}")
            os.system(cmd)
