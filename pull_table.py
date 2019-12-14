from urllib.request import urlopen
from bs4 import BeautifulSoup
import copy
import json
import re

def getname(tag, identifier):
    """Gets the name of a unit.

    Parameters
    ----------
    tag : str
        The html table entry being searched.
    identifier : SRE_Pattern
        The regex pattern that will return the desired result.
        This is predetermined, and admittedly a little sloppy.

    Returns
    -------
    str
        The name of the unit.
    """

    hold = tag.find("a")
    name = re.search(identifier, str(hold))
    try:
        return name.group(0)
    except AttributeError:
        print('Name Fetch error')
        print()

def pull_table():
    """Scrapes the wiki to pull some relevant information.

    Scrapes the wiki for information on adventurers and dragons,
    including rarity, general availability, and name. This data
    is then serialized and written to a .json as a nested
    dictionary.
    """
    
    adv_url = "https://dragalialost.gamepedia.com/Adventurer_List"
    drag_url = "https://dragalialost.gamepedia.com/Dragon_List"
    adv_html = urlopen(adv_url)
    adv_data = BeautifulSoup(adv_html, "html5lib")
    adv_table = adv_data.find("table", {"class" : "wikitable"})
    drag_html = urlopen(drag_url)
    drag_data = BeautifulSoup(drag_html, "html5lib")
    drag_table = drag_data.find("table", {"class" : "wikitable"})
    identifier = re.compile("""(?<=title=")[A-Za-z'ʻ() -]*(?=")""")

    adventurer = {}
    dragon = {}
    blank = {
        'size' : 0,
        'contents' : []
    }
    for category in ['All', 'Permanent', 'Seasonal', 'Dragonyule', 'Halloween', "Valentine's", 'Gala', 'Zodiac', 'Collab']:
        adventurer[category] = {}
        dragon[category] = {}
    
    for rarity in ['5', '4', '3']:
        adventurer['All'][rarity] = copy.deepcopy(blank)
        dragon['All'][rarity] = copy.deepcopy(blank)
        for subpool in ['Permanent', 'Seasonal', 'Dragonyule', 'Halloween', "Valentine's", 'Gala', 'Zodiac', 'Collab']:
            adventurer[subpool][rarity] = copy.deepcopy(blank)
            dragon[subpool][rarity] = copy.deepcopy(blank)

    for rarity in ['5', '4', '3']:
        a_rows = adv_table.find_all("tr", attrs={"data-rarity" : rarity})
        d_rows = drag_table.find_all("tr", attrs={"data-rarity" : rarity})
        for row in a_rows:
            adventurer['All'][rarity]['contents'].append(getname(row, identifier))
            adventurer['All'][rarity]['size'] += 1
        for row in d_rows:
            dragon['All'][rarity]['contents'].append(getname(row, identifier))
            dragon['All'][rarity]['size'] += 1

        for subpool in ['Permanent', 'Seasonal', 'Gala', 'Zodiac', 'Collab']:
            a_subrows = adv_table.find_all("tr", attrs={'data-availability' :  subpool, 'data-rarity' : rarity})
            d_subrows = drag_table.find_all("tr", attrs={'data-availability' :  subpool, 'data-rarity' : rarity})
            for row in a_subrows:
                adventurer[subpool][rarity]['contents'].append(getname(row, identifier))
                adventurer[subpool][rarity]['size'] += 1
            for row in d_subrows:
                dragon[subpool][rarity]['contents'].append(getname(row, identifier))
                dragon[subpool][rarity]['size'] += 1
        
        for subpool in ['Dragonyule', 'Halloween', "Valentine's"]:
            for unit in adventurer['Seasonal'][rarity]['contents']:
                if subpool in unit:
                    adventurer[subpool][rarity]['contents'].append(unit)
                    adventurer[subpool][rarity]['size'] += 1
            for unit in dragon['Seasonal'][rarity]['contents']:
                if subpool in unit:
                    dragon[subpool][rarity]['contents'].append(unit)
                    dragon[subpool][rarity]['size'] += 1

    pool = {
        'dragon' : dragon,
        'adventurer' : adventurer
        }

    with open("pools.json", "w+", encoding="utf8") as f:
        json.dump(pool, f)

if __name__ == '__main__':
    pull_table()