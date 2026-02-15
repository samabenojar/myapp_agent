import pandas as pd
from schema.canonical import BatterySample

def load_nasa(path: str):
    df = pd.read_csv(path)

    normalized = []

    for _, row in df.iterrows():
        sample = BatterySample(
            run_id="nasa_001",
            timestamp=row["Time"],
            voltage=row["Voltage_measured"],
            current=row["Current_measured"],
            temperature=row.get("Temperature_measured"),
            cycle=row.get("Cycle")
        )
        normalized.append(sample.dict())

    return pd.DataFrame(normalized)
