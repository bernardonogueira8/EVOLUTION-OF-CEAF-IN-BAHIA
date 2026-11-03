from pathlib import Path
import unicodedata

import pandas as pd

from app.utils import POPULATION_FOLDER, RAW_DATA_DIR, TRANSFORM_FOLDERS


def transform_folder(
    folder_path: Path,
    *,
    population: bool | None = None,
) -> pd.DataFrame:
    csv_files = sorted(folder_path.glob("*.csv"))
    if not csv_files:
        print(f"Nenhum CSV encontrado em {folder_path}; pasta ignorada.")
        return pd.DataFrame()

    if population is None:
        normalized_name = (
            unicodedata.normalize("NFKD", folder_path.name)
            .encode("ascii", "ignore")
            .decode("ascii")
            .casefold()
        )
        population = normalized_name in {"populacao", "population"}

    skiprows, skipfooter = (4, 8) if population else (6, 14)
    frames = []

    for csv_file in csv_files:
        frame = pd.read_csv(
            csv_file,
            encoding="latin-1",
            skiprows=skiprows,
            skipfooter=skipfooter,
            engine="python",
            sep=";",
        )
        frame["Ano"] = csv_file.stem
        frames.append(frame)

    return pd.concat(frames, ignore_index=True)


def transform_all(raw_data_dir: Path = RAW_DATA_DIR) -> dict[str, pd.DataFrame]:
    datasets: dict[str, pd.DataFrame] = {}

    for folder_name in (POPULATION_FOLDER, *TRANSFORM_FOLDERS):
        folder_path = raw_data_dir / folder_name
        if not folder_path.is_dir():
            print(f"Pasta não encontrada: {folder_path}; ignorando.")
            continue

        dataset = transform_folder(
            folder_path,
        )
        if not dataset.empty:
            datasets[folder_name] = dataset

    return datasets