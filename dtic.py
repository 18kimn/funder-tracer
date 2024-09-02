import requests
import pandas as pd

BASE_URL = "https://dtic.dimensions.ai"
params = {
    "search_mode": "content",
    "search_type": "kws",
    "search_field": "full_search",
    "or_facet_research_org": "grid.214458.e",
}


grants = []
researchers = []


def get_page(path="/discover/grant/results.json"):
    """
    Grabs grants data from DTIC Dimensions API, unauthenticated/undocumented/not allowed/etc
    There can be several researchers per grant, hence why it is extracted and processed into its own dataframe

    The parameters above are important -- they tell whatever backend is handling this to
    search only for our org and how to do it -- and that matches roughyl how the DTIC Dimensions
    UI does it. The `or_facet_research_org` parameter was obtained by just messing around
    with the interface, but I wonder if we can make a separate function to grab that as
    well.

    Recursive because the URL for the subsequent call is obtained from the previous call
    """
    print(f"Trying {path}...")

    response = requests.get(BASE_URL + path, params)

    if response.status_code > 300:
        raise Exception(f"Got code {response.status_code}")

    results = response.json()
    page_grants = results["docs"]
    for grant in page_grants:
        if not "researcher_details" in grant.keys():
            continue
        for researcher in grant["researcher_details"]:
            researcher["grant_id"] = grant["id"]
        researchers.extend(grant["researcher_details"])

    grants.extend(page_grants)
    if len(grants) >= results["count"]:
        pd.DataFrame(grants).to_csv("results/grants.csv", index=False)
        pd.DataFrame(researchers).to_csv("results/researchers.csv", index=False)
    else:
        print(f"Grabbed {len(grants)}/{results["count"]} grants so far.")
        get_page(results["navigation"]["results_json"])


get_page()
