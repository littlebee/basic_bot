import os
import sys
import shutil


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


def build_and_test(target_project_dir: str) -> None:
    os.chdir(target_project_dir)

    print("building project via {target_project_dir}/build.sh ...")
    os.system("./build.sh")

    print("testing project via {target_project_dir}/test.sh ...")
    os.system("./test.sh")


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
