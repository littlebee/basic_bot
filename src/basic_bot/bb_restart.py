#!/usr/bin/env python3

import subprocess
import time
import sys


def main(args):
    try:
        print("Stopping services")
        subprocess.run(["./stop.sh"] + args, check=True)

        print("Sleeping for 5s")
        time.sleep(5)

        print("Starting services")
        subprocess.run(["./start.sh"] + args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
