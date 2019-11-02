from urllib.request import urlopen
from bs4 import BeautifulSoup
import json

url = "https://dragalialost.gamepedia.com/Adventurer_List"
html = urlopen(url)
data = BeautifulSoup(html, "html5lib")

pool = {}
for category in ['All', 'Permanent', 'Seasonal', 'Gala', 'Zodiac', 'Collab']:
    pool[category] = {}

for rarity in ['5', '4', '3']:
    pool['All'][rarity] = len(data.find_all("tr", attrs={"data-rarity" : rarity}))
    for subpool in ['Permanent', 'Seasonal', 'Gala', 'Zodiac', 'Collab']:
        pool[subpool][rarity] = len(data.find_all("tr", attrs={'data-availability' :  subpool, 'data-rarity' : rarity}))

with open("pools.json", "r+", encoding="utf8") as f:
    f.read()
    f.seek(0)
    f.truncate()

with open("pools.json", "w") as f:
    json.dump(pool, f)
