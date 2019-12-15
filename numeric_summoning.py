import argparse
import inspect
from pull_table import pull_table
from banner_ops import checkquit, checkname

parser = argparse.ArgumentParser(description='Determine the expected number of pulls to achieve a desired result.')
parser.add_argument('-nb', '--newbanner', action='store_true',
                    help='Indicates that you would like to add one or more new banners to the system.')
parser.add_argument('-db', '--deletebanner', action='store_true',
                    help='Indicates that you would like to delete one or more banners from the system.')
parser.add_argument('--update', action='store_true',
                    help='Updates the pull table by scraping the wiki.')
parser.add_argument('--mode', choices=['single', 'ten'], default='ten',
                    help='Signifies whether to use singlepulls or tenpulls.')
parser.add_argument('--accurate', action='store_true',
                    help='Use more accurate numerical information - greatly increases runtime.')
parser.add_argument('-sc', '--suppresscalculate', action='store_false',
                    help='Suppresses calculation of expected value.')
parser.add_argument('-s', '--simulate', action='store_true',
                    help='Allows you to simulate pulling on the banner.')
parser.add_argument('-t', '--tests', action='store_true',
                    help='Returns diagnostics about the banner and generated Markov chains.')

args = parser.parse_args()

if args.update:
    pull_table()

if args.simulate or args.calculate or args.newbanner or args.deletebanner:
    print('enter "exit" at any prompt to exit the program.')

if args.newbanner or args.deletebanner:
    print('Ignoring other functionality for this run;')
    if args.newbanner:
        from banner_ops import Banner
        import banner_templates
        add_banners = True
        while add_banners:
            print('Which template does this banner fit?')
            print('enter "names" to see a list of templates.')
            temp_select = True
            while temp_select:
                temp = input('Enter template: ')
                checkquit(temp)
                if temp == 'names':
                    print(inspect.getdoc(banner_templates))
                else:
                    try:
                        template = getattr(banner_templates, temp)
                        temp_select = False
                    except AttributeError:
                        print('That was not a valid template.')
            new_banner = Banner(template)
            done = input('Add another banner? [y/n]: ')
            checkquit(done)
            if done.lower() in ['n', 'no', 'nope', 'nay']:
                add_banners = False
    if args.deletebanner:
        from banner_ops import delete
        import os
        namepath = os.getcwd() + '\\banner_storage'
        d_banner = True
        print('Which banner would you like to delete?')
        print('enter "names" to see a list of currently stored banners.')
        while d_banner:
            banner_name = input('Enter banner name: ')
            checkquit(banner_name)
            if banner_name == 'names':
                names = os.listdir(namepath)
                for name in names:
                    print(name)
            else:
                for_sure = input('Are you SURE you want to delete this banner? [y/n]: ')
                checkquit(for_sure)
                if for_sure.lower() in ['y', 'ye', 'yes', 'yeah']:
                    final_confirmation = input(f'enter "D" to delete {banner_name}: ')
                    checkquit(final_confirmation)
                    if final_confirmation in ['D', '"D"']:
                        delete(banner_name)
                        print(f'{banner_name} has been deleted.')
                    else:
                        print(f'{banner_name} was not deleted')
                done = input('Would you like to delete a different banner? [y/n]: ')
                checkquit(done)
                if done.lower() in ['n', 'no', 'nope', 'nay']:
                    d_banner = False
    print('File operations complete.')

elif args.simulate or args.calculate:
    import os
    import time
    import config
    from banner_ops import FindWants
    Banner = FindWants()
    namepath = os.getcwd() + '\\banner_storage'
    if args.accurate:
        config.MODE = 'Accurate'

    print('Which banner would you like to pull on?')
    print('enter "names" to see a list of currently stored banners.')
    while not Banner.found:
        banner_name = input('Enter banner name: ')
        checkquit(banner_name)
        if banner_name == 'names':
            names = os.listdir(namepath)
            for name in names:
                print(name)
        else:
            Banner.fetch(banner_name)
    config.MAX_PITY = Banner.banner['max pity']
    more_chars = True
    added_chars = []
    valid = []
    for rarity in ['5', '4', '3']:
        for classification in ['adventurer', 'dragon']:
            valid += Banner.banner['pool'][rarity][classification]['contents']
    for unit in Banner.banner['focus'].keys():
        if unit not in valid:
            valid += [unit]
    
    print('Please enter the units you would like from this banner.')
    print('enter "names" to see a list of available units.')
    while more_chars:
        char_name = input('Enter character name: ')
        checkquit(char_name)
        char_name = checkname(char_name)
        if char_name == 'names':
            for unit in valid:
                print(unit)
            continue
        else:
            if char_name not in valid:
                print('That unit is not on this banner.')
                continue
            if char_name not in added_chars:
                Banner.get_char(char_name)
                reset = True
                while reset:
                    number = input('How many do you want to pull? ')
                    checkquit(number)
                    try:
                        number = int(number)
                    except ValueError:
                        pass
                    if isinstance(number, int) and number > 0:
                        Banner.wants[char_name]['number'] = number
                        print('Added.')
                        added_chars += [char_name]
                        reset = False
                    elif number == 0:
                        print('Removing unit from index.')
                        del Banner.wants[char_name]
                        reset = False
                    else:
                        print('That is not a valid target')
            else:
                print('That character is already listed.')
                change_num = input('Would you like to change how many you want? [y/n]: ')
                checkquit(change_num)
                if change_num.lower() in ['y', 'ye', 'yes', 'yeah']:
                    reset = True
                    while reset:
                        number = input('How many do you want to pull? ')
                        checkquit(number)
                        try:
                            number = int(number)
                        except ValueError:
                            pass
                        if isinstance(number, int) and number > 0:
                            Banner.wants[char_name]['number'] = number
                            print('Done.')
                            reset = False
                        elif number == 0:
                            print('Removing unit from index.')
                            del Banner.wants[char_name]
                            reset = False
                        else:
                            print('That is not a valid target.')
        another_char = input('Would you like to add another character to the index? [y/n]: ')
        checkquit(another_char)
        if another_char.lower() in ['n', 'no', 'nope', 'nay']:
            more_chars = False

    if Banner.wants == []:
        print('You have not selected any targets.')
        print('Exiting program')
        exit()

    #sanity check
    ns = []
    for unit in Banner.wants.keys():
        ns += [Banner.wants[unit]['number']]
    bignum = 1
    for num in ns:
        bignum *= (num + 1)
    if bignum > 100:
        print('Hey... Look... This is a pretty large matrix.')
        print("I don't want to say you shouldn't go and compute it")
        print('But if you do, it may be very time consuming and resource intensive.')
        confirmation = input('You sure you want to go ahead and do this? [y/n]: ')
        checkquit(confirmation)
        if confirmation.lower() in ['y', 'ye', 'yes', 'yeah']:
            print('Alright dude')
            print('If it gets really bad, remember that you can always kill your terminal.')
        else:
            print("I didn't recognize that answer, so I'm gonna kill the program just in case.")
            quit()
    ##

    if args.mode == 'single':
        from constructors import SingleBlock
        Chain = SingleBlock
    if args.mode == 'ten':
        from constructors import TenBlock
        Chain = TenBlock

    s_time = time.process_time()
    ChainStruc = Chain(Banner.wants)
    ChainStruc.generate()
    g_time = time.process_time() - s_time
    print(f'Generated: {g_time} s')

    if args.simulate:
        print('Input a number to simulate that many pulls')
        print('Input "one by one" to simulate sequential individual pulls')
        print('Input "breakpoint" to calculate a probability breakpoint')
        num_pulls = input(': ')
        checkquit(num_pulls)
        try:
            num_pulls = int(num_pulls)
        except ValueError:
            pass
        if isinstance(num_pulls, int) and num_pulls >= 0:
            ChainStruc.simulate(num_pulls)
            sim_time = time.process_time() - s_time
            print(f'Simulated: {sim_time} s')

        elif num_pulls == 'breakpoint':
            ChainStruc.onebyone(mode='auto')

        elif num_pulls == 'one by one':
            ChainStruc.onebyone()
            
        else:
            print('That was not a valid number of pulls.')
            print('Try a non-negative integer, "one by one", or "breakpoint" next time.')

    if args.calculate:
        ChainStruc.hitting_time()
        calc_time = time.process_time() - s_time
        print(f'Calculated: {calc_time} s')

    if args.tests:
        import diagnostics
        if args.mode == 'single':
            Test = diagnostics.SingleTester(Banner.wants)  
        if args.mode == 'ten':
            Test = diagnostics.TenTester(Banner.wants)
        Test.test_chains()
        if args.mode == 'ten':
            Test.image_tenpull()
        Test.test_struc()
        Test.image_struc()
        Test.show_error()
        diag_time = time.process_time() - s_time
        print(f'Diagnostics: {diag_time} s')



