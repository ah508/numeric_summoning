import numpy as np
import itertools
import decimal
import pprint
import time
from multiset import Multiset, FrozenMultiset
from config import MAX_PITY, BASE_5, INC_5, MODE
from banner_ops import checkquit
Dec = decimal.Decimal
decimal.getcontext()

class SingleBlock:
    def __init__(self, wants):
        self.TYPE = 'single'
        self.MAX_PITY = MAX_PITY
        self.BASE_5 = BASE_5
        self.INC_5 = INC_5
        self.wants = wants
        self.universe = Multiset()
        for unit in wants.keys():
            for i in range(0, wants[unit]['number']):
                self.universe.update([unit])
        self.universe = FrozenMultiset(self.universe)
        self.indices = []
        for i in range(0, len(self.universe)):
            for j in itertools.combinations(self.universe, i):
                if FrozenMultiset(j) not in self.indices:
                    self.indices.append(FrozenMultiset(j))

    def generate(self):
        self.create_chains()
        self.construct_block()
        
    def construct_block(self):
        self.block_struc = np.array([])
        for vertical in self.indices:
            horz = np.array([])
            for horizontal in reversed(self.indices):
                block = self.get_block(horizontal, vertical)
                try:
                    horz = np.hstack((block, horz))
                except ValueError:
                    horz = block
            try:
                self.block_struc = np.vstack((self.block_struc, horz))
            except ValueError: 
                self.block_struc = horz
        self.absorption_p, absorption_s = self.get_end()
        self.full_struc = np.hstack((self.block_struc, self.absorption_p))
        self.full_struc = np.vstack((self.full_struc, absorption_s))

    def create_chains(self):
        state_set = self.universe | frozenset('5')
        self.chain_indices = []
        for i in range(0, len(state_set)):
            for j in itertools.combinations(state_set, i):
                if FrozenMultiset(j) not in self.chain_indices:
                    self.chain_indices.append(FrozenMultiset(j))
        self.chain_indices.append(state_set)
        c_ref = self.chain_indices
        self.n_chain_db = {}
        for pity in range(0, MAX_PITY + 2):
            if MODE == 'Accurate':
                n_chain = np.zeros([len(self.chain_indices), len(self.chain_indices)], dtype=np.dtype(Dec))
            if MODE == 'Approximate':
                n_chain = np.zeros([len(self.chain_indices), len(self.chain_indices)])
            for vertical in self.chain_indices:
                available = state_set - vertical
                rate_5 = BASE_5 + pity*INC_5
                cover = set()
                n_rate_none = 1
                for unit in available:
                    if unit not in cover:
                        try:
                            if self.wants[unit]['rarity'] == '5':
                                rate_5 -= self.wants[unit]['base prob'] + pity*self.wants[unit]['prob inc']
                                cover.update([unit])
                        except KeyError:
                            pass
                for horizontal in reversed(self.chain_indices):
                    acquisition = horizontal - vertical
                    if len(acquisition) > 1:
                        pass
                    elif horizontal == vertical:
                        n_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = n_rate_none
                    elif acquisition == frozenset():
                        pass
                    elif acquisition <= available and len(horizontal) == len(vertical) + 1:
                        attained = next(iter(acquisition))
                        if attained == '5':
                            n_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = rate_5
                            n_rate_none -= rate_5
                        elif self.wants[attained]['rarity'] == '5':
                            rate = self.wants[attained]['base prob'] + pity*self.wants[attained]['prob inc']
                            n_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = rate
                            n_rate_none -= rate
                        else:
                            rate = self.wants[attained]['base prob'] + pity*self.wants[attained]['prob inc']
                            n_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = rate
                            n_rate_none -= rate
            self.n_chain_db[pity] = n_chain
        if MODE == 'Accurate':
            self.s_chain = np.zeros([len(self.chain_indices), len(self.chain_indices)], dtype=np.dtype(Dec))
        elif MODE == 'Approximate':
            self.s_chain = np.zeros([len(self.chain_indices), len(self.chain_indices)])
        for vertical in self.chain_indices:
            available = state_set - vertical
            cover = set()
            s_rate_5 = 1
            s_rate_none = 1
            for unit in available:
                if unit not in cover:
                    try:
                        if self.wants[unit]['rarity'] == '5':
                            s_rate_5 -= self.wants[unit]['spec prob']
                            cover.update([unit])
                    except KeyError:
                        pass
            for horizontal in reversed(self.chain_indices):
                acquisition = horizontal - vertical
                if len(acquisition) > 1:
                    pass
                elif horizontal == vertical:
                    self.s_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = s_rate_none
                elif acquisition == frozenset():
                    pass
                elif acquisition <= available and len(horizontal) == len(vertical) + 1:
                    attained = next(iter(acquisition))
                    if attained == '5':
                        self.s_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = s_rate_5
                        s_rate_none -= s_rate_5
                    elif self.wants[attained]['rarity'] == '5':
                        self.s_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = self.wants[attained]['spec prob']
                        s_rate_none -= self.wants[attained]['spec prob']

    def get_block(self, horizontal, vertical):
        gained = horizontal - vertical
        block = np.zeros([MAX_PITY*10 + 2, MAX_PITY*10 + 2])
        if len(gained) > 1:
            pass
        else:
            flag_5 = False
            for unit in gained:
                if self.wants[unit]['rarity'] == '5':
                    flag_5 = True
            vert_index = self.chain_indices.index(vertical)
            horz_non_index = self.chain_indices.index(horizontal)
            horz_5_index = self.chain_indices.index(horizontal | frozenset('5'))
            for pity in range(0, MAX_PITY*10 + 2):
                if pity == 0:
                    pity_shift = 1
                else:
                    pity_shift = pity
                if flag_5 and pity != MAX_PITY*10 + 1:
                    block[pity][0] = (self.n_chain_db[(pity_shift-1)//10][vert_index][horz_5_index] 
                                    + self.n_chain_db[(pity_shift-1)//10][vert_index][horz_non_index])
                elif flag_5 and pity == MAX_PITY*10 + 1:
                    block[pity][0] = (self.s_chain[vert_index][horz_5_index]
                                    + self.s_chain[vert_index][horz_non_index])
                elif pity < MAX_PITY*10 + 1:
                    block[pity][0] = self.n_chain_db[(pity_shift-1)//10][vert_index][horz_5_index]
                    block[pity][pity + 1] = self.n_chain_db[(pity_shift-1)//10][vert_index][horz_non_index]
                elif pity == MAX_PITY*10 + 1:
                    block[pity][0] = self.s_chain[vert_index][horz_5_index]
        return block

    def get_end(self): #note: find some way to make this more accurate
        absorption_p = np.zeros([len(self.block_struc), 1])
        absorption_s = np.zeros([1, len(self.block_struc) + 1])
        absorption_s[0][-1] = 1
        for row in range(0, len(self.block_struc)):
            absorption_p[row] = 1 - sum(self.block_struc[row])
        return absorption_p, absorption_s

    def hitting_time(self):
        iden = np.eye(len(self.block_struc))
        subt = iden - self.block_struc
        final = np.linalg.inv(subt)
        t = sum(final[0])
        print(f'On average it will take {t} {self.TYPE}pulls to achieve the desired units.')

    def simulate(self, pull_num):
        simulated = np.linalg.matrix_power(self.full_struc, pull_num)
        index = self.indices + [self.universe]
        groups = len(index)-1

        self.output(simulated, groups, index)

        # sim_res = simulated[0]
        # parts = len(sim_res)-1
        # chunk = parts//groups
        # n=0
        # for i in range(0, groups):
        #     if i == 0:
        #         attained = ['None']
        #     else:
        #         attained = self.disp_conv(index[i])
        #     print(f'P{attained} = {sum(sim_res[n:n+chunk])*100}%')
        #     n=n+chunk
        # print(f'P{self.disp_conv(index[-1])} = {sim_res[-1]*100}%')

    def onebyone(self, mode='manual'):
        pull_count = 0
        step = np.copy(self.full_struc)
        initial = np.zeros([len(step), len(step)]) 
        initial[0][0] = 1
        index = self.indices + [self.universe]
        groups = len(index)-1
        stop = False
        if mode == 'manual':
            print('Press enter to continue pulling.')
            print('Input "stop" when you wish to stop.')
            stop = self.manual_proceed()
            while not stop:
                if pull_count == 0:
                    self.output(initial, groups, index)
                elif pull_count == 1:
                    self.output(step, groups, index)
                else:
                    step = self.full_struc @ step
                    self.output(step, groups, index)
                print(pull_count)
                pull_count += 1
                stop = self.manual_proceed()
        elif mode == 'auto':
            correct = False
            while not correct:
                b_prob = input('Please enter your desired probability of success: ')
                checkquit(b_prob)
                try:
                    d_prob = float(b_prob)
                except ValueError:
                    print('You must enter a number.')
                    continue
                if d_prob > 1:
                    print('You can not have a probability greater than 1.')
                elif d_prob == 1:
                    print('A 100 percent success rate is unreasonable.')
                elif d_prob < 0:
                    print('You can not have a probability less than 0.')
                elif 0 <= d_prob < 1:
                    correct = True
                    print('OK.')
                else:
                    print("That input should be valid, but it isn't. Try again.")
            while not stop:
                if pull_count == 0:
                    success = 0
                    curr = initial
                elif pull_count == 1:
                    success = step[0][len(step)-1]
                    curr = step
                else:
                    step = self.full_struc @ step
                    success = step[0][len(step)-1]
                    curr = step
                if success >= float(b_prob):
                    stop = True
                    print(f'It should take you {pull_count} pulls to achieve the desired success rate.')
                    see_out = input('Press the enter key to see the breakdown. Input "stop" if you would like to skip the breakdown. ')
                    checkquit(see_out)
                    if see_out != 'stop':
                        self.output(curr, groups, index)
                pull_count += 1

    def output(self, step, groups, index):
        probs = step[0]
        parts = len(probs)-1
        chunk = parts//groups
        n=0
        for i in range(0, groups):
            if i == 0:
                attained = ['None']
            else:
                attained = self.disp_conv(index[i])
            print(f'P{attained} = {sum(probs[n:n+chunk])*100}%')
            n=n+chunk
        print(f'P{self.disp_conv(index[-1])} = {probs[-1]*100}%')
    
    def manual_proceed(self):
        another_one = input(': ')
        checkquit(another_one)
        if another_one.lower() == 'stop':
            return True
        return False

    def disp_conv(self, index):
        out = []
        for (element, multiplicity) in index.items():
            cons = element + '(' + str(multiplicity) + ')'
            out.append(cons)
        return sorted(out)
        

class TenBlock(SingleBlock):
    def __init__(self, wants):
        super().__init__(wants)
        self.TYPE = 'ten'

    def generate(self):
        self.create_chains()
        self.create_a_chains()
        self.find_p()
        self.construct_block()

    def find_p(self):
        self.tenpull = {}
        for pity in range(0, MAX_PITY + 2):
            self.tenpull[pity] = self.sim_tenpull(pity)

    def sim_tenpull(self, pity):
        if pity == MAX_PITY + 1:
            first = self.s_chain
            mid = np.linalg.matrix_power(self.n_chain_db[0], 8)
            end = self.a_chain_db[0]
        else:
            first = self.n_chain_db[pity]
            mid = np.linalg.matrix_power(self.n_chain_db[pity], 8)
            end = self.a_chain_db[pity]
        return np.linalg.multi_dot([first, mid, end])

    def get_block(self, horizontal, vertical):
        block = np.zeros([MAX_PITY + 2, MAX_PITY + 2])
        gained = horizontal - vertical
        flag_5 = False
        for unit in gained:
            if self.wants[unit]['rarity'] == '5':
                flag_5 = True
        vert_index = self.chain_indices.index(vertical)
        horz_non_index = self.chain_indices.index(horizontal)
        horz_5_index = self.chain_indices.index(horizontal | frozenset('5'))
        for pity in range(0, MAX_PITY + 2):
            if flag_5:
                block[pity][0] = (self.tenpull[pity][vert_index][horz_5_index] 
                                + self.tenpull[pity][vert_index][horz_non_index])
            elif pity < MAX_PITY + 1:
                block[pity][0] = self.tenpull[pity][vert_index][horz_5_index]
                block[pity][pity + 1] = self.tenpull[pity][vert_index][horz_non_index]
            elif pity == MAX_PITY + 1:
                block[pity][0] = self.tenpull[pity][vert_index][horz_5_index]
        return block

    def get_end(self):
        absorption_p = []
        absorption_s = np.zeros([1, len(self.block_struc) + 1])
        absorption_s[0][-1] = 1
        non_index = self.chain_indices.index(self.universe)
        five_index = self.chain_indices.index(self.universe | frozenset('5'))
        for vertical in self.indices:
            vert_index = self.chain_indices.index(vertical)
            column = np.zeros([MAX_PITY + 2, 1])
            for pity in range(0, MAX_PITY + 2):
                column[pity] = (self.tenpull[pity][vert_index][non_index] + self.tenpull[pity][vert_index][five_index])
            try:
                absorption_p = np.vstack((absorption_p, column))
            except ValueError: 
                absorption_p = column
        return absorption_p, absorption_s
    
    def create_a_chains(self):
        state_set = self.universe | frozenset('5')
        c_ref = self.chain_indices
        self.a_chain_db = {}
        for pity in range(0, MAX_PITY + 2):
            if MODE == 'Accurate':
                a_chain = np.zeros([len(self.chain_indices), len(self.chain_indices)], dtype=np.dtype(Dec))
            elif MODE == 'Approximate':
                a_chain = np.zeros([len(self.chain_indices), len(self.chain_indices)])
            for vertical in self.chain_indices:
                available = state_set - vertical
                rate_5 = BASE_5 + pity*INC_5
                cover = set()
                a_rate_none = 1
                for unit in available:
                    if unit not in cover:
                        try:
                            if self.wants[unit]['rarity'] == '5':
                                rate_5 -= self.wants[unit]['base prob'] + pity*self.wants[unit]['prob inc']
                                cover.update([unit])
                        except KeyError:
                            pass
                for horizontal in reversed(self.chain_indices):
                    acquisition = horizontal - vertical
                    if len(acquisition) > 1:
                        pass
                    elif horizontal == vertical:
                        a_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = a_rate_none
                    elif acquisition == frozenset():
                        pass
                    elif acquisition <= available and len(horizontal) == len(vertical) + 1:
                        attained = next(iter(acquisition))
                        if attained == '5':
                            a_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = rate_5
                            a_rate_none -= rate_5
                        elif self.wants[attained]['rarity'] == '5':
                            rate = self.wants[attained]['base prob'] + pity*self.wants[attained]['prob inc']
                            a_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = rate
                            a_rate_none -= rate
                        else:
                            a_rate = self.wants[attained]['alt prob'] + pity*self.wants[attained]['alt inc']
                            a_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = a_rate
                            a_rate_none -= a_rate
            self.a_chain_db[pity] = a_chain
    
    
# grundlespite = {
#     'Akasha': {
#         'base prob' : Dec('.005'),
#         'alt prob' : Dec('.005'),
#         'spec prob' : Dec('.125'),
#         'prob inc' : Dec('.000639'),
#         'alt inc' : Dec('.000639'),
#         'rarity' : 5, 
#         'number' : 2
#         },
#     'WXania' : {
#         'base prob' : Dec('.02333'),
#         'alt prob' : Dec('.14001'),
#         'spec prob' : Dec('0'),
#         'prob inc' : Dec('0'),
#         'alt inc' : Dec('-.00073'),
#         'rarity' : 4,
#         'number' : 1
#     #     },
#     # 'Sylas' : {
#     #     'base prob' : Dec('.005'),
#     #     'alt prob' : Dec('.005'),
#     #     'spec prob' : Dec('.125'),
#     #     'prob inc' : Dec('.000639'),
#     #     'alt inc' : Dec('.000639'),
#     #     'rarity' : 5,
#     #     'number' : 1
#         }
#     }

# s_time = time.process_time()
# np.set_printoptions(precision=3)
# test = TenBlock(grundlespite)
# # test = SingleBlock(grundlespite)
# test.generate()
# print('constructed:')
# print(time.process_time() - s_time)
# testfix = Testers(test)
# # testfix.test_tenpull()
# testfix.show_individ_error(0.001)
# testfix.show_error()
# test.hitting_time()
# test.simulate(18)
# print('solved:')
# print(time.process_time() - s_time)