import psutil


def is_process_running(pid: int):
    try:
        psutil.Process(pid)
        return True
    except psutil.NoSuchProcess:
        return False


def is_pid_file_valid(pid_file: str):
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read())
            return is_process_running(pid)
    except FileNotFoundError:
        return False
