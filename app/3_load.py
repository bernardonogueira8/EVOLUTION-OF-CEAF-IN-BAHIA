from pathlib import Path

import pandas as pd

from app.utils import CURATED_DATA_DIR, PROCESSED_DATA_DIR


CURATED_METRICS = {
    "Qtd_apresentada.xlsx": "QTD Apresentada",
    "Qtd_aprovada.xlsx": "QTD Aprovado",
    "Valor_apresentado.xlsx": "Valor Apresentada",
    "Valor_aprovado.xlsx": "Valor Aprovado",
}

POPULATION_FILE = "População.xlsx"

CURATED_COLUMNS = [
    "Procedimento",
    "Macrorregião",
    "Período",
    "População",
    "QTD Apresentada",
    "QTD Aprovado",
    "Valor Apresentada",
    "Valor Aprovado",
]


def _to_numeric(value: object, *, source: str) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text or text == "-":
        return None

    normalized = text.replace(".", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError as error:
        raise ValueError(
            f"Valor inválido em {source}: {value!r}"
        ) from error


def _to_year(value: object, *, source: str) -> int:
    numeric_value = _to_numeric(value, source=source)
    if numeric_value is None or not numeric_value.is_integer():
        raise ValueError(f"Ano inválido em {source}: {value!r}")
    return int(numeric_value)


def create_curated(
    processed_data_dir: Path = PROCESSED_DATA_DIR,
    curated_data_dir: Path = CURATED_DATA_DIR,
) -> Path:
    curated: pd.DataFrame | None = None

    for filename, metric_name in CURATED_METRICS.items():
        source_path = processed_data_dir / filename
        if not source_path.is_file():
            raise FileNotFoundError(
                f"Planilha processada necessária não encontrada: {source_path}"
            )

        dataset = pd.read_excel(source_path)
        required_columns = {"Procedimento", "Ano", "Total"}
        missing_columns = required_columns.difference(dataset.columns)
        if missing_columns:
            raise ValueError(
                f"{source_path} não contém as colunas necessárias: "
                f"{', '.join(sorted(missing_columns))}"
            )

        region_columns = [
            column
            for column in dataset.columns
            if column not in {"Procedimento", "Ano", "Total"}
        ]
        if not region_columns:
            raise ValueError(f"Nenhuma coluna de macrorregião encontrada em {source_path}")

        long_data = dataset.melt(
            id_vars=["Procedimento", "Ano"],
            value_vars=region_columns,
            var_name="Macrorregião",
            value_name=metric_name,
        )
        long_data["Procedimento"] = long_data["Procedimento"].astype("string").str.strip()
        long_data["Macrorregião"] = long_data["Macrorregião"].astype("string").str.strip()
        long_data["Período"] = [
            _to_year(value, source=f"{source_path.name}/Ano")
            for value in long_data["Ano"]
        ]
        long_data = long_data.drop(columns="Ano")
        long_data[metric_name] = [
            _to_numeric(value, source=f"{source_path.name}/{metric_name}")
            for value in long_data[metric_name]
        ]

        keys = ["Procedimento", "Macrorregião", "Período"]
        if long_data[keys].isna().any().any():
            raise ValueError(f"Chaves vazias encontradas em {source_path}")
        if long_data.duplicated(keys).any():
            duplicate_keys = long_data.loc[
                long_data.duplicated(keys, keep=False), keys
            ].head()
            raise ValueError(
                f"Chaves duplicadas em {source_path}: "
                f"{duplicate_keys}"
            )

        if curated is None:
            curated = long_data
        else:
            curated = curated.merge(
                long_data,
                on=keys,
                how="outer",
                validate="one_to_one",
            )

    if curated is None or curated.empty:
        raise ValueError("Não há dados para gerar a planilha curated.")

    population_path = processed_data_dir / POPULATION_FILE
    if not population_path.is_file():
        raise FileNotFoundError(
            f"Planilha processada necessária não encontrada: {population_path}"
        )

    population_source = pd.read_excel(population_path)
    population_columns = {
        "Macrorregião de Saúde",
        "População_residente",
        "Ano",
    }
    missing_columns = population_columns.difference(population_source.columns)
    if missing_columns:
        raise ValueError(
            f"{population_path} não contém as colunas necessárias: "
            f"{', '.join(sorted(missing_columns))}"
        )

    population_source = population_source.loc[
        population_source["Macrorregião de Saúde"]
        .astype("string")
        .str.strip()
        .ne("Total")
    ]
    population = pd.DataFrame(
        {
            "Macrorregião": population_source[
                "Macrorregião de Saúde"
            ].astype("string").str.strip(),
            "Período": [
                _to_year(value, source=f"{population_path.name}/Ano")
                for value in population_source["Ano"]
            ],
            "População": [
                _to_numeric(value, source=f"{population_path.name}/População")
                for value in population_source["População_residente"]
            ],
        }
    )

    population_keys = ["Macrorregião", "Período"]
    if population[population_keys].isna().any().any():
        raise ValueError(f"Chaves vazias encontradas em {population_path}")
    if population.duplicated(population_keys).any():
        raise ValueError(
            f"Chaves de macrorregião e período duplicadas em {population_path}"
        )

    curated = curated.merge(
        population,
        on=population_keys,
        how="left",
        validate="many_to_one",
    )
    curated = curated.reindex(columns=CURATED_COLUMNS)
    curated = curated.sort_values(
        ["Período", "Macrorregião", "Procedimento"],
        kind="stable",
        ignore_index=True,
    )
    first_year = int(curated["Período"].min())
    last_year = int(curated["Período"].max())
    curated_data_dir.mkdir(parents=True, exist_ok=True)
    output_path = curated_data_dir / f"CEAF {first_year} a {last_year}.xlsx"
    curated.to_excel(output_path, index=False)
    print(f"Planilha curated salva: {output_path}")
    return output_path


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