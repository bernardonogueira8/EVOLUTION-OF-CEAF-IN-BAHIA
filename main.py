import argparse
from importlib import import_module


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de dados SIA/SUS - CEAF")
    parser.add_argument(
        "--stage",
        choices=("all", "extract", "transform"),
        default="all",
        help="Etapa a executar (transform também grava os arquivos processados).",
    )
    stage = parser.parse_args().stage

    if stage in ("all", "extract"):
        extractor_1 = import_module("app.0_extract")
        extractor_1.main()
        extractor_2 = import_module("app.1_extract")
        extractor_2.main()

    if stage in ("all", "transform"):
        transformer = import_module("app.2_transform")
        loader = import_module("app.3_load")
        datasets = transformer.transform_all()
        loader.load_all(datasets)


if __name__ == "__main__":
    main()
