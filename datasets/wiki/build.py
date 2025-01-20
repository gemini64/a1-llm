import os, re, requests, json, spacy
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep

def strip_wiki_quotes(input: str) -> str:
    """Takes a string and uses regex pattern matching
    to remove wikipedia style quotes."""
    text = input
    text = re.sub(r'\[\d+\]', '', text)  # Remove reference numbers
    text = re.sub(r'\s+', ' ', text)      # Normalize whitespace
    
    return text.strip()

def get_wiki_page_content(url: str) -> str | None:
    """Given a wikipedia url, fetches the content of the
    article summary."""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Parse data
    pointer = soup.find("p")
    pars = []

    while pointer.find_next_sibling() != None:
        if pointer.name == "p":
            pars.append(pointer.get_text())
            pointer = pointer.next_sibling
        else:
            break

    # remove empty paragraphs
    pars = [ x for x in pars if x.strip()]

    # sanitize content
    pars = [ strip_wiki_quotes(x) for x in pars ]

    return " ".join(pars)

def crawl_wiki_pages(
    base_urls: list[str]) -> pd.DataFrame:
    """Crawls multiple Wikipedia pages and returns their content
    in a pandas DataFrame."""
    dataset = []
    
    for url in base_urls:
        try:
            content = get_wiki_page_content(url)
            if content:
                dataset.append({
                    'url': url,
                    'text': content,
                    'length': len(content.split())
                })
            sleep(1)  # Be nice to Wikipedia servers
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
    
    # return pandas dataframe
    df = pd.DataFrame(dataset)
    return df

def spacy_cut_text(input: str, min_words: int = 10) -> str:
    """Cuts a text to the last sentence that matches
    a minimum words limit."""
    nlp = spacy.load("it_core_news_lg")
    sentences = [x for x in nlp(input).sents]

    for sent in sentences:
        text = sent.text
        sent_w = len(text.split())

        if ( words < min_words):
            results.append(text)
            words += sent_w
        else:
            break

    return " ".join(results)    

# --- flags
output_file = "./output.tsv"
input_file = "./pages.json"

cut_sentences = True
min_words = 45

pages = []
with open(input_file, "r", encoding='utf-8') as f_in:
    pages = json.load(f_in)

df = crawl_wiki_pages(base_urls=pages)

# drop rows with < min_words
if (min_words):
    df = df[df['length'] >= min_words]

# cut sentences
if (cut_sentences):
    df['text'] = df['text'].map(lambda x: spacy_cut_text(input=x, min_words=min_words))
    df['length'] = df['text'].map(lambda x: len(x.split()))

df.to_csv(output_file ,encoding="utf-8", sep="\t", index=False)