import numpy as np
import itertools
import decimal
import pprint
import time
from multiset import Multiset, FrozenMultiset
from config import MAX_PITY, BASE_5, INC_5
Dec = decimal.Decimal
decimal.getcontext()

class BlockGenerator:
    def __init__(self, wants):
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
        
    def construct_block(self):
        self.create_chains()
        self.find_p()
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
            for i in range(0, MAX_PITY + 2):
                self.checkvec.append(self.tenpull[i][self.chain_indices.index(vertical)][self.chain_indices.index(self.universe | frozenset('5'))]
                                    + self.tenpull[i][self.chain_indices.index(vertical)][self.chain_indices.index(self.universe)])
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
        self.a_chain_db = {}
        for pity in range(0, MAX_PITY + 2):
            n_chain = np.zeros([len(self.chain_indices), len(self.chain_indices)], dtype=np.dtype(Dec))
            a_chain = np.copy(n_chain)
            for vertical in self.chain_indices:
                available = state_set - vertical
                rate_5 = BASE_5 + pity*INC_5
                n_rate_none = 1
                a_rate_none = 1
                for unit in available:
                    try:
                        if self.wants[unit]['rarity'] == 5:
                            rate_5 -= self.wants[unit]['base prob'] + pity*self.wants[unit]['prob inc']
                    except KeyError:
                        pass
                for horizontal in reversed(self.chain_indices):
                    acquisition = horizontal - vertical
                    if len(acquisition) > 1:
                        pass
                    elif horizontal == vertical:
                        n_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = n_rate_none
                        a_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = a_rate_none
                    elif acquisition == frozenset():
                        pass
                    elif acquisition <= available and len(horizontal) == len(vertical) + 1:
                        attained = next(iter(acquisition))
                        if attained == '5':
                            n_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = rate_5
                            a_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = rate_5
                            n_rate_none -= rate_5
                            a_rate_none -= rate_5
                        elif self.wants[attained]['rarity'] == 5:
                            rate = self.wants[attained]['base prob'] + pity*self.wants[attained]['prob inc']
                            n_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = rate
                            a_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = rate
                            n_rate_none -= rate
                            a_rate_none -= rate
                        else:
                            rate = self.wants[attained]['base prob'] + pity*self.wants[attained]['prob inc']
                            a_rate = self.wants[attained]['alt prob'] + pity*self.wants[attained]['alt inc']
                            n_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = rate
                            a_chain[c_ref.index(vertical)][c_ref.index(horizontal)] = a_rate
                            n_rate_none -= rate
                            a_rate_none -= a_rate
            self.n_chain_db[pity] = n_chain
            self.a_chain_db[pity] = a_chain
        self.s_chain = np.zeros([len(self.chain_indices), len(self.chain_indices)], dtype=np.dtype(Dec))
        for vertical in self.chain_indices:
            available = state_set - vertical
            s_rate_5 = 1
            s_rate_none = 1
            for unit in available:
                try:
                    if self.wants[unit]['rarity'] == 5:
                        s_rate_5 -= self.wants[unit]['spec prob']
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
        block = np.zeros([MAX_PITY + 2, MAX_PITY + 2]) #placeholder
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

    def get_end(self):
        absorption_p = np.zeros([len(self.block_struc), 1])
        absorption_s = np.zeros([1, len(self.block_struc) + 1])
        absorption_s[0][-1] = 1
        for row in range(0, len(self.block_struc)):
            absorption_p[row] = 1 - sum(self.block_struc[row])
        return absorption_p, absorption_s

    def test_pt_matrix(self):
        for row in self.full_struc:
            if sum(row) != 1:
                print(f'failure on {row}')
                print(f'equal to: {sum(row)}')

    def show_error(self):
        error = []
        for item in range(0, len(self.block_struc)):
            error.append(Dec(self.absorption_p[item][0]) - self.checkvec[item])
        print(f'Sum of row errors: {sum(error)}')
        print(f'Sum of squared row errors: {sum([x**2 for x in error])}')

    def hitting_time(self):
        iden = np.eye(len(self.block_struc))
        subt = iden - self.block_struc
        final = np.linalg.inv(subt)
        print(final[0])
        t = sum(final[0])
        print(t)

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
                attained = list(index[i])
            print(f'P{attained} = {sum(sim_res[n:n+chunk])*100}%')
            n=n+chunk
        print(f'P{list(index[-1])} = {sim_res[-1]*100}%')
        
    
grundlespite = {
    'Akasha': {
        'base prob' : Dec('.005'),
        'alt prob' : Dec('.005'),
        'spec prob' : Dec('.125'),
        'prob inc' : Dec('.000639'),
        'alt inc' : Dec('.000639'),
        'rarity' : 5,
        'number' : 1
        },
    'WXania' : {
        'base prob' : Dec('.02333'),
        'alt prob' : Dec('.14001'),
        'spec prob' : Dec('0'),
        'prob inc' : Dec('0'),
        'alt inc' : Dec('-.00073'),
        'rarity' : 4,
        'number' : 1
    #     },
    # 'Sylas' : {
    #     'base prob' : Dec('.005'),
    #     'alt prob' : Dec('.005'),
    #     'spec prob' : Dec('.125'),
    #     'prob inc' : Dec('.000639'),
    #     'alt inc' : Dec('.000639'),
    #     'rarity' : 5
        }
    }

s_time = time.process_time()
np.set_printoptions(precision=3)
test = BlockGenerator(grundlespite)
test.construct_block()
print('constructed:')
print(time.process_time() - s_time)
test.show_error()
test.hitting_time()
test.simulate(18)
print('solved:')
print(time.process_time() - s_time)