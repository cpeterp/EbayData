from bs4 import BeautifulSoup
import getpass
from pathlib import Path
import pandas as pd
import requests
import re
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import json
import warnings

def scraper(query_text:str, options:dict = None, cookie:dict = None, 
            verbose:bool = False):
    """
    Scapes ebay using a search term and a set of search options. Search options 
    can be gleaned from a traditional search of eBay"s website. 

    params:
    - query_text: The search text (as you would type it into eBay's search bar)
    - options: query options passed to the search request. These are documented 
        in the URL_parsing.md file
    - cookie: The cookie (as text) from your browser, which can be copied after 
        logging into eBay. Without this cookie, page timeouts will be more 
        frquent and some item data will not be available
    - verbose: Whether to print out additional status updates or not  
    """
    base_url = "https://www.ebay.com/sch/i.html?"
    headers= {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53"
    }
    
    if cookie is None:
        warnings.warn("No cookie set. Without a cookie, some data will not be"\
                      " available")
    
    interruptions = 0
    read_page = 1
    last_page = 1

    listings = []
    while read_page <= last_page:
        if verbose:
            print(f"--- Reading Page {read_page} of Ebay Results ---")
        
        options["_nkw"] = query_text
        options["_pgn"] = read_page
        r = requests.get(base_url, params=options, headers=headers, cookies=cookie)
        data = r.text
        soup = BeautifulSoup(data, "html5lib")
    
        messages = soup.find_all("div", attrs={"class":"s-message__content"})
        message_text = " ".join([m.text for m in messages])
        if "unable to show you" in message_text:
            print(f"Page issue encountered at page {read_page} of query "\
                f"\"{query_text}\" with URL: ")
            print(r.url)
            print(f"Page issued message \"{message_text}\".")
            print("Skipping remaining results.")
            break

        # Find the listing/results count so we know if we have to pagenate 
        listing_count_data = soup.find("h1", attrs={"class": "srp-controls__count-heading"})
        listing_count = None
        try:
            res = re.search("(?P<listing_count>\d+(?:\,\d+)*)\+? result", listing_count_data.text)
            res = res.groupdict()
            listing_count = res.get("listing_count")
            listing_count = listing_count.replace(",","")
            listing_count = int(listing_count)
        except AttributeError:
            print(f"Could not find result count of page {read_page} of query \"{query_text}\" with URL: ")
            print(r.url)
            print("Attempting to continue.")
            pass

        if listing_count == 0:
            print(f"Query \"{query_text}\" returned 0 results with URL: ")
            print(r.url)
            print("Exiting scrape")
            return pd.DataFrame([])

        new_listings = soup.find_all("li", attrs={"class": "s-item"})
        listings += new_listings

        if listing_count <= 240:
            break
        else:
            pagenation_items = soup.find_all("a", attrs={"class": "pagination__item"})
            if len(pagenation_items) == 0:
                print(f"Search interrupted at page {read_page} with URL: ")
                print(r.url)
                print("Page HTML: ")
                print(soup.text)
                print(f"Interruptions encountered: {interruptions}")
                interruptions += 1
                print("Continuing...")
                time.sleep(1)
                continue
        
            read_page += 1
            last_page = int(pagenation_items[-1].text)

        #time.sleep(.5)

    listing_data = [__listing_to_row(li) for li in listings]
    
    listing_data = pd.DataFrame(listing_data)
    listing_data["price"] = listing_data["price"].apply(__format_price)
    listing_data["sold_date"] = pd.to_datetime(listing_data["sold_date"])
    return listing_data

def retrieve_cookies():
    """
    Uses Selenium to retrieve cookies form Ebay for webscraping.
    """
    # Default variables
    package_dir = Path(__file__).parent
    driver_path = package_dir.parent / "resources/chromedriver.exe"

    # Load configs
    with open(package_dir/"lib/search_config.json", "rt") as F:
        config = json.load(F)

    # Load ebay credentials
    login_info_path = package_dir/".env/login_info.json"
    try:
        with open(login_info_path, "rt") as F:
            login_info = json.load(F)
    except:
        if not login_info_path.exists():
            login_info_path.mkdir(parents=True)
        print("Enter your Ebay credentials.")
        usr = getpass.getuser("Ebay Username: ")
        psw = getpass.getpass("Ebay Password: ")
        login_info = {"username":usr, "password":psw}
        with open(login_info_path, "wt") as F:
            json.dump(login_info, F)
    
    # Selenium start options
    chrome_options = Options()
    chrome_options.add_argument("--window-size=%s" % config["window_size"])

    print(str(driver_path))
    service = Service(executable_path=str(driver_path))
    driver = webdriver.Chrome(service=service)
    driver.delete_all_cookies()
    driver.get("https://signin.ebay.com/ws/eBayISAPI.dll")
    time.sleep(1)

    while __is_captcha(driver):
        time.sleep(0.5)

    time.sleep(1)
    email_address = driver.find_element(By.XPATH, "//input[@id='userid']")
    email_address.clear()
    email_address.send_keys(login_info['username'])
    email_address.send_keys(Keys.RETURN)
    time.sleep(1)

    while __is_captcha(driver):
        time.sleep(0.5)

    time.sleep(1)
    password = driver.find_element(By.XPATH, "//input[@id='pass']")
    password.clear()
    password.send_keys(login_info['password'])
    password.send_keys(Keys.RETURN)
    time.sleep(1)

    while __is_captcha(driver):
        time.sleep(0.5)

    time.sleep(1)
    send_cookies = {}
    all_cookies = driver.get_cookies()
    for cookie in all_cookies:
        if cookie["name"] in config["cookie_names"]:
            send_cookies[cookie["name"]] = cookie["value"]

    return send_cookies

def __is_captcha(driver):
    elements = \
        driver.find_elements(By.XPATH, "//iframe[@id='captchaFrame']") +\
        driver.find_elements(By.XPATH, "//form[@id='captcha_form']")
    if len(elements) > 0:
        return True
    else:
        return False

def __listing_to_row(listing):
    """ Extract name, price, date, tags, and link from a li element"""
    # Name
    prod_name_data = listing.find("span", attrs={"role":"heading"})
    prod_name = None
    if prod_name_data is not None:
        prod_name = prod_name_data.text
        prod_name = prod_name.replace("New Listing", "")

    # Price
    prod_price_data = listing.find("span", attrs={"class":"s-item__price"})
    prod_price = None
    if prod_price_data is not None:
        prod_price = prod_price_data.text

    # Date
    sold_date_data = listing.find_all("span", attrs={"class":"POSITIVE"})
    sold_date = None
    for span in sold_date_data:
        if "Sold" in span.text:
            sold_date = span.text.replace("Sold ", "")

    # Tags
    prod_tag_data = listing.find_all("div", attrs={"class":"s-item__subtitle"})
    prod_tags = []
    for div in prod_tag_data:
        new_tags = div.text
        new_tags = new_tags.split(" · ")
        prod_tags += new_tags

    # Product link
    prod_link_data = listing.find("a", attrs={"class":"s-item__link"})
    prod_link = None
    if prod_link_data is not None:
        prod_link = prod_link_data["href"]

    # Seller name and rating
    prod_seller_data = listing.find(
        "span", 
        attrs={"class": "s-item__seller-info-text"}
    )
    prod_seller = None
    if prod_seller_data is not None:
        seller_re = "Seller: (?P<seller_name>\S+) "\
            "\((?P<seller_sales_count>\S+)\) (?P<seller_score>\d+\.?\d*)\%"
        res = re.search(seller_re, prod_seller_data.text)
        prod_seller = res.groupdict()
    if prod_seller is None:
        prod_seller = {}

    row = {
        "name": prod_name,
        "price": prod_price,
        "sold_date": sold_date,
        "tags": prod_tags,
        "link": prod_link,
        "seller_name": prod_seller.get("seller_name"),
        "seller_sales_count": prod_seller.get("seller_sales_count"),
        "seller_score": prod_seller.get("seller_score")
    }
    return row

def __format_price(raw_price):
    """ Converts a string price with the "$" symbol and commas to a float """
    if raw_price is None:
        return None
    price = re.sub("[\$\,]","", raw_price)
    price = re.findall("\d+\.\d+", price)
    price = [float(p) for p in price]
    if len(price) < 1:
        return None
    new_price = sum(price)/len(price)
    return new_price