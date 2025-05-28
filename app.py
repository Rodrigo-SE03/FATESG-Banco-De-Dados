import chainlit as cl
from embeddingV2 import embed_chunks        # mesma função usada no pré‑processo
from mongo import get_collection                # sua conexão PyMongo
from dotenv import load_dotenv
from together import Together
import os

load_dotenv(override=True)


TOGETHER_KEY = os.getenv("TOGETHER_KEY")
client = Together(api_key=TOGETHER_KEY)
collection = get_collection()
# ------------------------------------------------------
# Utilitário: gera embedding 1×1 (retorna lista[dict])
def embed_query(text: str):
    return embed_chunks([text])[0]["embedding"]

# ------------------------------------------------------

# Função para reranking via Together API
def rerank_together(query: str, candidates: list[str]):
    response = client.rerank.create(
        model="Salesforce/Llama-Rank-V1",
        query=query,
        documents=candidates
    ).results
    # Reordena com base no relevance_score e recupera texto original
    reranked = sorted(response, key=lambda x: x.relevance_score, reverse=True)

    # Retorna lista de (relevance_score, candidate_text)
    return [(r.relevance_score, candidates[r.index]) for r in reranked]

# ------------------------------------------------------

@cl.on_message
async def main(message: cl.Message):
    # 1) vetor da pergunta
    query_text = message.content
    query_vec = embed_query(query_text)

    # 2) busca vetorial (top‑5)
    pipeline_search  = [
        {
            "$vectorSearch": {
                "queryVector": query_vec,
                "path": "embedding",
                "numCandidates": 100,
                "limit": 5,
                "index": "default"
            }
        },
        {"$project": {"_id": 0, "text": 1, "score": {"$meta": "vectorSearchScore"}}}
    ]
    hits = list(collection.aggregate(pipeline_search))

    if not hits:
        await cl.Message(content="Nenhum resultado encontrado.").send()
        return

    candidate_texts = [hit["text"][:2000] for hit in hits]  # Trunca cada texto para evitar erro de token
    reranked = rerank_together(query_text, candidate_texts)

    # 4) monta resposta
    score, resposta_texto = reranked[0]
    resposta = f"Score (reranked): {score:.4f}\n\n{resposta_texto}"

    await cl.Message(content=resposta).send()
