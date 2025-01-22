import os, re, requests, json, spacy
from time import sleep
from bs4 import BeautifulSoup
import pandas as pd

def strip_quotes(input: str) -> str:
    """Takes a string and uses regex pattern matching
    to remove wikipedia style quotes."""
    text = input
    text = re.sub(r'\[\d+\]', '', text)  # Remove reference numbers
    text = re.sub(r'\s+', ' ', text)      # Normalize whitespace
    
    return text.strip()

def get_wiki_page_summary(url: str) -> str | None:
    """Given a wikipedia **url**, fetches the content of the
    article summary.
    
    _Note:_ Only text from p elements is returned"""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Get first p element
    pointer = soup.find("p")
    pars = []

    # append all direct p siblings
    while pointer.find_next_sibling() != None:
        if pointer.name == "p":
            pars.append(pointer.get_text()) # extract unformatted text
            pointer = pointer.next_sibling
        else:
            break

    # remove empty paragraphs
    pars = [ x for x in pars if x.strip()]

    # strip quote symbols
    pars = [ strip_quotes(x) for x in pars ]

    # return 
    return "\n\n".join(pars)

def crawl_wiki_pages(
    base_urls: list[str]) -> pd.DataFrame:
    """Crawls multiple Wikipedia pages and returns their summaries
    in a pandas DataFrame."""
    dataset = []
    
    for url in base_urls:
        try:
            content = get_wiki_page_summary(url)
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
    (or exceeds) a minimum words limit."""
    words = 0
    nlp = spacy.load("it_core_news_lg") # we also expect Italian text

    # split into paragraphs
    # Note: we expect that paragraphs are separated by double newlines
    pars = input.split("\n\n")
    results = []

    for par in pars:

        # exit if min_words is reached
        if (words >= min_words):
            break

        par_w = len(par.split())
        
        if (words + par_w < min_words):
            results.append(par)
            words += par_w
        else:
            par_r = []
            sentences = [x for x in nlp(par).sents]

            for sent in sentences:

                text = sent.text
                sent_w = len(text.split())

                if (words < min_words):
                    par_r.append(text)
                    words += sent_w
                else:
                    break

            results.append(" ".join(par_r))

    return "\n\n".join(results)

# --- flags
output_file = "./output.tsv"
input_file = "./pages_wikipedia.json" # a list of links to crawl

cut_sentences = True # set to True to cut summary to the last sentence that matches (or exceeds) min_words
min_words = 40 # minimum words a summary should contain

# read urls
pages = []
with open(input_file, "r", encoding='utf-8') as f_in:
    pages = json.load(f_in)

# build dataframe
df = crawl_wiki_pages(base_urls=pages)

# --- apply filters
# drop rows with < min_words
if (not df.empty and min_words):
    df = df[df['length'] >= min_words]

# cut sentences
if (not df.empty and cut_sentences):
    df['text'] = df['text'].map(lambda x: spacy_cut_text(input=x, min_words=min_words))
    df['length'] = df['text'].map(lambda x: len(x.split())) # recalculate word counts

# --- output data
df.to_csv(output_file ,encoding="utf-8", sep="\t", index=False)