import pandas as pd

# Lista fixa de abas a carregar (lowercase)
SHEETS = ["bronze", "prata", "ouro", "platina", "rubi", "esmeralda", "diamante"]


def load_sheets(filepath: str) -> dict[str, pd.DataFrame]:
    """
    Carrega as colunas A:C somente das abas definidas em SHEETS, caso existam no arquivo.
    Trata decimal e milhares corretamente e normaliza nomes das abas e dados (remove espaços extras).
    Retorna um dicionário {nome_aba_lowercase: DataFrame}.
    """
    # 1) Descobre abas disponíveis
    xls = pd.ExcelFile(filepath)
    available = xls.sheet_names
    print(f"Abas disponíveis em '{filepath}': {available}")  # debug

    # 2) Mapeamento lowercase -> original (strip de espaços)
    sheet_map = {name.strip().lower(): name for name in available}
    # 3) Seleciona apenas as abas que realmente existem e são de interesse
    wanted = [sheet_map[s] for s in SHEETS if s in sheet_map]
    if not wanted:
        raise ValueError(
            f"Nenhuma das abas {SHEETS} foi encontrada em '{filepath}'. "
            f"Abas disponíveis: {available}"
        )

    # 4) Leitura das abas selecionadas, tratando decimal e milhares
    raw = pd.read_excel(
        filepath,
        sheet_name=wanted,
        usecols="A:C",
        names=["segmentacao", "ValorLiquido", "PlanoPagamento"],
        header=0,
        dtype={"segmentacao": str, "PlanoPagamento": str},
        decimal=",",
        thousands="."
    )

    # 5) Processa cada DataFrame: converte tipos e normaliza strings
    result = {}
    for actual_name, df in raw.items():
        # converte ValorLiquido para float
        df["ValorLiquido"] = pd.to_numeric(df["ValorLiquido"], errors="coerce").fillna(0.0)

        # strip em colunas de texto
        df["segmentacao"] = df["segmentacao"].str.strip()
        df["PlanoPagamento"] = df["PlanoPagamento"].str.strip()

        # strip em cabeçalhos
        df.columns = df.columns.str.strip()

        # adiciona ao resultado com chave lowercase e sem espaços
        result[actual_name.strip().lower()] = df

    return result
