# TODO: 
# option to exlcude traders in dlc areas
# price factor for individual items
# exception handling

import re
import requests
from bs4 import BeautifulSoup
import time
import os.path
import random

price_table = open(os.path.expanduser('~')+"\\Documents\\Elder Scrolls Online\\live\\AddOns\\TamrielTradeCentre\\PriceTable.lua", "r").read()
ItemLOT = open(os.path.expanduser('~')+"\\Documents\\Elder Scrolls Online\\live\\AddOns\\TamrielTradeCentre\\ItemLookUpTable_EN.lua", "r").read()

# Fill this list with items you want to check

item_list = []

with open("itemlist.txt") as file:
    for line in file: 
        line = line.strip() #or some other preprocessing
        item_list.append(line) #storing everything in memory!

# Dict for the average prices
item_price = dict()

get_number_regex = re.compile(r'(\d+.\d+)(?=,)')

# Get average prices and Ids of items
for item in item_list:
    # Regex the heck out of those tables, please rewrite this :(
    item_index_regex = re.compile(r''+item+'[\s\S]*?,')
    item_index = get_number_regex.search(item_index_regex.search(ItemLOT).group()).group()
    # Builds regex for specific item index
    search_item_avg_info_regex = re.compile(r'(\['+str(item_index)+'\])[\s\S]*?,')
    # Get the item with avg price
    item_info = search_item_avg_info_regex.search(price_table)
    # Extract avg price 
    item_avg_price = get_number_regex.search(item_info.group()).group()
    item_price[item] = (item_index, float(item_avg_price))

# Factor at which price difference the listing will be issued to the user
# in percent(%), e.g. if item is 1000 avg then issue at 200 at factor 0.2
alarm_factor_price = 0.8

# Factor of how likely the listing is still active in minutes
# Listings older the factor will be ignored
alarm_factor_time = 60

print("Items will show up if the listing is "+str(alarm_factor_price*100)+"(%) cheaper and not older then "+str(alarm_factor_time)+" minutes")
print("Checking for these items: \n(Name, ID, Avg price)")
print(item_price)

url_p1 = "https://eu.tamrieltradecentre.com/pc/Trade/SearchResult?SearchType=Sell&ItemID="
url_p2 = "&ItemCategory1ID=&ItemTraitID=&ItemQualityID=&IsChampionPoint=false&LevelMin=&LevelMax=&MasterWritVoucherMin=&MasterWritVoucherMax=&AmountMin=&AmountMax=&PriceMin=&PriceMax=&SortBy=Price&Order=asc"

price_regex = re.compile(r'\d*,*\d*\.*\d+(?= *X)')

while(True):
    for item in item_list:
        # Dont remove or you will send unlimited requests to the server
        time.sleep(60+random.randint(0, 5))
        # Create URL for get
        url = url_p1+item_price[item][0]+'&ItemNamePattern='+item+url_p2
        #print("Updating listings...")
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        #print(item)
        # Extract infos from all listings
        for entry in soup.find_all('tr', 'cursor-pointer'):
            #print(entry)
            price = None
            last_seen = None
            location = None 

            # Get location of listing

            location = entry.find('td', 'hidden-xs')
            location = location.find_next_sibling()
            location = location.get_text("  ", strip = True)
            
            # Get per item price and total price
            gold_amount = entry.find('td', 'gold-amount')
            gold_amount_text = gold_amount.get_text("  ", strip = True)
            price = price_regex.search(gold_amount_text).group()
            price = float(price.replace(',', ''))
            
            # Get time elapsed since listing appeared
            last_seen = float(gold_amount.find_next_sibling().get('data-mins-elapsed'))
            
            # If item is cheap enough and the listing is fresh then alarm user
            if price < item_price[item][1]*alarm_factor_price and last_seen < alarm_factor_time:
                print(item+" for "+str(gold_amount_text)+ " at " +str(location)+" listed since "+str(last_seen)+" minutes")