import os
import json
import copy
import decimal
decimal.getcontext()
Dec = decimal.Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return {'__Decimal__' : str(o)}
        return json.JSONEncoder.default(self, o)


class Banner:
    def __init__(self, template):
        with open("pools.json", "r") as f:
            self.available = json.load(f)
        self.template = template
        blank = {
                'dragon' : {
                    'size' : 0,
                    'contents' : []
                },
                'adventurer' : {
                    'size' : 0,
                    'contents' : []
                }
            }
        self.pools = {
            '5' : copy.deepcopy(blank),
            '4' : copy.deepcopy(blank),
            '3' : copy.deepcopy(blank)
        }
        self.banner = {}
        self.p_adds = []
        self.input_pools()
        self.input_focus()
        self.set_rates()
        commit = input('Proceed to save banner? [y/n]: ')
        if commit.lower() in ['y', 'ye', 'yes', 'yeah']:
            self.store_banner()

    def add_pools(self, pool):
        if pool not in self.p_adds:
            self.p_adds += [pool]
            for rarity in ['5', '4', '3']:
                for classification in ['adventurer', 'dragon']:
                    for category in ['size', 'contents']:
                        self.pools[rarity][classification][category] += self.available[classification][pool][rarity][category]
        else:
            print('That pool has already been added.')

    def input_pools(self):
        breaker = 0
        while breaker == 0:
            new_pool = input('Please add a pool to the banner [Permanent, Gala, Seasonal, Zodiac, Collab]: ')
            try:
                self.add_pools(new_pool)
            except KeyError:
                print('That was not a valid pool')
            again = input('Add another pool? [y/n]: ')
            if again.lower() in ['y', 'yes', 'ye', 'yeah']:
                continue
            else:
                if 'Permanent' not in self.p_adds and 'All' not in self.p_adds:
                    no_perm = input('The permanent pool has not been included. Continue anyway? [y/n]: ')
                    if no_perm.lower() not in ['y', 'yes', 'ye', 'yeah']:
                        continue
                breaker = 1

    def add_focus(self, unit, rarity, classification):
        if unit not in self.banner.keys():
            self.banner[unit] = {}
            self.banner[unit]['rarity'] = rarity
            self.banner[unit]['classification'] = classification
            return False
        else:
            print(f'{unit} is already on the banner.')
            return True

    def input_focus(self):
        breaker = 0
        while breaker == 0:
            new_focus = input('Please add a unit to the banner [NOTE - very picky]: ')
            if new_focus == "Poli'ahu":
                new_focus = 'Poliʻahu'
            not_found = True
            for rarity in ['5', '4', '3']:
                for classification in ['adventurer', 'dragon']:
                    if new_focus in self.pools[rarity][classification]['contents']:
                        not_found = False
                        flag = self.add_focus(new_focus, rarity, classification)
                        if not flag:
                            self.pools[rarity][classification]['size'] -= 1
            if not_found:
                go_ahead = input('This unit was not found in the pool. Add them anyway? [y/n]: ')
                if go_ahead.lower() in  ['y', 'yes', 'ye', 'yeah']:
                    rare_repeat = True
                    class_repeat = True
                    while rare_repeat:
                        unit_rarity = input('What is the rarity of this unit? [5, 4, 3]: ')
                        if unit_rarity in ['5', '4', '3']:
                            rare_repeat = False
                        else:
                            print('That is not a valid rarity.')
                    while class_repeat:
                        unit_classification = input('What type of unit is this? [dragon, adventurer]: ')
                        if unit_classification.lower() in ['dragon', 'd', 'drag']:
                            unit_classification = 'dragon'
                            class_repeat = False
                        elif unit_classification.lower() in ['adventurer', 'adv', 'a']:
                            unit_classification = 'adventurer'
                            class_repeat = False
                        else:
                            print('That is not a valid classification.')
                    self.pools[unit_rarity][unit_classification]['contents'] += [new_focus]
                    self.add_focus(new_focus, unit_rarity, unit_classification)
            again = input('Add another unit? [y/n]: ')
            if again.lower() in ['y', 'yes', 'ye', 'yeah']:
                continue
            else:
                breaker = 1

    def set_rates(self):
        f_counts = {}
        for rarity in ['5', '4', '3']:
            f_counts[rarity] = {}
            for classification in ['dragon', 'adventurer']:
                f_counts[rarity][classification] = 0
                for unit in self.banner.values():
                    if (unit['rarity'], unit['classification']) == (rarity, classification):
                        f_counts[rarity][classification] += 1
                #note: very messy
        banner_rates = copy.deepcopy(self.template)
        template = self.template
        for rarity in ['5', '4', '3']:
            for classification in ['dragon', 'adventurer']:
                try:
                    correction = Dec(1)/Dec(f_counts[rarity][classification])
                except ZeroDivisionError:
                    if template[rarity]['Focus']['rate'] != 0:
                        print(f'No focus for {rarity}* {classification}')
                        print(f'Defaulting to one unlisted focus unit.')
                    correction = 1
                banner_rates[rarity]['Focus'][classification] = (template[rarity]['Focus']['rate']
                                                                *correction
                                                                *Dec(template[rarity]['Focus'][classification][0])
                                                                /Dec(template[rarity]['Focus'][classification][1]))
                try:
                    nf_correction = Dec(1)/Dec(self.pools[rarity][classification]['size'])
                except ZeroDivisionError:
                    print(f"Error: every {rarity}* {classification} is a focus")
                    print('Defaulting to one unlisted nonfocus unit.')
                    nf_correction = 1
                banner_rates[rarity]['Non Focus'][classification] = (template[rarity]['Non Focus']['rate']
                                                                    *nf_correction
                                                                    *Dec(template[rarity]['Non Focus'][classification][0])
                                                                    /Dec(template[rarity]['Non Focus'][classification][1]))
        self.banner_rates = banner_rates
        
    def store_banner(self):
        banner_name = input('Please give this banner a name: ')
        banner_info = {
            'banner rates' : self.banner_rates,
            'focus' : self.banner,
            'pool' : self.pools
        }
        path = os.getcwd() + '\\banner_storage' + '\\' + banner_name
        with open(path, "w+", encoding="utf8") as f:
            json.dump(banner_info, f, cls=DecimalEncoder)

# def as_decimal(dct):
#     if '__Decimal__' in dct:
#         return decimal.Decimal(dct['__Decimal__'])
#     return dct


            


