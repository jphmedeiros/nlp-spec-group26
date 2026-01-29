"""
Propositions data extraction utilities.
"""

import pandas as pd
from .config import PROPOSITIONS_JSON
from .utils import generate_word_cloud
from .repository import insert_word_clouds_batch

import logging
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)


def load_propositions_dataset(propositions_json_path: str = PROPOSITIONS_JSON) -> Tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """
    Load propositions JSON and return authors series, filtered dataframe and full dataframe.

    Args:
        propositions_json_path: Path to the JSON file containing the propositions object.

    Returns:
        Tuple containing (df_authors, df_propositions_filtered, df_propositions).
    """
    df_propositions = pd.json_normalize(pd.read_json(propositions_json_path)["proposicoes"])
    df_authors = df_propositions["autores"]
    df_propositions_filtered = df_propositions.loc[:, ["id", "descricaoTipo", "dataApresentacao", "urlInteiroTeor", "autores"]]
    return df_authors, df_propositions_filtered, df_propositions


def extract_unique_authors(df_authors: pd.Series) -> List[Tuple[int, str, str, str]]:
    """
    Extract deduplicated authors from the authors series.

    Args:
        df_authors: Series where each element is a list/dict of authors for a proposition.

    Returns:
        List of tuples (idDeputadoAutor, nomeAutor, siglaPartidoAutor, siglaUFAutor).
    """
    authors_added: Dict[int, int] = {}
    authors: List[Tuple[int, str, str, str]] = []
    for i in range(0, df_authors.size):
        for j in range(0, len(df_authors.iloc[i])):
            idep = df_authors.iloc[i][j].get("idDeputadoAutor")
            name = df_authors.iloc[i][j].get("nomeAutor")
            party = df_authors.iloc[i][j].get("siglaPartidoAutor")
            uf = df_authors.iloc[i][j].get("siglaUFAutor")

            if idep and idep not in authors_added:
                authors_added[idep] = 1
                authors.append((idep, name, party, uf))

    return authors


def extract_propositions(df_propositions_filtered: pd.DataFrame) -> List[Tuple[int, str, str, Any, List[int]]]:
    """
    Build a list of propositions from a filtered DataFrame.

    Args:
        df_propositions_filtered: DataFrame with columns id, descricaoTipo, dataApresentacao, urlInteiroTeor, autores

    Returns:
        List of proposition tuples: (id, url_inteiro_teor, descricao_tipo, data_apresentacao, authors_ids)
    """
    propositions: List[Tuple[int, str, str, Any, List[int]]] = []

    for i in range(0, df_propositions_filtered["id"].size):
        idp = int(df_propositions_filtered.iloc[i]["id"])
        url = df_propositions_filtered.iloc[i]["urlInteiroTeor"]
        ptype = df_propositions_filtered.iloc[i]["descricaoTipo"]
        sub_date = df_propositions_filtered.iloc[i]["dataApresentacao"]

        authors: List[int] = []
        authors_added: Dict[int, int] = {}

        for j in range(0, len(df_propositions_filtered.iloc[i]["autores"])):
            idep = df_propositions_filtered.iloc[i]["autores"][j].get("idDeputadoAutor")

            if idep and idep not in authors_added:
                authors_added[idep] = 1
                authors.append(idep)

        propositions.append((idp, url, ptype, sub_date, authors))

    return propositions


def generate_and_insert_word_clouds(df_propositions: pd.DataFrame) -> None:
    """
    Generate and insert word clouds for each proposition in the dataframe.

    The dataframe is expected to contain columns `id` and `textoInteiroTeorLimpo`.

    Args:
        df_propositions: DataFrame with proposition data.
    """
    for i in range(0, df_propositions["id"].size):
        idp = df_propositions.iloc[i]["id"]
        text = df_propositions.iloc[i].get("textoInteiroTeorLimpo", "")
        word_cloud_to_insert = generate_word_cloud(idp, text)
        insert_word_clouds_batch(word_cloud_to_insert)
        logger.debug("Inserted word cloud for id %s", idp)
