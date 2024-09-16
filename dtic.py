import requests
import pandas as pd
import click
import os
import asyncio
import requests
from concurrent.futures import ThreadPoolExecutor
import re
from tqdm import tqdm

grants = []
researchers = []

BASE_URL = "https://dtic.dimensions.ai"

def get_organizations(search):
    response = requests.get(
        "https://dtic.dimensions.ai/completion/publication/research_org.json?query="
        + search
    )
    if response.status_code > 300:
        raise Exception(f"Got code {response.status_code}")

    results = response.json()["suggestions"]
    return results

def get_grants(uni_id: str, progress=None, path="/discover/grant/results.json", test=False):
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

    params = {
        "search_mode": "content",
        "search_type": "kws",
        "search_field": "full_search",
        "or_facet_research_org": uni_id,
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

    if test:
        return results['count']
    elif len(grants) >= results["count"]:
        progress.update(len(page_grants))
        return pd.DataFrame(grants)
    else:
        progress.update(len(page_grants))
        return get_grants(uni_id, progress, results["navigation"]["results_json"])


async def get_for(grant_id: str, executor, semaphore, loop, progress):
    async with semaphore:
        try:
            results = await loop.run_in_executor(
                executor,
                lambda: requests.get(
                    f"https://dtic.dimensions.ai/details/sources/grant/{grant_id}/for.json"
                ),
            )
            progress.update(1)
            # Multiple fields are often present, super super super annoying
            return ", ".join([r["details"]["name"] for r in results.json()["entities"]])
        except Exception as _:
            progress.update(1)
            return ''


async def clean_dataset(df: pd.DataFrame):
    df["researchers"] = df.apply(
        lambda row: ', '.join([f"{r["first_name"]} {r["last_name"]}" for r in row['researcher_details']] if not pd.isna(row["researcher_details"]) else ''),
        axis=1,
    )
    df["link"] = df.apply(lambda row: BASE_URL + row["navigation"]["path"], axis=1)

    # Get fields (like departments) -- can be multiple per grant
    loop = asyncio.get_event_loop()
    with tqdm(total=df.shape[0], desc='Grabbing fields', unit='grant') as progress:
        semaphore = asyncio.Semaphore(15)
        with ThreadPoolExecutor() as executor:
            tasks = [
                get_for(grant_id, executor, semaphore, loop, progress)
                for grant_id in df["id"].to_list()
            ]
            x = await asyncio.gather(*tasks)
            df["fields"] = x

    # Clean up dates
    df["start_date"] = df.apply(
        lambda row: (
            re.search("[0-9]{4}-[0-9]{2}-[0-9]{2}", row["start_date"]).group(0)
            if not pd.isna(row["start_date"])
            else None
        ),
        axis=1,
    )
    df["end_date"] = df.apply(
        lambda row: (
            re.search("[0-9]{4}-[0-9]{2}-[0-9]{2}", row["end_date"]).group(0)
            if not pd.isna(row["end_date"])
            else None
        ),
        axis=1,
    )

    return df[
        [
            "id",
            "title",
            "start_date",
            "end_date",
            "funding_amount",
            "researchers",
            "funding_org_name",
            "short_abstract",
            "fields",
            "link",
            "linkout"
        ]
    ]


@click.command()
@click.option("--uni", prompt="Your university", help="Please input your university")
def prompt(uni):
    universities = get_organizations(uni)
    for i, uni in enumerate(universities[:10]):
        click.echo(f"{i + 1}) {uni['data']['name']}")

    if len(universities) == 0:
        click.echo('No results found for your query, starting over.')
        prompt.main()
                
    selection = click.prompt(
        "Please select a university (1-10), or type 0 to start over", type=str
    ).lower()
    if selection == "0":
        prompt.main()

    if not selection.isnumeric():
        click.echo("Invalid selection; please start over.")
        prompt.main()

    if not int(float(selection)) in range(1, 11):
        click.echo("Invalid selection; please start over.")
        prompt.main()

    university = universities[int(float(selection)) - 1]
    click.echo(f"Got it, trying to fetch data for {university['data']['name']} now!")

    total_n = get_grants(university['data']['id'], None, '/discover/grant/results.json', True)
    with tqdm(total=total_n, desc='Fetching grants', unit='grant') as progress:
        df = get_grants(university["data"]["id"], progress)

    df = asyncio.run(clean_dataset(df))
    df.to_csv("grants.csv", index=False)
    click.echo()
    click.echo(
        f"Success! Saved data to 'grants.csv' in this directory ({os.getcwd()}) :)"
    )


if __name__ == "__main__":
    prompt()
