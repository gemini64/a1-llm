import requests, json

###
# An Utility script that fetches Italian
# irregular verbs from Wikitionary
#
#   output -> a JSON string list
###

# --- flags
output_dir = "./inventories/"
output_file = "italian_irregular_verbs.json"
output_path = f"{output_dir}/{output_file}"

web_host = "https://en.wiktionary.org/w/api.php"
req_params = {
    "list": "categorymembers",
    "cmtitle": "Category:Italian_irregular_verbs",
    "cmtype": "page"
}

def query(request, host):
    """Recursively queries hosts that conform to wikimedia
    php web API specs. See also this for more info

    https://www.mediawiki.org/wiki/API:Continue"""
    request['action'] = 'query'
    request['format'] = 'json'
    last_continue = {}
    while True:
        # Clone original request
        req = request.copy()
        # Modify it with the values returned in the 'continue' section of the last result.
        req.update(last_continue)
        # Call API
        result = requests.get(host, params=req).json()
        if 'error' in result:
            raise Exception(result['error'])
        if 'warnings' in result:
            print(result['warnings'])
        if 'query' in result:
            yield result['query']
        if 'continue' not in result:
            break
        last_continue = result['continue']

# Query category pages
irregular_verbs = []
for result in query(req_params, web_host):
    pages = result["categorymembers"]

    for page in pages:
        irregular_verbs.append(page["title"])

# Write out data
with open(output_path, 'w', encoding='utf-8') as f_out:
    json.dump(irregular_verbs, f_out, ensure_ascii=False)