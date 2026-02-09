from water_futures_battle.masterplan.services import parse_excel_masterplan
from water_futures_battle.masterplan.pydantic_model import Model
from pathlib import Path
from rich import print

def test_parse_masterplan():
    path = Path("data/masterplan.xlsx")
    json_d = parse_excel_masterplan(path)
    print(json_d)
    
    output = Model(**json_d)
    print(output.model_dump_json(indent=4))
