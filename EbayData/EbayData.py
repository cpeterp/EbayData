from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
import time
import json
import warnings

def scraper(query_text, cookie=None, verbose=False):

    base_url = config['base_url']
    headers= {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53"
    }
    
    if cookie is not None:
        headers['cookie'] = cookie
    else:
        warnings.warn('No cookie set. Without a cookie, some data will nto be available')
    
    interruptions = 0
    read_page = 1
    last_page = 1

    listings = []
    while read_page <= last_page:
        if verbose:
            print(f'--- Reading Page {read_page} of Ebay Results ---')
        options = {
            '_fsrp':1, # ?
            'rt':'nc', # ?
            '_from':'R40', # ?
            '_nkw': query_text, # query text
            '_udlo': 23, # Price low
            '_udhi': 1234, # Price High
            'RAM%20Size': '16%20GB', # RAM size (Bizzarely, in the real URL we see %2520, which before encoding is %20, which is itself an encoded space character)
            'Processor': 'AMD%20Ryzen%207', # Processor
            'Release%20Year': 2022, # Release year
            'Operating%20System': 'Windows%2011%20Pro', # OS
            '_sacat': 0, # Category variable (0 is either All or Default - i.e. let ebay decide)
            'LH_Complete': 1, # Completed listings
            'LH_Sold': 1, # Sold listings
            'LH_ItemCondition':'1000|1500|2000|2010|2020|2030|2500|3000', # All item conditions other than parts
            '_ipg': 240, # Items per page
            '_pgn': read_page # Page number
        }
        
        r = requests.get(base_url, params=options, headers=headers)
        data = r.text
        soup = BeautifulSoup(data, 'html5lib')
    
        messages = soup.find_all('div', attrs={'class':'s-message__content'})
        message_text = ' '.join([m.text for m in messages])
        if 'unable to show you' in message_text:
            print(f'Page issue encountered at page {read_page} of query \'{query_text}\' with URL: ')
            print(r.url)
            print(f'Page issued message \'{message_text}\'.')
            print('Skipping remaining results.')
            break

        # Find the listing/results count so we know if we have to pagenate 
        listing_count_data = soup.find('h1', attrs={'class': 'srp-controls__count-heading'})
        listing_count = None
        try:
            res = re.search('(?P<listing_count>\d+(?:\,\d+)*)\+? result', listing_count_data.text)
            res = res.groupdict()
            listing_count = res.get('listing_count')
            listing_count = listing_count.replace(',','')
            listing_count = int(listing_count)
        except AttributeError:
            print(f'Could not find result count of page {read_page} of query \'{query_text}\' with URL: ')
            print(r.url)
            print('Attempting to continue.')
            pass

        if listing_count == 0:
            print(f'Query \'{query_text}\' returned 0 results with URL: ')
            print(r.url)
            print('Exiting scrape')
            return pd.DataFrame([])

        new_listings = soup.find_all('li', attrs={'class': 's-item'})
        listings += new_listings

        if listing_count <= 240:
            break
        else:
            pagenation_items = soup.find_all('a', attrs={'class': 'pagination__item'})
            if len(pagenation_items) == 0:
                print(f'Search interrupted at page {read_page} with URL: ')
                print(r.url)
                print('Page HTML: ')
                print(soup.text)
                print(f'Interruptions encountered: {interruptions}')
                interruptions += 1
                print('Continuing...')
                time.sleep(1)
                continue
        
            read_page += 1
            last_page = int(pagenation_items[-1].text)

        #time.sleep(.5)

    listing_data = [__listing_to_row(li) for li in listings]
    
    listing_data = pd.DataFrame(listing_data)
    listing_data['price'] = listing_data['price'].apply(__format_price)
    listing_data['sold_date'] = pd.to_datetime(listing_data['sold_date'])
    return listing_data

def __listing_to_row(listing):
    ''' Extract name, price, date, tags, and link from a li element'''
    # Name
    prod_name_data = listing.find('span', attrs={'role':'heading'})
    prod_name = None
    if prod_name_data is not None:
        prod_name = prod_name_data.text
        prod_name = prod_name.replace('New Listing', '')

    # Price
    prod_price_data = listing.find('span', attrs={'class':'s-item__price'})
    prod_price = None
    if prod_price_data is not None:
        prod_price = prod_price_data.text

    # Date
    sold_date_data = listing.find_all('span', attrs={'class':'POSITIVE'})
    sold_date = None
    for span in sold_date_data:
        if 'Sold' in span.text:
            sold_date = span.text.replace('Sold ', '')

    # Tags
    prod_tag_data = listing.find_all('div', attrs={'class':'s-item__subtitle'})
    prod_tags = []
    for div in prod_tag_data:
        new_tags = div.text
        new_tags = new_tags.split(' · ')
        prod_tags += new_tags

    # Product link
    prod_link_data = listing.find('a', attrs={'class':'s-item__link'})
    prod_link = None
    if prod_link_data is not None:
        prod_link = prod_link_data['href']

    # Seller name and rating
    prod_seller_data = listing.find('span', attrs={'class': 's-item__seller-info-text'})
    prod_seller = None
    if prod_seller_data is not None:
        seller_re = 'Seller: (?P<seller_name>\S+) \((?P<seller_sales_count>\S+)\) (?P<seller_score>\d+\.?\d*)\%'
        res = re.search(seller_re, prod_seller_data.text)
        prod_seller = res.groupdict()
    if prod_seller is None:
        prod_seller = {}

    row = {
        'name': prod_name,
        'price': prod_price,
        'sold_date': sold_date,
        'tags': prod_tags,
        'link': prod_link,
        'seller_name': prod_seller.get('seller_name'),
        'seller_sales_count': prod_seller.get('seller_sales_count'),
        'seller_score': prod_seller.get('seller_score')
    }
    return row

def __format_price(raw_price):
    ''' Converts a string price with the '$' symbol and commas to a float '''
    if raw_price is None:
        return None
    price = re.sub('[\$\,]','', raw_price)
    price = re.findall('\d+\.\d+', price)
    price = [float(p) for p in price]
    if len(price) < 1:
        return None
    new_price = sum(price)/len(price)
    return new_price