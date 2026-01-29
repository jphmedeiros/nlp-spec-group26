import time
import logging
from typing import List, Tuple, Any, Optional
from pydantic import BaseModel
from .repository import insert_proposition_summaries_batch, insert_proposition_entities_batch, insert_proposition_topics_batch
import concurrent.futures

logger = logging.getLogger(__name__)


class ResponseSchema(BaseModel):
    """
    Pydantic model representing expected structured response from the LLM.
    """
    text_summary: str
    main_theme: str
    entities: List[List[str]]
    sentiment: str
    ideology: str

    class Config:
        schema_extra = {
            "examples": [
                {
                    "text_summary": "Summary in up to 50 words.",
                    "main_theme": "Main theme up to 10 words.",
                    "entities": [["date", "06 Nov 2025"], ["person", "Joao"]],
                    "sentiment": "neutral",
                    "ideology": "center"
                }
            ]
        }


def generate_proposition_summary_and_entities(client: Any, proposition_id: int, full_text: str) -> Tuple[List[Tuple], List[Tuple]]:
    """
    Call the LLM to generate a summary and named entities for a single proposition.

    Returns a tuple of (summaries_list, entities_list). Each is a list of tuples ready for DB insertion.
    """
    try:
        start = time.time()
        response = client.responses.parse(
            model="gpt-5-nano",
            input=[
                {"role": "developer", "content":
                 """
                 Você é um chatbot especialista em processamento de linguagem natural.
                
                 Regras:
                 1. O tema principal deve ser representado em no máximo 10 palavras.
                 2. O resumo do texto deve ter no máximo 50 palavras.
                 3. Cada item de entities é um par com tipo da entidade nomeada e seu valor, por exemplo: 
                     - ['data', '06 de nov. de 2025']
                 4. classifique o sentimento do texto em 7 nuances:
                     - extremamente-positivo, positivo, positivo-neutro, neutro, negativo-neutro, negativo, extremamente-negativo
                 5. classifique o em uma das 7 seguintes ideologias:
                     - extrema-esquerda, esquerda, centro-esquerda, centro, centro-direita, direita, extrema-direita
                
                 Revise o conteúdo gerado e corrija se necessário.
                 """
                },
                {
                    "role": "user",
                    "content": [
                        {  
                            "type": "input_text",  
                            "text": f"""
                                Execute a seguinte sequência de passos.
                               
                                1. Faça resumo do texto.
                                2. Identifique o tema principal
                                3. Faça um reconhecimento de entidades nomeadas (NER).
                                4. Classifique o sentimento do texto.
                                5. Classifique a ideologia do texto.
                               
                                texto: {full_text}
                            """
                        },
                    ]
                }
            ],
            text_format=ResponseSchema
        )

        logger.info("API call for ID %d took: %.2fs", proposition_id, time.time() - start)

        parsed = response.to_dict().get("output")[1].get("content")[0].get("parsed")

        summaries = [(
            int(proposition_id),
            parsed.get("text_summary"),
            parsed.get("main_theme"),
            parsed.get("sentiment"),
            parsed.get("ideology"),
        )]

        entities = [
            (int(proposition_id), entity[0], entity[1])
            for entity in parsed.get("entities", [])
        ]

        return summaries, entities

    except Exception:
        logger.exception("Error processing proposition id %d", proposition_id)
        return [], []


def process_propositions_in_parallel(client: Any, df_propositions: Any, max_workers: int = 10) -> None:
    """
    Process a batch of propositions in parallel using threads to call the LLM.

    Args:
        client: OpenAI client instance.
        df_propositions: DataFrame with propositions and text column `textoInteiroTeorLimpo`.
        max_workers: Number of thread workers.
    """

    all_summaries = []
    all_entities = []
    new_processed_ids = set()

    ids = df_propositions['id'].tolist()
    texts = df_propositions['textoInteiroTeorLimpo'].tolist()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(lambda args: generate_proposition_summary_and_entities(client, *args), zip(ids, texts))

        for i, (summaries, entities) in enumerate(results):
            current_id = ids[i]
            if summaries and entities:
                all_summaries.extend(summaries)
                all_entities.extend(entities)
                new_processed_ids.add(current_id)
                logger.debug("Processed index %d, id %d", i, current_id)
            else:
                logger.warning("Failed to process proposition id: %d", current_id)

    if all_summaries:
        logger.info(f"Inserting {len(all_summaries)} summaries into the database...")
        insert_proposition_summaries_batch(all_summaries)

    if all_entities:
        logger.info(f"Inserting {len(all_entities)} entities into the database...")
        insert_proposition_entities_batch(all_entities)

    logger.info(f"Successfully processed and updated {len(new_processed_ids)} propositions.")


class ResponseSchemaClassification(BaseModel):
    """
    Pydantic schema for the classification response returned by the LLM.

    Fields:
        topic: the selected topic (one of the allowed topics).
    """
    topic: str

    class Config:
        schema_extra = {
            "examples": [
                {
                    "topic": "Saúde Pública",
                }
            ]
        }


TOPICS: List[str] = [
    "Administração Pública", "Direitos Humanos e Minorias", "Segurança Pública",
    "Defesa Nacional", "Finanças e Orçamento", "Tributação e Reforma Tributária",
    "Saúde Pública", "Educação", "Previdência Social", "Assistência Social",
    "Trabalho e Emprego", "Desenvolvimento Regional", "Infraestrutura e Logística",
    "Transporte", "Energia e Recursos Naturais", "Meio Ambiente e Sustentabilidade",
    "Mudanças Climáticas", "Agricultura, Pecuária e Extrativismo",
    "Ciência, Tecnologia e Inovação", "Comunicações",
    "Proteção de Dados e Segurança Digital", "Regulação de Inteligência Artificial",
    "Cultura", "Esporte", "Habilitação", "Urbanismo",
    "Justiça e Sistema Judiciário", "Combate à Violência Doméstica",
    "Direitos das Pessoas com Deficiência",
    "Políticas para Povos Indígenas e Comunidades Tradicionais"
]


def classify_and_store_proposition_topics(client: Any,
                                         propositions: List[Tuple[int, str]],
                                         max_workers: int = 8,
                                         batch_insert: bool = True) -> None:
    """
    Classify a list of propositions in parallel using the LLM and store results in the DB.

    Args:
        client: OpenAI client instance (expected to support client.responses.parse).
        propositions: List of tuples (proposition_id, full_text).
        max_workers: Number of threads used for parallel classification.
        batch_insert: If True, perform a single batch insert at the end; otherwise insert per item.
    """

    rows: List[Tuple[int, str, float]] = []

    def classify_one(proposition_id: int, text: str) -> Optional[Tuple[int, str]]:
        """
        Call the LLM to classify a single proposition. Returns a tuple for DB insertion
        or None if classification failed.
        """
        try:
            # Provide the Pydantic model as the text_format so the API can validate/generate according to schema
            response = client.responses.parse(
                model="gpt-5-nano",
                input=[
                    {"role": "developer", "content":
                    """
                    Você é um chatbot especialista em processamento de linguagem natural.
                    """
                    },
                    {
                        "role": "user",
                        "content": [
                            {  
                                "type": "input_text",  
                                "text": f"""
                                    Classifique a proposição em exatamente um dos seguintes topicos. 
                        
                                    topicos: {TOPICS}

                                    proposição: {text}
                                """
                            },
                        ]
                    }
                ],
                text_format=ResponseSchemaClassification
            )

            parsed = response.to_dict().get("output")[1].get("content")[0].get("parsed")

            topic = parsed.get("topic")
            logger.info("Classified ID %s as '%s'", proposition_id, topic)
            return int(proposition_id), topic
        except Exception as exc:
            logger.exception("Error classifying proposition ID %s: %s", proposition_id, exc)
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {
            executor.submit(classify_one, prop_id, text): prop_id
            for prop_id, text in propositions
        }
        for fut in concurrent.futures.as_completed(future_to_id):
            pid = future_to_id[fut]
            try:
                result = fut.result()
                if result:
                    if batch_insert:
                        rows.append(result)
                    else:
                        # insert immediately
                        insert_proposition_topics_batch([result])
                        logger.info("Inserted classified topic for ID %s", pid)
            except Exception as exc:
                logger.exception("Unhandled error when classifying ID %s: %s", pid, exc)

    if batch_insert and rows:
        try:
            insert_proposition_topics_batch(rows)
            logger.info("Inserted %d classified proposition topics.", len(rows))
        except Exception:
            logger.exception("Failed to insert classified proposition topics batch.")
