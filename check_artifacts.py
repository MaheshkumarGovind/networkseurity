import pandas as pd
from pathlib import Path
import os

# Find latest Artifacts run
artifacts_dir = Path("Artifacts")
if not artifacts_dir.exists():
    print("❌ No Artifacts folder—re-run python main.py (it'll stop at transformation).")
else:
    runs = [d for d in artifacts_dir.iterdir() if d.is_dir() and d.name.startswith('20')]
    if not runs:
        print("❌ No run folders in Artifacts—re-run main.py.")
    else:
        latest_run = max(runs, key=os.path.getctime)
        train_path = latest_run / "data_ingestion" / "ingested" / "train.csv"
        test_path = latest_run / "data_ingestion" / "ingested" / "test.csv"
        
        for path, name in [(train_path, "train"), (test_path, "test")]:
            if path.exists():
                df = pd.read_csv(path)
                print(f"\n📊 {name.upper()}.CSV Columns: {df.columns.tolist()}")
                print(f"Shape: {df.shape}")
                print(f"'label' in columns? {'label' in df.columns}")
                print(f"Sample rows:\n{df.head(3)}")
            else:
                print(f"❌ {path} not found.")