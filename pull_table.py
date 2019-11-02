from urllib.request import urlopen
from bs4 import BeautifulSoup
import json

adv_url = "https://dragalialost.gamepedia.com/Adventurer_List"
drag_url = "https://dragalialost.gamepedia.com/Dragon_List"
adv_html = urlopen(adv_url)
adv_data = BeautifulSoup(adv_html, "html5lib")
drag_html = urlopen(drag_url)
drag_data = BeautifulSoup(drag_html, "html5lib")

adventurer = {}
dragon = {}
for category in ['All', 'Permanent', 'Seasonal', 'Gala', 'Zodiac', 'Collab']:
    adventurer[category] = {}
    dragon[category] = {}

for rarity in ['5', '4', '3']:
    adventurer['All'][rarity] = len(adv_data.find_all("tr", attrs={"data-rarity" : rarity}))
    dragon['All'][rarity] = len(drag_data.find_all("tr", attrs={"data-rarity" : rarity}))
    for subpool in ['Permanent', 'Seasonal', 'Gala', 'Zodiac', 'Collab']:
        adventurer[subpool][rarity] = len(adv_data.find_all("tr", attrs={'data-availability' :  subpool, 'data-rarity' : rarity}))
        dragon[subpool][rarity] = len(drag_data.find_all("tr", attrs={'data-availability' :  subpool, 'data-rarity' : rarity}))

pool = {
    'dragon' : dragon,
    'adventurer' : adventurer
    }

with open("pools.json", "w+", encoding="utf8") as f:
    json.dump(pool, f)    