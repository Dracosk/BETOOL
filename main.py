import sys
import subprocess
import time
import random

def run_module(module_name):
    subprocess.run([sys.executable, "-m", f'pipe.{module_name}'], check=True)
    print(f"Module {module_name} executed successfully.")

def run_main():
    run_module("fixtures")
    time.sleep(random.uniform(0.7, 1)) 
    run_module("results")
    time.sleep(random.uniform(0.5, 0.7))
    run_module("odds")
    print("Daily tasks executed successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        run_main()
        sys.exit(0)

    module_name = sys.argv[1].lower()
    valid_modules = ["fixtures", "leagues", "teams", "results", "odds"]

    if module_name == "daily":
        run_main()
    elif module_name in valid_modules:
        run_module(module_name)
    else:
        print(f"Unknown module name: {module_name}. Please choose from: {', '.join(valid_modules)}")
        sys.exit(1)

