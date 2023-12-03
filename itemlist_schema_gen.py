from bs4 import BeautifulSoup
import requests
import json
import streamlit as st
import pandas as pd

def generate_itemlist(url):
    try:
        r = requests.get(url)
        r.raise_for_status()  # Raises a HTTPError if one occurred
    except requests.exceptions.HTTPError as errh:
        st.error(f"HTTP Error occurred: {errh}")
        return None
    except requests.exceptions.ConnectionError as errc:
        st.error(f"Error Connecting: {errc}")
        return None
    except requests.exceptions.Timeout as errt:
        st.error(f"Timeout Error: {errt}")
        return None
    except requests.exceptions.RequestException as err:
        st.error(f"Unknown error occurred: {err}")
        return None

    soup = BeautifulSoup(r.content, 'html.parser')

    # Find the anchorViewer elements
    anchors = soup.find_all('a', {'data-hook': 'anchorViewer'})

    if not anchors:
        st.error(f"No anchorViewer elements found in the page: {url}")
        return None

    itemList = []
    for i, anchor in enumerate(anchors, start=1):
        item_url = url + anchor['href']
        item_name = anchor.get_text()
        itemList.append({
            "@type": "ListItem",
            "position": i,
            "name": item_name,
            "url": item_url,
        })
    return itemList
def generate_itemlist_jsonld(url, itemList):
    schema = {
        '@context': 'https://schema.org',
        '@type': 'ItemList',
        'itemListElement': itemList
    }
    jsonld = json.dumps(schema, indent=4)
    return f'<script type="application/ld+json">\n{jsonld}\n</script>'


@st.cache
def generate_schemas(urls):
    schema_data = []

    for url in urls:
        url = url.strip()  # remove leading/trailing white spaces
        if not url:
            st.error("Empty URL provided. Skipping.")
            continue
        itemList = generate_itemlist(url)
        if itemList is not None:
            jsonld = generate_itemlist_jsonld(url, itemList)
            schema_data.append([url, jsonld])
    
    return pd.DataFrame(schema_data, columns=['Blog URL', 'Schema'])

st.title("JSON-LD ItemList Schema Generator for Wix Blogs")

# User inputs
urls = st.text_area("Enter the list of blog URLs (one per line):")

# Generate JSON-LD for each URL
if st.button('Generate JSON-LD'):
    urls = urls.splitlines()
    if not urls or all(not url.strip() for url in urls):
        st.error("No URL provided.")
    else:
        schema_df = generate_schemas(urls)

        csv = schema_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Schemas as CSV",
            data=csv,
            file_name='schemas.csv',
            mime='text/csv',
        )
