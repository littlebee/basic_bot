import os


pip_list = os.popen("python -m pip list").read()
# for each package with a name that starts with 'types'
# uninstall it
packages = pip_list.split("\n")[2:]

for package in packages:
    # Extract package name from line (first column)
    if package.strip():
        package_name = package.split()[0]
        if package_name.startswith("types-"):
            print(f"Uninstalling {package_name}...")
            os.system(f"python -m pip uninstall -y {package_name}")

print("Finished uninstalling types- packages")
