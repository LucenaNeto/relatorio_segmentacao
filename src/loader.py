import pandas as pd

# Lista fixa de abas a carregar (lowercase)
SHEETS = ["bronze", "prata", "ouro", "platina", "rubi", "esmeralda", "diamante"]


def load_sheets(filepath: str) -> dict[str, pd.DataFrame]:
    """
    Carrega as colunas A:C somente das abas definidas em SHEETS, caso existam no arquivo.
    Trata decimal e milhares corretamente e normaliza nomes das abas para lowercase.
    Retorna um dicionário {nome_aba_lowercase: DataFrame}.
    """
    # 1) Descobre abas disponíveis
    xls = pd.ExcelFile(filepath)
    available = xls.sheet_names
    print(f"Abas disponíveis em '{filepath}': {available}")  # debug

    # 2) Mapeamento lowercase -> original
    sheet_map = {name.lower(): name for name in available}
    # 3) Seleciona apenas as abas que realmente existem e interesse
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

    # 5) Converte ValorLiquido para float e normaliza colunas como string
    result = {}
    for actual_name, df in raw.items():
        df["ValorLiquido"] = pd.to_numeric(df["ValorLiquido"], errors="coerce").fillna(0.0)
        df["segmentacao"] = df["segmentacao"].astype(str)
        df["PlanoPagamento"] = df["PlanoPagamento"].astype(str)
        result[actual_name.lower()] = df

    return result
