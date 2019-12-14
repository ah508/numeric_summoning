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
    """Decodes the Decimal datatype."""

    if '__Decimal__' in dct:
        return decimal.Decimal(dct['__Decimal__'])
    return dct

def delete(banner_name):
    """Deletes a banner."""

    path = os.getcwd() + '\\banner_storage' + '\\' + banner_name
    try:
        os.remove(path)
    except FileNotFoundError:
        print('That banner does not exist.')

def checkquit(s):
    """Checks for an exit input."""

    if s == 'exit':
        exit()

def checkname(charname):
    """Corrects names to stored formats."""

    if charname == "Poli'ahu":
        return 'Poliʻahu'
    if charname == 'Juggernaut':
        return 'Juggernaut (Dragon)'
    return charname

class Banner:
    """Defines and saves a banner that you can pull on.

    Pulls information from pools.json and accepts user input to
    create and store a banner for later calculations. There are
    a few known issues, such as the fact that you can add many
    pools twice with the inclusion of 'All'. This is intended
    to be fixed in a later update.

    Attributes
    ----------
    available : {dict}
        Nested dictionary with four key values, denoting:
        {class : {pool : {rarity : {information}}}}
            class : str
                'adventurer' or 'dragon'
            pool : str
                'All', 'Collab', 'Dragonyule', 'Gala',
                'Halloween', 'Permanent', 'Seasonal', 
                "Valentine's", or 'Zodiac'
            rarity : str
                '3', '4', or '5'
            information : str
                'contents' or 'size'
                contents : [str]
                    List of unit names.
                size : int
                    Denotes the size of the pool.
    template : {dict}
        Nested dictionary containing information on pool
        probabilities and ratios. See 'banner_templates.py'.
    pools : {dict}
        Nested dictionary that stores information on the pools of
        the banner under construction. Information is similar to
        that of available (see above), but the depth and order of
        keys is different.
        {'rarity' : {'class' : {'information'}}}
            rarity : str
                '3', '4', or '5'
            class : str
                'adventurer' or 'dragon'
            information : str
                'size' or 'contents'
                size : int
                    Denotes the size of the pool.
                contents : [str]
                    List of unit names.
    banner : {dict}
        The banner under construction. The first key denotes
        what information needs to be retrieved, but the
        dictionaries associated with those keys all have
        wildly different structures, so it is difficult to
        give a summary of them here. The first set of keys,
        and the information the associated dictionaries
        contain is as follows, though:
        {'banner rates', 'focus', 'max pity', 'pool'}
            banner rates :
                Contains the breakdown of probabilities for
                each unit designation
            focus :
                Contains the names and designations of each
                of the focus units.
            max pity :
                Denotes the number of tenpulls needed to reach
                maximum pity. Implicitly reveals whether the
                banner is a normal banner or a gala banner.
            pool :
                Contains the contents and size of the pool
                of available units. If a unit is not in this
                pool, it cannot be pulled on this banner.
    p_adds : [str]
        A list of pool names denoting those which have already
        been added.

    Parameters
    ----------
    template : {dict}
        Nested dictionary of a particular format.
        Expected to be one of the templates listed in
        'banner_templates.py' though in theory you could 
        use an external one, as long as it fit the format.
    """

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
        """Attempts to add a pool to the current banner.
        
        Parameters
        ----------
        pool : str
            Name of the pool attempting to be added
        """

        if pool not in self.p_adds:
            self.p_adds += [pool]
            for rarity in ['5', '4', '3']:
                for classification in ['adventurer', 'dragon']:
                    for category in ['size', 'contents']:
                        self.pools[rarity][classification][category] += self.available[classification][pool][rarity][category]
        else:
            print('That pool has already been added.')

    def input_pools(self):
        """Prompts user input of pools to the current banner.
        
        Prompts the user to input the pools relevant to the current
        banner, and checks to see that entry is valid. Also checks
        to see that the permanent pool is included, however it does
        ensure that 'All' and 'Permanent' are mutually exclusive.
        This can result in mis-sized pools, and is intended to be
        addressed in a future update.
        """

        breaker = 0
        while breaker == 0:
            new_pool = input("Please add a pool to the banner [Permanent, Gala, Seasonal, Dragonyule, Halloween, Valentine's, Zodiac, Collab]: ")
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
        """Attempts to add a focus unit to the current banner.

        Parameters
        ----------
        unit : str
            The name of the unit attempting to be added.
        rarity : str
            The rarity of the unit attempting to be added.
        classification : str
            Denotes whether the unit is a dragon or an adventurer.

        Returns
        -------
        bool
            Indicates whether or not the attempted addition was
            successful. Unintuitively, 'False' indicates success.
        """

        if unit not in self.banner.keys():
            self.banner[unit] = {}
            self.banner[unit]['rarity'] = rarity
            self.banner[unit]['classification'] = classification
            return False
        else:
            print(f'{unit} is already on the banner.')
            return True

    def input_focus(self):
        """Prompts user input of focus units to the current banner.
        
        Prompts the user for input of focus units, checks whether
        or not the requested input is valid, and if so adds the
        unit to the list of focuses. If a unit is not found to
        exist, the user is asked if they would like to define
        that unit. This feature has not currently been thoroughly
        tested, so there may be some issues with detection further
        down the line.
        """

        breaker = 0
        while breaker == 0:
            new_focus = input('Please add a unit to the banner [NOTE - very picky]: ')
            checkquit(new_focus)
            new_focus = checkname(new_focus)
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
        """Sets the rates for the current banner."""

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
        """Checks for and applies corrections to rates.

        Parameters
        ----------
        counts : int
            The number of units that the rate is split between.
        rarity : str
            The rarity of the unit(s) in question.
        unit_type : str
            Indicates whether or not the unit is a focus.
        classification : str
            Indicates whether or not the unit is a dragon or
            an adventurer

        Returns
        -------
        working_dict : dict
            Dictionary containing information on the base rate,
            base increment, alternative rate, alternative increment,
            and special rate for the given categorization. The
            'alternative' is with respect to the last pull of a
            tenpull, and the 'special' is in reference to a forced
            pity break.
        """

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
        """Saves the banner."""

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
    """Fetches a banner and determines desired units.

    A class with methods that fetch a desired banner from storage
    and maintain a list of desired units from that banner.

    Attributes
    ----------
    found : bool
        Indicates whether or not the banner was successfully
        located.
    wants : {dict}
        A nested dictionary containing pull information about
        the units you "want."
    banner : {dict}
        A nested dictionary defining the banner retrieved from
        storage.
    """

    def __init__(self):
        self.found = False
        self.wants = {}

    def fetch(self, banner_name):
        """Fetches the banner from storage.
        
        Parameters
        ----------
        banner_name : str
            The name of the banner.
        """

        path = os.getcwd() + '\\banner_storage' + '\\' + banner_name
        try:
            with open(path, "r") as f:
                self.banner = json.load(f, object_hook=as_decimal)
            self.found = True
        except FileNotFoundError:
            print('That banner does not exist.')
        
    def get_char(self, char_name):
        """Fetches a desired character from the banner.

        Fetches a desired character from the banner and adds
        them to a set of "wants."

        Parameters
        ----------
        char_name : str
            The name of the character being fetched.
        """

        banner = self.banner
        hit = False
        b_foc = self.banner['focus']
        b_pool = self.banner['pool']
        b_rates = self.banner['banner rates']
        if char_name in banner['focus']:
            self.wants[char_name] = b_rates[b_foc[char_name]['rarity']]['Focus'][b_foc[char_name]['classification']]
            self.wants[char_name]['rarity'] = b_foc[char_name]['rarity']
            hit = True
        else:
            for rarity in ['5', '4', '3']:
                for classification in ['dragon', 'adventurer']:
                    if char_name in b_pool[rarity][classification]['contents']:
                        self.wants[char_name] = b_rates[rarity]['Non Focus'][classification]
                        self.wants[char_name]['rarity'] = rarity
                        hit = True
                        break
        if not hit:
            print('That unit is not on this banner.')



