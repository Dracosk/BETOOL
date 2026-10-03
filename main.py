import sys
import subprocess
import time
import random
import pandas as pd
from ml.predict import prediction_run
import datetime

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

def run_bot():

    df_bets = prediction_run()
    
    if df_bets.empty:
        print("No bets to place today.")
        return
    cols = ['game_date', 'local', 'away', 'market', 'bet_name', 'model_prob', 'odd', 'ev_pct', 'bank_pct']
    df_bets = df_bets[[c for c in cols if c in df_bets.columns]]

    print('\nChosen events for betting:')
    print('1. Only today\'s events')
    print('2. matching events for the next 3 days')
    print('3. Complete betting list')

    choice = input("Enter your choice (1, 2, or 3): ")

    if choice == '1':
        today = datetime.date.today()
        df_export = df_bets[df_bets['game_date'] == pd.Timestamp(today)]
        if df_export.empty:
            print("No bets to place today.")
            return
    elif choice == '2':
        three_days = datetime.date.today() + datetime.timedelta(days=3)
        df_export = df_bets[(df_bets['game_date'] >= pd.Timestamp(datetime.date.today())) & (df_bets['game_date'] <= pd.Timestamp(three_days))]
        if df_export.empty:
            print("No bets to place in the next 3 days.")
            return
    elif choice == '3':
        df_export = df_bets
    else:
        print("Invalid choice. Please enter 1, 2, or 3.")
        sys.exit(1)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'paper_bets_{timestamp}.csv'
    df_export.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Exported {len(df_export)} bets to {filename}")
    print("Betting list exported successfully, please check the CSV file to monitor the bets")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        run_main()
        sys.exit(0)

    module_name = sys.argv[1].lower()
    valid_modules = ["fixtures", "leagues", "teams", "results", "odds"]

    if module_name == "daily":
        run_main()
    elif module_name == "bot":
        run_bot()
    elif module_name in valid_modules:
        run_module(module_name)
    else:
        valid_options = valid_modules + ["daily", "bot"]
        print(f"Unknown module name: {module_name}. Please choose from: {', '.join(valid_options)}")
        sys.exit(1)

