from together import Together
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import tiktoken
#from mongo import collection
import os
import re

import wikipedia

load_dotenv(override=True)
TOGETHER_KEY = os.getenv("TOGETHER_KEY")

client = Together(api_key=TOGETHER_KEY)
wikipedia.set_lang("pt")

enc = tiktoken.get_encoding("cl100k_base")


def divide_text_into_sections(text):
    section_pattern = re.compile(r"(==+)(.*?)\1")  # Captura títulos de seções
    sections = []

    # Procurar todas as seções
    for match in section_pattern.finditer(text):
        section_title = match.group(2).strip()  # título da seção
        section_content = text[match.end():]  # Conteúdo após o título da seção
        # Procurar próximo título de seção para pegar o conteúdo da seção corretamente
        next_match = section_pattern.search(section_content)
        if next_match:
            section_content = section_content[:next_match.start()]  # pega conteúdo até o próximo título
        sections.append({'title': section_title, 'content': section_content.strip()})

    return sections

def search_wiki(title):
    print("Buscando no Wikipedia")
    wiki = wikipedia.page(title)
    seq = divide_text_into_sections(wiki.content)
    for s in seq:
        print(s)
    # wiki_search = wiki.replace("{{title}}", title)
    # response = requests.get(wiki_search)
    # response = response.json()['query']['pages']
    # for r in response.values():
    #     for l in r['revisions']:
    #         for s in l['slots']:
    #             if 'main' in s:
    #                 content = l['slots'][s]['*']
    #                 text = treat_text(content).split('\n')
    #                 return [t for t in text if t.strip() != '']
                

def embbed(text):
    response = client.embeddings.create(
      model = "togethercomputer/m2-bert-80M-8k-retrieval",
      input = text
    ) 
    return response.data


def create_embedding(title):
    text = search_wiki(title)
    text = [t for t in text if t.strip() != '']
    if text:
        embedding = embbed(text)
        return embedding, text
    else:
        print(f"Não foi possível encontrar o título: {title}")
        return None, None

def get_embedding(title):
    embbedings, text = create_embedding(title)
    return
    for i, embbed in enumerate(embbedings):
        collection.insert_one({
            'text': text[i],
            'embedding': embbed.embedding
        })
        

get_embedding('Linkin Park')