import numpy as np
import itertools
import decimal
from decimal import Decimal
import pprint
import time

class BlockGenerator:
    def __init__(self, wants):
        self.wants = wants
        # print(wants.keys())
        self.universe = frozenset(wants.keys())
        self.indices = []
        self.blockmap = {}
        self.endmap = {}
        for i in range(0, len(self.universe)):
            for j in itertools.combinations(self.universe, i):
                self.indices.append(frozenset(j))
        
        self.bloc_struc = np.array([])
        self.end_col = np.array([])
        self.precomp_blocks()
        for vertical in self.indices:
            horz = np.array([])
            need = self.universe - vertical
            gained_list = {}
            final = self.endmap[need]
            for horizontal in reversed(self.indices):
                gain = horizontal - vertical
                if vertical == horizontal:
                    block = self.comp_block(need)
                elif horizontal > vertical:
                    block = self.blockmap[gain]
                    block -= final
                    for prehandled in gained_list.keys():
                        if prehandled > horizontal:
                            block -= gained_list[prehandled]
                    gained_list[horizontal] = block      
                else:
                    block = self.blockmap[frozenset()]
                try:
                    horz = np.hstack((block, horz))
                except ValueError:
                    horz = block
            try:
                self.bloc_struc = np.vstack((self.bloc_struc, horz))
            except ValueError: 
                self.bloc_struc = horz
            try:
                self.end_col = np.vstack((self.end_col, final))
            except ValueError:
                self.end_col = final
        self.megablock = np.hstack((self.bloc_struc, self.end_col))
    
    def comp_block(self, need):
        block = np.zeros([12,12]) #placeholder
        for pity in range(0, len(block)):
            p_break, p_diag = self.find_p(need, pity, get=False)
            if pity < len(block) - 1:
                block[pity][pity+1] = p_diag
                block[pity][0] = p_break
            else:
                block[pity][0] = p_break + p_diag
        return block

    def precomp_blocks(self):
        for index in (self.indices + [self.universe]):
            sub_block = np.zeros([12, 12]) #placeholder
            end_block = np.zeros([12, 12]) #alsoplaceholder
            if index != frozenset():
                for pity in range(0, len(sub_block)):
                    p_break, p_diag = self.find_p(index, pity)
                    if pity < len(sub_block) - 1:
                        sub_block[pity][pity+1] = p_diag
                        sub_block[pity][0] = p_break
                        end_block[pity][pity+1] = p_diag
                        end_block[pity][0] = p_break
                    else:
                        sub_block[pity][0] = p_break
                        end_block[pity][0] = p_break 
            self.blockmap[index] = sub_block
            self.endmap[index] = end_block

    def find_p(self, acquired, pity_level, get=True): # good god is this ugly. replace with markov chains or something.
        if not get:
            p_norm = 1
            p_alt = 1
            p_5_correct = []
            if pity_level < 11:
                for unit in acquired:
                    p_norm -= (self.wants[unit]['base prob'] + pity_level*self.wants[unit]['prob inc'])
                    p_alt -= (self.wants[unit]['alt prob'] + pity_level*self.wants[unit]['alt inc'])
                    if self.wants[unit]['rarity'] == 5:
                        p_5_correct.append((self.wants[unit]['base prob'] + pity_level*self.wants[unit]['prob inc']))
                p_forced = p_norm
                p_diag = (p_norm - ((.04 + pity_level*.005) - sum(p_5_correct)))**9
                p_diag *= (p_alt - ((.04 + pity_level*.005) - sum(p_5_correct)))
                #placeholder vals
            else:
                p_forced = 1
                for unit in acquired:
                    p_norm -= self.wants[unit]['base prob']
                    p_alt -= self.wants[unit]['alt prob']
                    p_forced -= self.wants[unit]['spec prob']
                p_diag = 0
            p_noget = p_forced*(p_norm**8)*p_alt
            p_break = p_noget - p_diag
            return p_break, p_diag
        
        else:
            p_diag = 0
            p_break = 0
            p_vec = []
            n_vec = []
            spec_vec = []
            order = []
            no_p = 1
            no_p_alt = 1
            flag_5 = False
            # print(acquired)
            for unit in acquired:
                order.append(unit)
                p_vec.append(self.wants[unit]['base prob'])
                n_vec.append(1)
                spec_vec.append(self.wants[unit]['prob inc'])
                no_p -= self.wants[unit]['spec prob']
                no_p_alt -= self.wants[unit]['alt prob']
            if pity_level < 11:
                spec_vec = [x*pity_level for x in spec_vec]
                p_vec = [sum(n) for n in zip(p_vec, spec_vec)]
                for unit in acquired:
                    no_p_alt -= pity_level*self.wants[unit]['alt inc']
                    if self.wants[unit]['rarity'] == 5:
                        flag_5 = True
                for i in range(0, len(p_vec)):
                    new_n = n_vec[:i] + [0] + n_vec[i+1:]
                    p_break += self.wants[order[i]]['alt prob']*self.recursive_p(p_vec, new_n, sum(new_n), pull_size=9)
                # print(p_vec)
                # print(n_vec)
                p_break += no_p_alt*self.recursive_p(p_vec, n_vec, sum(n_vec), pull_size=9)
                if flag_5:
                    return p_break, p_diag
                else:
                    p_get = 0
                    p_vec_alt = p_vec + [.04 + pity_level*.005]
                    n_vec_alt = n_vec + [1]
                    for i in range(0, len(p_vec_alt)):
                        new_n = n_vec_alt[:i] + [0] + n_vec_alt[i+1:]
                        ## ERROR HERE
                        if i < len(p_vec):
                            p_get += self.wants[order[i]]['alt prob']*self.recursive_p(p_vec_alt, new_n, sum(new_n), pull_size=9)
                        else:
                            p_get += p_vec_alt[-1]*self.recursive_p(p_vec_alt, new_n, sum(new_n), pull_size=9)
                    p_get += no_p_alt*self.recursive_p(p_vec_alt, n_vec_alt, sum(n_vec_alt), pull_size=9)
                    p_diag = p_break - p_get
                    return p_get, p_diag
                    
            else:
                for i in range(0, len(p_vec)):
                    new_n = n_vec[:i] + [0] + n_vec[i+1:]
                    for j in range(0, len(p_vec)):
                        if j >= len(p_vec)-1:
                            p_break += self.wants[order[i]]['spec prob']*no_p_alt*self.recursive_p(p_vec, new_n, sum(new_n), pull_size=8)
                        else:
                            new_n_alt = new_n[:j] + [0] + new_n[j+1:]
                            p_break += self.wants[order[i]]['spec prob']*self.wants[order[j]]['alt prob']*self.recursive_p(p_vec, new_n_alt, sum(new_n_alt), pull_size=8)
                for k in range(0, len(p_vec)):   
                    new_n_fin = n_vec[:k] + [0] + n_vec[k+1:]
                    p_break += no_p*self.wants[order[k]]['alt prob']*self.recursive_p(p_vec, new_n_fin, sum(new_n_fin), pull_size=8)
                p_break += no_p*no_p_alt*self.recursive_p(p_vec, n_vec, sum(n_vec), pull_size=8)
                return p_break, p_diag
    
    def choose(self, n, r):
        f = self.factorial
        return f(n)//(f(r)*f(n-r))

    def factorial(self, n):
        if n <= 1:
            return 1
        else:
            return n*self.factorial(n-1)

    def recursive_p(self, p, n, m, pull_size=10):
        if m == pull_size:
            _p = 1
            for i in range(0, len(p)):
                _p *= p[i]**n[i]
            return _p*pull_size
        else:
            _p = 1
            for i in range(0, len(p)):
                _p *= p[i]**n[i]
            end_p = _p*self.choose(pull_size, m)*(1-sum(p))**(pull_size-m)
            for i in range(0, len(p)):
                new_n = n[:i] + [n[i]+1] + n[i+1:]
                end_p += self.recursive_p(p, new_n, m+1, pull_size=pull_size)
            return end_p

    def test_pt_matrix(self):
        for i in range(0, len(self.bloc_struc)):
            print(f'{sum(self.bloc_struc[i])}')
        print('-----')
        for i in range(0, len(self.bloc_struc)):
            print(sum(self.megablock[i]))
            # if sum(self.bloc_struc[i]) != 1:
            #     print(f'error on row {i} : sums to {sum(self.bloc_struc[i])}')
    def hitting_time(self):
        iden = np.eye(len(self.bloc_struc))
        subt = iden - self.bloc_struc
        final = np.linalg.inv(subt)
        print(final[0])
        t = sum(final[0])
        print(t)
        
    
grundlespite = {
    'Akasha': {
        'base prob' : .005,
        'alt prob' : .005,
        'spec prob' : .125,
        'prob inc' : .000639,
        'alt inc' : .000639,
        'rarity' : 5
        },
    'WXania' : {
        'base prob' : .02333,
        'alt prob' : .14001,
        'spec prob' : 0,
        'prob inc' : 0,
        'alt inc' : -.00073,
        'rarity' : 4
        }
    }

s_time = time.process_time()

test = BlockGenerator(grundlespite)
print('generated:')
print(time.process_time() - s_time)
# test.test_pt_matrix()
# np.set_printoptions(precision=3)
# printer = pprint.PrettyPrinter()
# printer.pprint(test.endmap)
# print(test.universe)
# print(test.fullsize)
# print(test.bloc_struc)
# print(test.end_col)
test.hitting_time()
print('inverted:')
print(time.process_time() - s_time)

