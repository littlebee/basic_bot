#!/usr/bin/env python3
import os
import shutil

shutil.copyfile("./README.md", "./docs/index.md")

shutil.rmtree("./docs/services")
shutil.rmtree("./docs/commons")
shutil.rmtree("./docs/test_helpers")

os.makedirs("./docs/services", exist_ok=True)
os.makedirs("./docs/commons", exist_ok=True)
os.makedirs("./docs/test_helpers", exist_ok=True)

services_dir = os.path.join("./src/basic_bot/services")
services = [
    file
    for file in os.listdir(services_dir)
    if file != "__init__.py" and file.endswith(".py")
]
for service in services:
    service_name = service[:-3]
    doc_file = f"./docs/services/{service_name}.md"
    with open(doc_file, "w") as f:
        # without the title, the mkdocs TOC entry will be stripped of
        # underscores and capitalized
        f.write(f"---\ntitle: {service_name}\n---\n")
    cmd = f"pydoc-markdown -m basic_bot.services.{service_name} >> {doc_file}"
    print(f"running: {cmd}")
    os.system(cmd)
