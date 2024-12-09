import requests, os, json

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

output_file = "./italian_irregular_verbs.json"

web_host = "https://en.wiktionary.org/w/api.php"
req_params = {
    "list": "categorymembers",
    "cmtitle": "Category:Italian_irregular_verbs",
    "cmtype": "page"
}

irregular_verbs = []
for result in query(req_params, web_host):
    pages = result["categorymembers"]

    for page in pages:
        irregular_verbs.append(page["title"])

with open(output_file, 'w', encoding='utf-8') as f_out:
    json.dump(irregular_verbs, f_out, ensure_ascii=False)