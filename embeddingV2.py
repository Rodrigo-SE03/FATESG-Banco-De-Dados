import os, re, math
import wikipedia
from together import Together
from dotenv import load_dotenv
from mongo import get_collection 
import tiktoken

collection = get_collection()

# ---------- Config ----------------------------------------------------------
load_dotenv(override=True)
TOGETHER_KEY = os.getenv("TOGETHER_KEY")
MODEL_EMB = "togethercomputer/m2-bert-80M-8k-retrieval"
CHUNK_TOKENS = 100
OVERLAP_TOKENS = 20

client = Together(api_key=TOGETHER_KEY)
wikipedia.set_lang("pt")
enc = tiktoken.get_encoding("cl100k_base")          # mesmo tokenizer usado no modelo

# ---------- Utilidades ------------------------------------------------------
def n_tokens(text: str) -> int:
    return len(enc.encode(text))

# def chunk_text(text: str,
#                max_tokens: int = CHUNK_TOKENS,
#                overlap: int = OVERLAP_TOKENS):
#     words = text.split()
#     chunks, buf = [], []

#     buf_tokens = 0
#     for w in words:
#         tok_len = n_tokens(w)  # em média é 1, mas garante p/ emojis etc.
#         if buf_tokens + tok_len > max_tokens:
#             chunks.append(" ".join(buf))
#             # cria overlap
#             overlap_words = buf[-overlap:] if overlap else []
#             buf = overlap_words + [w]
#             buf_tokens = n_tokens(" ".join(buf))
#         else:
#             buf.append(w)
#             buf_tokens += tok_len

#     if buf:
#         chunks.append(" ".join(buf))
#     return chunks

def split_sections(raw: str):
    """
    Separa o conteúdo baseado nos cabeçalhos '==', '===' da MediaWiki.
    Retorna lista de (heading, body).
    """
    pattern = re.compile(r"(==+)\s*(.*?)\s*\1")
    sections = []
    last_idx = 0
    last_title = "Introdução"

    for m in pattern.finditer(raw):
        body = raw[last_idx:m.start()].strip()
        sections.append((last_title, body))
        last_title = m.group(2).strip()
        last_idx = m.end()

    # última seção
    sections.append((last_title, raw[last_idx:].strip()))
    return sections

# ---------- Pipeline principal ---------------------------------------------
def wiki_chunks(title: str):
    """
    Para cada seção da página da Wikipédia:
    - Divide em chunks com overlap
    - Prefixa com "Título - Seção"
    - Retorna lista de chunks prontos para embedding
    """
    page = wikipedia.page(title)
    sections = split_sections(page.content)

    all_chunks = []
    for sec_title, sec_body in sections:
        if not sec_body.strip():
            continue
        full_text = f"{title} - {sec_title}\n\n{sec_body.strip()}"
        all_chunks.append(full_text)
    return all_chunks


def embed_chunks(chunks):
    """
    Recebe um iterável de strings, devolve lista de dicts:
    [{text, embedding}]
    """
    # modelo aceita batching: aproveite para economizar chamadas
    batch_size = 32
    result = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        resp = client.embeddings.create(model=MODEL_EMB, input=batch)
        for text, emb in zip(batch, resp.data):
            result.append({"text": text, "embedding": emb.embedding})

    return result

def process_title(title: str):
    print(f"🔎  Buscando “{title}” na Wikipédia PT…")
    chunks = wiki_chunks(title)
    print(f"• {len(chunks)} chunks gerados (~{round(sum(map(n_tokens, chunks))/len(chunks))} tokens cada)")

    print("🧠  Enviando para Together…")
    items = embed_chunks(chunks)
    print("✅  Embeddings prontos!")

    # --- grava em MongoDB, se desejar ---
    collection.insert_many(items)

    return items

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Exemplo de uso
    paginas = ["Linkin Park","Luan Santana","System of a Down","Chico Buarque","Skrillex","Skillet","Anitta"]
    for title in paginas:
        print(title)
        data = process_title(title)
