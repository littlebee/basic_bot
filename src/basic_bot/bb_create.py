"""
Usage:
```sh
    bb_create <new_project_directory_name>
```

Description:
    Create a new robot project directory with the given name.  The new project
    will contain a basic bot project structure with some example code and
    scripts to get you started.  The new project will be created in the current
    working directory.

"""

import os
import sys
import shutil
from pathlib import Path


if len(sys.argv) != 2:
    print("usage: bb_create <new_project_directory_name>")
    sys.exit(1)

project_name = sys.argv[1]
target_project_dir = os.path.join(os.getcwd(), project_name)


def create_project(target_project_dir: str) -> None:
    this_file = os.path.abspath(__file__)
    source_files_dir = os.path.join(os.path.dirname(this_file), "created_files")

    print(f"copying files from {source_files_dir} -> {target_project_dir}...")
    shutil.copytree(source_files_dir, target_project_dir)

    os.rename(
        os.path.join(target_project_dir, "___.gitignore"),
        os.path.join(target_project_dir, ".gitignore"),
    )
    rmdir(["webapp", "node_modules"])
    rmdir(["webapp", "dist"])


def build_and_test(target_project_dir: str) -> None:
    os.chdir(target_project_dir)

    print("building project via {target_project_dir}/build.sh ...")
    os.system("./build.sh")

    print("testing project via {target_project_dir}/test.sh ...")
    os.system("./test.sh")


def rmdir(dirs: list[str]) -> None:
    dir = Path(os.path.join(target_project_dir, *dirs))
    if dir.exists():
        shutil.rmtree(dir)


# Note: # main itself can't take arguments.  see, https://setuptools.pypa.io/en/latest/userguide/entry_point.html
def main() -> None:
    if os.path.exists(target_project_dir):
        print(
            f"project directory {target_project_dir} already exists. will not overwrite"
        )
        return

    create_project(target_project_dir)
    build_and_test(target_project_dir)

    print("done.\n\n")
    print(
        f"`cd ./{project_name}` to start working on your new robot project. 🎉\n"
        f"Also check out the README.md in ./{project_name} for more info."
        "May the force be with you.\n"
    )


if __name__ == "__main__":
    main()
