import pickle
import os
from typing import Any

from water_futures_battle.jurisdictions.entities import Province

DEST_FOLDER = '../.temp'

def upload_results(
        province_name: str,
        idx: int
    ) -> Any:
    file_path = f'{DEST_FOLDER}/results-{province_name}-{idx}.pkl' 

    try:
        with open(file_path, 'rb') as f:
            loaded_data = pickle.load(f)
        print(f"✅ Data successfully loaded from {file_path}")
        return loaded_data
        
    except FileNotFoundError:
        print(f"⚠️ File not found for {province_name} at {file_path}")
        return {}

    except Exception as e:
        print(f"❌ Error loading data for {province_name}: {e}")

        return {}

def save_results(
        province_name: str,
        idx: int,
        result: Any
    ) -> str:
    file_path = f'{DEST_FOLDER}/results-{province_name}-{idx}.pkl'

    if not os.path.exists(DEST_FOLDER):
        os.makedirs(DEST_FOLDER)

    try:
        with open(file_path, 'wb') as f:
            pickle.dump(result, f)
        print(f"✅ Data successfully saved to {file_path}")
        return file_path
        
    except Exception as e:
        print(f"❌ Error saving data: {e}")
        return ""
    