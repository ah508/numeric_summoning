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

def as_decimal(dct):
    if '__Decimal__' in dct:
        return decimal.Decimal(dct['__Decimal__'])
    return dct

def delete(banner_name):
    path = os.getcwd() + '\\banner_storage' + '\\' + banner_name
    try:
        os.remove(path)
    except FileNotFoundError:
        print('That banner does not exist.')

def checkquit(s):
        if s == 'exit':
            exit()

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
            checkquit(new_pool)
            try:
                self.add_pools(new_pool)
            except KeyError:
                print('That was not a valid pool')
            again = input('Add another pool? [y/n]: ')
            checkquit(again)
            if again.lower() in ['y', 'yes', 'ye', 'yeah']:
                continue
            else:
                if 'Permanent' not in self.p_adds and 'All' not in self.p_adds:
                    no_perm = input('The permanent pool has not been included. Continue anyway? [y/n]: ')
                    checkquit(no_perm)
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
            checkquit(new_focus)
            if new_focus == "Poli'ahu":
                new_focus = 'Poliʻahu'
            not_found = True
            for rarity in ['5', '4', '3']:
                for classification in ['adventurer', 'dragon']:
                    if new_focus in self.pools[rarity][classification]['contents']:
                        if self.template[rarity]['Focus']['base'] == 0:
                            print('This banner template does not have focus units of that rarity.')
                            continue
                        if self.template[rarity]['Focus'][classification] == 0:
                            print(f'This banner template does not have focus {classification}s of that rarity.')
                            continue
                        not_found = False
                        flag = self.add_focus(new_focus, rarity, classification)
                        if not flag:
                            self.pools[rarity][classification]['size'] -= 1
            if not_found:
                go_ahead = input('This unit was not found in the pool. Add them anyway? [y/n]: ')
                checkquit(go_ahead)
                if go_ahead.lower() in  ['y', 'yes', 'ye', 'yeah']:
                    rare_repeat = True
                    class_repeat = True
                    while rare_repeat:
                        unit_rarity = input('What is the rarity of this unit? [5, 4, 3]: ')
                        checkquit(unit_rarity)
                        if unit_rarity in ['5', '4', '3']:
                            rare_repeat = False
                        else:
                            print('That is not a valid rarity.')
                    while class_repeat:
                        unit_classification = input('What type of unit is this? [dragon, adventurer]: ')
                        checkquit(unit_classification)
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
            checkquit(again)
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
        #note: very messy^
        banner_rates = {}
        for rarity in ['5', '4', '3']:
            banner_rates[rarity] = {}
            for unit_type in ['Focus', 'Non Focus']:
                banner_rates[rarity][unit_type] = {}
                for classification in ['dragon', 'adventurer']:
                    banner_rates[rarity][unit_type][classification] = self.rate_handler(f_counts, rarity, unit_type, classification)
        self.banner_rates = banner_rates
        
    def rate_handler(self, counts, rarity, unit_type, classification):
        template = self.template[rarity][unit_type]
        working_dict = {}
        if unit_type == 'Focus':
            correction = Dec(counts[rarity][classification])
            if correction == 0:
                if template['base'] != 0:
                    print(f'No {unit_type} for {rarity}* {classification}')
                    print(f'Defaulting to one unlisted {unit_type} unit.')
                correction = 1
        else:
            correction = Dec(self.pools[rarity][classification]['size'])
            if correction == 0:
                if template['base'] != 0:
                    print(f'No {unit_type} for {rarity}* {classification}')
                    print(f'Defaulting to one unlisted {unit_type} unit.')
                correction = 1
        working_dict['base prob'] = (template['base']
                                    *Dec(template[classification][0])
                                    /Dec(template[classification][1])
                                    /correction)
        working_dict['prob inc'] = (template['inc']
                                    *Dec(template[classification][0])
                                    /Dec(template[classification][1])
                                    /correction)
        if rarity == '5':
            working_dict['alt prob'] = working_dict['base prob']
            working_dict['alt inc'] = working_dict['prob inc']
            tot_5 = (self.template['5']['Focus']['base'] 
                    + self.template['5']['Non Focus']['base'])
            working_dict['spec prob'] = working_dict['base prob']/tot_5
        elif rarity == '4':
            tot_4 = (self.template['4']['Focus']['base']
                    + self.template['4']['Non Focus']['base'])
            tot_5 = (self.template['5']['Focus']['base'] 
                    + self.template['5']['Non Focus']['base'])
            inc_5 = (self.template['5']['Focus']['inc']
                    + self.template['5']['Non Focus']['inc'])
            unit_ratio = working_dict['base prob']/tot_4
            working_dict['alt prob'] = (1 - tot_5)*unit_ratio
            working_dict['alt inc'] = -1*(working_dict['alt prob'] - (1 - tot_5 - inc_5)*unit_ratio)
            working_dict['spec prob'] = 0
        else:
            working_dict['alt prob'] = 0
            working_dict['alt inc'] = 0
            working_dict['spec prob'] = 0
        return working_dict

    def store_banner(self):
        banner_name = input('Please give this banner a name: ')
        checkquit(banner_name)
        banner_info = {
            'banner rates' : self.banner_rates,
            'focus' : self.banner,
            'pool' : self.pools,
            'max pity' : self.template['max pity']
        }
        path = os.getcwd() + '\\banner_storage' + '\\' + banner_name
        with open(path, "w+", encoding="utf8") as f:
            json.dump(banner_info, f, cls=DecimalEncoder)
    

class FindWants:
    def __init__(self):
        self.found = False
        self.wants = {}

    def fetch(self, banner_name):
        path = os.getcwd() + '\\banner_storage' + '\\' + banner_name
        try:
            with open(path, "r") as f:
                self.banner = json.load(f, object_hook=as_decimal)
            self.found = True
        except FileNotFoundError:
            print('That banner does not exist.')
        
    def get_char(self, char_name):
        banner = self.banner
        b_foc = self.banner['focus']
        b_pool = self.banner['pool']
        b_rates = self.banner['banner rates']
        if char_name in banner['focus']:
            self.wants[char_name] = b_rates[b_foc[char_name]['rarity']]['Focus'][b_foc[char_name]['classification']]
            self.wants[char_name]['rarity'] = b_foc[char_name]['rarity']
        else:
            for rarity in ['5', '4', '3']:
                for classification in ['dragon', 'adventurer']:
                    if char_name in b_pool[rarity][classification]['contents']:
                        self.wants[char_name] = b_rates[rarity]['Non Focus'][classification]
                        self.wants[char_name]['rarity'] = rarity
                    else:
                        print('That unit is not on this banner.')



