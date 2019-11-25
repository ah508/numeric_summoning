import numpy as np
import itertools
import decimal
import pprint
import time
from multiset import Multiset, FrozenMultiset
from config import MAX_PITY, BASE_5, INC_5, MODE
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
        self.checkvec = []
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
                            if self.wants[unit]['rarity'] == 5:
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
                        elif self.wants[attained]['rarity'] == 5:
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
                        if self.wants[unit]['rarity'] == 5:
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
                    elif self.wants[attained]['rarity'] == 5:
                        self.s_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = self.wants[attained]['spec prob']
                        s_rate_none -= self.wants[attained]['spec prob']

    def get_block(self, horizontal, vertical):
        gained = horizontal - vertical
        block = np.zeros([MAX_PITY*10 + 1, MAX_PITY*10 + 1])
        if len(gained) > 1:
            pass
        else:
            flag_5 = False
            for unit in gained:
                if self.wants[unit]['rarity'] == 5:
                    flag_5 = True
            vert_index = self.chain_indices.index(vertical)
            horz_non_index = self.chain_indices.index(horizontal)
            horz_5_index = self.chain_indices.index(horizontal | frozenset('5'))
            for pity in range(0, MAX_PITY*10 + 1):
                if flag_5 and pity != MAX_PITY*10:
                    block[pity][0] = (self.n_chain_db[pity//10][vert_index][horz_5_index] 
                                    + self.n_chain_db[pity//10][vert_index][horz_non_index])
                elif flag_5 and pity == MAX_PITY*10:
                    block[pity][0] = (self.s_chain[vert_index][horz_5_index]
                                    + self.s_chain[vert_index][horz_non_index])
                elif pity < MAX_PITY*10:
                    block[pity][0] = self.n_chain_db[pity//10][vert_index][horz_5_index]
                    block[pity][pity + 1] = self.n_chain_db[pity//10][vert_index][horz_non_index]
                elif pity == MAX_PITY*10:
                    block[pity][0] = self.s_chain[vert_index][horz_5_index]
        return block

    def get_end(self):
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
        sim_res = simulated[0]
        index = self.indices + [self.universe]
        groups = len(index)-1
        parts = len(sim_res)-1
        chunk = parts//groups
        n=0
        for i in range(0, groups):
            if i == 0:
                attained = ['None']
            else:
                attained = self.disp_conv(index[i])
            print(f'P{attained} = {sum(sim_res[n:n+chunk])*100}%')
            n=n+chunk
        print(f'P{self.disp_conv(index[-1])} = {sim_res[-1]*100}%')
    
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
            if self.wants[unit]['rarity'] == 5:
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
                            if self.wants[unit]['rarity'] == 5:
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
                        elif self.wants[attained]['rarity'] == 5:
                            rate = self.wants[attained]['base prob'] + pity*self.wants[attained]['prob inc']
                            a_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = rate
                            a_rate_none -= rate
                        else:
                            a_rate = self.wants[attained]['alt prob'] + pity*self.wants[attained]['alt inc']
                            a_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = a_rate
                            a_rate_none -= a_rate
            self.a_chain_db[pity] = a_chain
    

class Testers:
    def __init__(self, subject):
        self.subject = subject
        for vertical in self.subject.indices:
            if self.subject.TYPE == 'ten':
                for i in range(0, MAX_PITY + 2):
                    self.subject.checkvec.append(self.subject.tenpull[i][self.subject.chain_indices.index(vertical)][self.subject.chain_indices.index(self.subject.universe | frozenset('5'))]
                                                + self.subject.tenpull[i][self.subject.chain_indices.index(vertical)][self.subject.chain_indices.index(self.subject.universe)])
            elif self.subject.TYPE == 'single':
                for i in range(0, MAX_PITY*10):
                    self.subject.checkvec.append(self.subject.n_chain_db[i//10][self.subject.chain_indices.index(vertical)][self.subject.chain_indices.index(self.subject.universe | frozenset('5'))]
                                                + self.subject.n_chain_db[i//10][self.subject.chain_indices.index(vertical)][self.subject.chain_indices.index(self.subject.universe)])
                for i in range(MAX_PITY*10, MAX_PITY*10 + 1):
                    self.subject.checkvec.append(self.subject.s_chain[self.subject.chain_indices.index(vertical)][self.subject.chain_indices.index(self.subject.universe | frozenset('5'))]
                                                + self.subject.s_chain[self.subject.chain_indices.index(vertical)][self.subject.chain_indices.index(self.subject.universe)])

    def test_pt_matrix(self):
        for row in self.subject.full_struc:
            if sum(row) != 1:
                print(f'failure on {row}')
                print(f'equal to: {sum(row)}')

    def test_markov(self):
        for chain in self.subject.n_chain_db.keys():
            for i in range(0, len(self.subject.n_chain_db[chain])):
                if sum(self.subject.n_chain_db[chain][i]) != 1:
                    print(f'norm failure at pity {chain} with value {sum(self.subject.n_chain_db[chain][i])}')
        try:
            for chain in self.subject.a_chain_db.keys():
                for i in range(0, len(self.subject.a_chain_db[chain])):
                    if sum(self.subject.a_chain_db[chain][i]) != 1:
                        print(f'alt failure at pity {chain} on row {i} with value {sum(self.subject.a_chain_db[chain][i])}')
        except AttributeError:
            pass
        for i in range(0, len(self.subject.s_chain)):
            if sum(self.subject.s_chain[i]) != 1:
                print(f'spec failure on row {i} with value {sum(self.subject.a_chain_db[chain][i])}')

    def test_tenpull(self):
        try:
            for key in self.subject.tenpull.keys():
                for row in range(0, len(self.subject.tenpull[key])):
                    if sum(self.subject.tenpull[key][row]) != 1:
                        print(f'tenpull error at pity {key} on row {row} with value {1 - sum(self.subject.tenpull[key][row])}')
        except AttributeError:
            print('Not a valid test.')

    def show_error(self):
        error = []
        for item in range(0, len(self.subject.block_struc)):
            error.append(Dec(self.subject.absorption_p[item][0]) - self.subject.checkvec[item])
        print(f'Sum of row errors: {sum(error)}')
        print(f'Sum of squared row errors: {sum([x**2 for x in error])}')

    def show_individ_error(self, tolerance):
        error = []
        for item in range(0, len(self.subject.block_struc)):
            error.append(Dec(self.subject.absorption_p[item][0]) - self.subject.checkvec[item])
        for i in range(0, len(error)):
            if abs(error[i]) >= tolerance:
                print(f'error of {error[i]} on row {i}')
    
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