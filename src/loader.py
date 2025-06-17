import pandas as pd

# Lista fixa de abas a carregar
SHEETS = ["bronze", "prata", "ouro", "platina", "rubi", "esmeralda", "diamante"]

def load_sheets(filepath: str) -> dict[str, pd.DataFrame]:
    """
    Carrega as colunas A:C de cada aba especificada e garante que 'ValorLiquido' seja float.
    Retorna um dicionário {nome_aba: DataFrame}.
    """
    # Leitura: já trata decimal=',' e milhares='.' para não remover o ponto decimal
    raw = pd.read_excel(
        filepath,
        sheet_name=SHEETS,
        usecols="A:C",
        names=["segmentacao", "ValorLiquido", "PlanoPagamento"],
        header=0,
        dtype={"segmentacao": str, "PlanoPagamento": str},
        decimal=",",
        thousands="."
    )

    # Converte cada DataFrame individualmente
    for name, df in raw.items():
        df["ValorLiquido"] = pd.to_numeric(df["ValorLiquido"], errors="coerce").fillna(0.0)
        raw[name] = df

    return raw
