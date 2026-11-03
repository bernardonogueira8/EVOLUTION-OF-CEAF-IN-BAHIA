from pathlib import Path

from playwright.sync_api import Playwright, sync_playwright

from app.utils import (
    POPULATION_FOLDER,
    RAW_DATA_DIR,
    TABNET_URL_POPULATION,
    YEARS,
)


def run(
    playwright: Playwright,
    raw_data_dir: Path = RAW_DATA_DIR,
    years: range = YEARS,
) -> None:
    browser = playwright.chromium.launch(headless=False)
    failures: list[tuple[int, Exception]] = []

    try:
        context = browser.new_context()
        try:
            page = context.new_page()
            output_dir = raw_data_dir / POPULATION_FOLDER
            output_dir.mkdir(parents=True, exist_ok=True)

            for year in years:
                year_str = str(year)
                short_year = year_str[-2:]
                popup = None

                try:
                    print(f"Processando população para {year_str}...")
                    page.goto(TABNET_URL_POPULATION, timeout=60_000)

                    page.get_by_label("Linha", exact=True).select_option(
                        "Macrorregião_de_Saúde"
                    )
                    page.get_by_label("Coluna", exact=True).select_option(
                        "--Não-Ativa--"
                    )

                    page.locator("#fig2").click()
                    page.get_by_label("Unidade da Federação").select_option("5")

                    period_select = page.get_by_label("Períodos Disponíveis")
                    available_periods = {
                        option.get_attribute("value")
                        for option in period_select.locator("option").all()
                    }
                    period = f"pop{short_year}.dbf"

                    if period not in available_periods:
                        print(f"Sem dados disponíveis para {year_str}; ignorando.")
                        continue

                    period_select.select_option(period)
                    with page.expect_popup() as popup_info:
                        page.get_by_role("button", name="Mostra").click()
                    popup = popup_info.value

                    with popup.expect_download() as download_info:
                        popup.get_by_role("link", name="Copia como .CSV").click()
                    download = download_info.value

                    output_path = output_dir / f"{year_str}.csv"
                    download.save_as(output_path)
                    print(f"Salvo: {output_path}")
                except Exception as error:
                    failures.append((year, error))
                    print(f"Falha em {year_str}: {error}")
                finally:
                    if popup is not None:
                        popup.close()
        finally:
            context.close()
    finally:
        browser.close()

    if failures:
        failed_years = ", ".join(str(year) for year, _ in failures)
        raise RuntimeError(
            f"Falha na extração da população para os anos: {failed_years}"
        ) from failures[0][1]


def main() -> None:
    with sync_playwright() as playwright:
        run(playwright)


if __name__ == "__main__":
    main()
