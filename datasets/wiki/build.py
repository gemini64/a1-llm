import os, re, requests, json
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

def get_wiki_page_content(url: str, n_pars: int = 1) -> str | None:
    """Given a wikipedia url, fetches the content of the
    article summary. Returns a **n_pars** number of paragraphs
    from the article summary."""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Parse data
    pointer = soup.find("p")
    print(pointer)
    pars = []

    while pointer.find_next_sibling() != None:
        if pointer.name == "p":
            pars.append(pointer.get_text())
            pointer = pointer.next_sibling
        else:
            break

    # remove empty paragraphs
    pars = [x for x in pars if x.strip()]

    # sanitize content
    pars = [ strip_wiki_quotes(x) for x in pars ]

    samples = max(0, min(n_pars, len(pars)-1))
    return None if samples == 0 else "\n\n".join(pars[:samples])

def crawl_wiki_pages(
    base_urls: list[str],
    n_pars: int = 1) -> pd.DataFrame:
    """Crawls multiple Wikipedia pages and returns their content
    in a pandas DataFrame."""
    dataset = []
    
    for url in base_urls:
        try:
            content = get_wiki_page_content(url, n_pars)
            if content and len(content.split()) > 10:  # Ensure minimum content length
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

# --- flags
output_file = "./output.tsv"
input_file = "./pages.json"

pages = []
with open(input_file, "r", encoding='utf-8') as f_in:
    pages = json.load(f_in)

df = crawl_wiki_pages(base_urls=pages)
df.to_csv(output_file ,encoding="utf-8", sep="\t", index=False)