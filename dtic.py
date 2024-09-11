import requests
import pandas as pd
import click
import os

grants = []
researchers = []


def get_organizations(search):
    response = requests.get('https://dtic.dimensions.ai/completion/publication/research_org.json?query=' + search)
    if response.status_code > 300:
        raise Exception(f"Got code {response.status_code}")

    results = response.json()["suggestions"]
    return results

def get_page(uni_id: str, path="/discover/grant/results.json"):
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
        
    BASE_URL = "https://dtic.dimensions.ai"
    params = {
        "search_mode": "content",
        "search_type": "kws",
        "search_field": "full_search",
        "or_facet_research_org": uni_id
    }

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
        pd.DataFrame(grants).to_csv("grants.csv", index=False)
        pd.DataFrame(researchers).to_csv("researchers.csv", index=False)
        click.echo(f"Saved data to 'grants.csv' in this directory ({os.getcwd()}) :)")
    else:
        print(f"Grabbed {len(grants)}/{results["count"]} grants so far.")
        get_page(uni_id, results["navigation"]["results_json"])



@click.command()
@click.option('--uni', prompt='Your university', help='Please input your university')
def prompt(uni):
    universities = get_organizations(uni)
    for i, uni in enumerate(universities[:10]):
        click.echo(f"{i + 1}) {uni['data']['name']}")

    selection = click.prompt("Please select a university (1-10), or type 0 to start over", type=str).lower()
    if selection == '0':
        prompt.main()
        
    if not selection.isnumeric():
        click.echo('Invalid selection; please start over.')
        prompt.main()
    
    if not int(float(selection)) in range(1, 10):
        click.echo('Invalid selection; please start over.')
        prompt.main()
        
    university = universities[int(float(selection)) - 1]
    click.echo(f'Got it, trying to fetch data for {university['data']['name']} now!')
    get_page(university['data']['id'])
    
if __name__ == '__main__':
    prompt()
