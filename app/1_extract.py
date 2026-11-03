from pathlib import Path

from playwright.sync_api import Playwright, sync_playwright

from app.utils import RAW_DATA_DIR, TABNET_URL, TABNET_CONTENTS, YEARS


def run(
    playwright: Playwright,
    raw_data_dir: Path = RAW_DATA_DIR,
    years: range = YEARS,
) -> None:
    browser = playwright.chromium.launch(headless=False)
    failures: list[tuple[str, int, Exception]] = []

    try:
        context = browser.new_context()
        try:
            page = context.new_page()

            for content, folder_name in TABNET_CONTENTS:
                output_dir = raw_data_dir / folder_name
                output_dir.mkdir(parents=True, exist_ok=True)
                print(f"\n--- Extraindo: {content} ---")

                for year in years:
                    year_str = str(year)
                    short_year = year_str[-2:]
                    popup = None

                    try:
                        print(f"Processando {year_str}...")
                        page.goto(TABNET_URL, timeout=60_000)
                        
                        # Cabeçalho
                        page.get_by_label("Linha", exact=True).select_option(
                            "Procedimento"
                        )
                        page.get_by_label("Coluna", exact=True).select_option("Macrorregião de Saúde")
                        page.get_by_label("Conteúdo").select_option(content)
                        
                        # Filtros
                        page.locator("#fig8").click()
                        page.get_by_label("Grupo procedimento").select_option("6")
                        page.locator("#fig9").click()
                        page.get_by_label("Subgrupo proced.").select_option("55")

                        periods = [
                            f"qaba{short_year}{month:02d}.dbf"
                            for month in range(12, 0, -1)
                        ]
                        period_select = page.get_by_label("Períodos Disponíveis")
                        available_periods = {
                            option.get_attribute("value")
                            for option in period_select.locator("option").all()
                        }
                        valid_periods = [
                            period
                            for period in periods
                            if period in available_periods
                        ]

                        if not valid_periods:
                            print(f"Sem dados disponíveis para {year_str}; ignorando.")
                            continue

                        period_select.select_option(valid_periods)
                        with page.expect_popup() as popup_info:
                            page.get_by_role("button", name="Mostra").click()
                        popup = popup_info.value
                        
                        alerta_sem_dados = popup.get_by_role("heading", name="Nenhum registro selecionado")
                        try:
                            alerta_sem_dados.wait_for(timeout=3000)
                            sem_dados = True
                        except Exception:
                            sem_dados = False
                        
                        if sem_dados:
                            print(f"Sem dados disponíveis para {year_str}; ignorando.")
                            popup.close()
                            continue

                        # Se não há mensagem de erro, segue com o fluxo de download
                        with popup.expect_download() as download_info:
                            popup.get_by_role("link", name="Copia como .CSV").click()
                        download = download_info.value
                        output_path = output_dir / f"{year_str}.csv"
                        download.save_as(output_path)
                        print(f"Salvo: {output_path}")
                    except Exception as error:
                        failures.append((content, year, error))
                        print(f"Falha em {content}, {year_str}: {error}")
                    finally:
                        if popup is not None:
                            popup.close()
        finally:
            context.close()
    finally:
        browser.close()

    if failures:
        failed_years = ", ".join(
            f"{content}/{year}" for content, year, _ in failures
        )
        raise RuntimeError(f"Falha na extração dos períodos: {failed_years}") from failures[0][2]


def main() -> None:
    with sync_playwright() as playwright:
        run(playwright)


if __name__ == "__main__":
    main()
