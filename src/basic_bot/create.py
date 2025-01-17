# TODO : create directory structure and files described in the README.md
import os


def main():
    this_file = os.path.abspath(__file__)
    web_dir = os.path.join(os.path.dirname(this_file), "webapp")
    webdir_file_list = os.listdir(web_dir)

    print(f"hello chooms from {this_file}")
    print(f"web_dir: {web_dir}")
    print(f"webdir_file_list: {webdir_file_list}")


if __name__ == "__main__":
    main()
