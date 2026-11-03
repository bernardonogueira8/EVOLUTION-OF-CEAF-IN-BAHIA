from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "1_raw"
PROCESSED_DATA_DIR = DATA_DIR / "2_processed"
CURATED_DATA_DIR = DATA_DIR / "3_curated"

POPULATION_FOLDER = "População"
TRANSFORM_FOLDERS = (
    "Qtd_aprovada",
    "Valor_aprovado",
    "Qtd_apresentada",
    "Valor_apresentado",
    "Valor_do_complemento_federal",
    "Valor_do_complemento_do_gestor",
    "Valor_do_incremento",
)

TABNET_CONTENTS = (
    ("Qtd.aprovada", "Qtd_aprovada"),
    ("Valor_aprovado", "Valor_aprovado"),
    ("Qtd.apresentada", "Qtd_apresentada"),
    ("Valor_apresentado", "Valor_apresentado"),
    ("Valor_do_complemento_federal", "Valor_do_complemento_federal"),
    ("Valor_do_complemento_do_gestor", "Valor_do_complemento_do_gestor"),
    ("Valor_do_incremento", "Valor_do_incremento"),
)

YEARS = range(2025, 2026)
TABNET_URL = "http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sia/cnv/qaba.def"
TABNET_URL_POPULATION = "http://tabnet.datasus.gov.br/cgi/deftohtm.exe?ibge/cnv/popsvs2024br.def"