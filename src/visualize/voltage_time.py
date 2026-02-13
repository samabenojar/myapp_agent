from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

from src.normalize.nasa_to_canonical import CANONICAL_FILE
from src.schema.canonical import CANONICAL_COLUMNS

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PLOT_FILE = Path("outputs/voltage_vs_time.png")


def plot_voltage_time(
    canonical_path: Path = CANONICAL_FILE, output_path: Path = PLOT_FILE
) -> Path:
    if not canonical_path.exists():
        raise FileNotFoundError(f"Canonical file not found: {canonical_path}")

    with canonical_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        if reader.fieldnames is None:
            raise ValueError("Canonical file is missing a header row")
        if reader.fieldnames != CANONICAL_COLUMNS:
            raise ValueError(
                f"Canonical file columns must exactly match {CANONICAL_COLUMNS}, "
                f"got {reader.fieldnames}"
            )

        points: dict[str, list[tuple[float, float]]] = {}
        for row in reader:
            run_id = str(row["run_id"])
            timestamp = float(row["timestamp"])
            voltage = float(row["voltage"])
            points.setdefault(run_id, []).append((timestamp, voltage))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    for run_id, run_points in sorted(points.items()):
        run_points.sort(key=lambda item: item[0])
        timestamps = [item[0] for item in run_points]
        voltages = [item[1] for item in run_points]
        ax.plot(timestamps, voltages, marker="o", label=run_id)

    ax.set_title("Voltage vs Time")
    ax.set_xlabel("Time since run start (s)")
    ax.set_ylabel("Voltage (V)")
    ax.grid(True, alpha=0.4)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return output_path


def main() -> None:
    written_path = plot_voltage_time()
    print(f"Wrote plot to {written_path}")


if __name__ == "__main__":
    main()
