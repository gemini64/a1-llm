import requests, json
import urllib.parse
from random import sample

def fetch_pages_in_category(
    endpoint: str = "https://it.wikipedia.org", # the enpoint to query
    category_name: str = "Gatti", # a category name
    max_pages: int | None = None) -> list[str]: # an upper limit to fetched pages
    """Uses wikimedia API to get a **max_pages** number
    of page urls from a specific **category_name** category.

    Should work on any **endpoint** that implements the wikimedia
    query API."""
    # Base parameters for the API
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category_name}",
        "cmlimit": "max",  # Fetch the maximum allowed per request (500 for most users, 5000 for bots)
        "format": "json"
    }
    
    urls = []  # List to store the URLs
    total_fetched = 0  # Counter to track fetched pages

    while True:
        # API request
        response = requests.get(f"{endpoint}/w/api.php", params=params)
        data = response.json()
        
        # Extract pages
        pages = data.get("query", {}).get("categorymembers", [])
        for page in pages:
            # Construct URL for each page
            url = f"{endpoint}/wiki/{urllib.parse.quote(page['title'].replace(' ', '_'))}"
            urls.append(url)
            total_fetched += 1
            
            # Stop if max_pages limit is reached
            if max_pages and total_fetched >= max_pages:
                return urls
        
        # Check if there's more data to fetch
        if "continue" in data:
            params.update(data["continue"])
        else:
            break  # No more pages to fetch

    return urls

# --- flags
# output_file = "./pages.json" # output file path
# base_url = "https://it.wikipedia.org"
# max_pages = 250 # these are max_pages for EACH category supplied
# categories = [ "Voci_in_vetrina_su_it.wiki" ]

output_file = "./pages.json" # output file path
base_url = "https://it.wikinews.org"
max_pages = 25 # these are max_pages for EACH category supplied
categories = [
    "Ambiente",
    "Cultura_e_società",
    "Curiosità",
    "Disastri_e_incidenti",
    "Economia_e_finanza",
    "Giustizia_e_criminalità",
    "Politica_e_conflitti",
    "Scienza_e_tecnologia",
    "Trasporti",
    "Sport"
    ]

take_all = True # if True the max_pages value will be ignored during fetching and used to random sample results
remove_duplicates = True # if True, pages that have the same url are dropped
remove_hub_pages = True # if True, pages that represents a page hub are dropped

# --- fetch urls
pages = []

for category in categories:
    if (take_all):
        results = fetch_pages_in_category(endpoint=base_url, category_name=category, max_pages=None)
        n_samples = max(0, min(len(results),max_pages))

        results = sample(results, n_samples)
    else:
        results = fetch_pages_in_category(endpoint=base_url, category_name=category, max_pages=max_pages)

    pages.extend(results)

# --- apply filters
# remove duplicates
if (remove_duplicates):
    pages = list(set(pages))

# remove category pages
if (remove_hub_pages):
    pages = [ x for x in pages if ("/wiki/Portale:" not in x)] # wikinews hub pages


# --- write out
with open(output_file, "w", encoding="utf-8") as f_out:
    json.dump(pages, f_out, ensure_ascii=False)