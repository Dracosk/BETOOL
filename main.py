import sys
import subprocess

def run_module(module_name):
    subprocess.run([sys.executable, "-m", f'pipe.{module_name}'], check=True)
    print(f"Module {module_name} executed successfully.")

def run_main():
    run_module("fixtures")
    run_module("results")
    print("Daily tasks executed successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        run_main()
        sys.exit(0)

    module_name = sys.argv[1].lower()
    valid_modules = ["fixtures", "leagues", "teams", "results"]

    if module_name == "daily":
        run_main()
    elif module_name in valid_modules:
        run_module(module_name)
    else:
        print(f"Unknown module name: {module_name}. Please choose from: {', '.join(valid_modules)}")
        sys.exit(1)

