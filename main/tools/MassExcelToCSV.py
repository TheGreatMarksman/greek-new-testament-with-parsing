import pandas as pd
from pathlib import Path

# Step 1: Build path
excel_dir = Path(__file__).parent / "rp_code_info_tables"
print(f"Looking in folder: {excel_dir.resolve()}")

# Step 2: Check if directory exists
if not excel_dir.exists():
    print("❌ Folder does not exist!")
    exit()

# Step 3: Loop through Excel files
found = False
for excel_file in excel_dir.glob("*.xlsx"):
    found = True
    print(f"Processing: {excel_file.name}")
    try:
        df = pd.read_excel(excel_file, sheet_name=0)
        csv_path = excel_file.with_suffix(".csv")
        df.to_csv(csv_path, index=False)
        print(f"✅ Saved CSV to: {csv_path.relative_to(Path.cwd())}")
    except Exception as e:
        print(f"❌ Failed to convert {excel_file.name}: {e}")

if not found:
    print("⚠️ No .xlsx files found in the folder.")
