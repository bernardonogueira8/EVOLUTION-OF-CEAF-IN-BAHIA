from pathlib import Path

import pandas as pd

from app.utils import PROCESSED_DATA_DIR


def load_all(
    datasets: dict[str, pd.DataFrame],
    processed_data_dir: Path = PROCESSED_DATA_DIR,
) -> list[Path]:
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    saved_files = []

    for name, dataset in datasets.items():
        if dataset.empty:
            print(f"Dataset {name} vazio; arquivo existente será preservado.")
            continue

        output_path = processed_data_dir / f"{name}.xlsx"
        dataset.to_excel(output_path, index=False)
        saved_files.append(output_path)
        print(f"Planilha processada salva: {output_path}")

    if not saved_files:
        print("Nenhum dataset foi carregado.")

    return saved_files