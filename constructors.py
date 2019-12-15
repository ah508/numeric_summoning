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
    """Constructs the markov chain for single pulls.

    This class contains methods to construct several markov chains
    characterizing the results of singular pulls at each pity level.
    The information from these chains may then be synthesized into
    a much larger chain that characterizes the entire state space.
    Methods for performing certain operations, such as simulating
    a given number of pulls, or finding the time spent in transient
    states are also included.

    Attributes
    ----------
    TYPE : str
        Indicates what this chain is meant to handle, singles
        or tenpulls. May be needed for external methods.
    MAX_PITY : int
        Indicates the number of pulls needed to reach maximum
        pity for the forced pity break.
    BASE_5 : Decimal
        Denotes the base 5* rate.
    INC_5 : Decimal
        Denotes the increment to the 5* rate based on pity.
    wants : {dict}
        A nested dictionary of a particular format, listing
        information on the units that the user wants from the
        gacha.
    universe : FrozenMultiset
        A multiset characterizing the set of units desired
        from the gacha.
    indices : [FrozenMultiset]
        A list of FrozenMultisets that represents the greater
        block structure of the complete markov chain.
    chain_indices : [FrozenMultiset]
        A list of FrozenMultisets that represents the state
        space of the single pull markov chains.
    n_chain_db : {int : array}
        A dictionary that maps pity level to the correct single
        pull markov chain.
    s_chain : array
        The single pull markov chain for the forced pity break.
    block_struc : array
        A submatrix of the full markov chain containing only
        the transient states.
    full_struc : array
        The full markov chain, containing all of the information
        on transition probabilities to and from each state.
    absorption_p :
        The probability of absorption for a particular state
        of the markov chain. Appended to block_struc along with
        another similar vector to produce full_struc. This is
        made an attribute of the class so it can be used for
        diagnostics.

    Parameters
    ----------
    wants : {dict}
        A nested dictionary of a particular format, listing
        information on the units that the user wants from the
        gacha. This could conceivably be done manually, but
        generally it will be handled by the main program.
    """

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
        """Calls the constructor methods."""

        self.create_chains()
        self.construct_block()
        
    def construct_block(self):
        """Creates and concatonates blocks to form the markov chain.

        The states of the markov chain we wish to construct has a very
        simple structure that lends itself to iterative generation.
        The indices generated in __init__ are used as the axes of a
        block superstructure, where each block represents the set of
        states that you are transitioning into. The index of the
        vertical axis denotes your current block-set of states, and
        the index of the horizontal axis denotes the block-set of
        states you are transitioning into. Within each of these blocks,
        there is a common substructure defined by your pity rate, and
        the position of the block in the superstructure (read: the
        units attained in the transition to this state from your
        current state).

        This method handles the formation of the block superstructure,
        and calls get_block for the generation of the substructure
        within each block.
        """

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
        """Creates markov chains representing single pulls.

        This method constructs a markov chain containing information
        regarding the transitions between each state of possession, for
        a single pull, at a specific pity level. This is done for each
        pity level, and the chains are mapped to that pity level with a
        dictionary. A chain is also generated for the forced pity break
        that occurs at the 101st or 61st pull.
        """

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
        """Creates blocks used to construct the final markov chain.

        This method generates the substructure mentioned in
        construct_blocks. It uses the horizontal and vertical indices
        to determine which units are aquired in the transition to this
        set of states, and uses the rarities of the units acquired to
        determine the form of this particular block. The substates here
        are defined by pity rate, and the transition probabilities are
        retrieved from n_chain_db and s_chain. Please note that
        although the entries of this matrix are stochastic, it is
        merely a small part of a markov chain - not a markov chain
        itself.

        Parameters
        ----------
        horizontal : FrozenMultiset
            A multiset representing the horizontal index of the
            block superstructure under construction.
        vertical : FrozenMultiset
            A multiset representing the vertical index of the
            block superstructure under construction.

        Returns
        -------
        block : numpy array
            The matrix needed to fill the [vertical][horizontal]
            index of the block matrix under construction.
        """

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
        """Creates the vector of escape probabilities for the chain.

        Finds the probability of entering the final state of the
        markov chain from any particular state, and constructs two
        arrays to store that information.
        NOTE: This is achieved very lazily, so the probability of
        absorption for a particular state may end up being larger than
        it is supposed to be. In trial runs, this has not caused any
        failures in computation, but it could conceivably do so. This
        is intended to be fixed in a future update.

        Returns
        -------
        absorption_p : array
            An n x 1 array containing the escape probabilities
            of the full markov chain, where n is the vertical
            size of said markov chain.
        absorption_s : array
            An array that designates the final state as
            absorbing in the full markov chain.
        """

        absorption_p = np.zeros([len(self.block_struc), 1])
        absorption_s = np.zeros([1, len(self.block_struc) + 1])
        absorption_s[0][-1] = 1
        for row in range(0, len(self.block_struc)):
            absorption_p[row] = 1 - sum(self.block_struc[row])
        return absorption_p, absorption_s

    def hitting_time(self):
        """Finds the expected hitting time by inversion."""

        iden = np.eye(len(self.block_struc))
        subt = iden - self.block_struc
        final = np.linalg.inv(subt)
        t = sum(final[0])
        print(f'On average it will take {t} {self.TYPE}pulls to achieve the desired units.')

    def simulate(self, pull_num):
        """Simulates a given number of pulls.

        Parameters
        ----------
        pull_num : int
            The number of pulls to simulate.
        """

        simulated = np.linalg.matrix_power(self.full_struc, pull_num)
        index = self.indices + [self.universe]
        groups = len(index)-1
        self.output(simulated, groups, index)

    def onebyone(self, mode='manual'):
        """A method to simulate pulls one at a time.

        Determines the state of the markov chain at each step, and if
        desired displays the probability of being in each state at that
        step. NOTE: state here does not literally refer to all states
        of the markov chain - referring instead to the states of
        possesion that define the block superstructure of the chain.
        This method is also used to determine the number of steps
        needed to achieve a certain probability of being in the final
        absorbing state.

        Parameters
        ----------
        mode : str(='manual')
            Determines how the method is run, and what output
            it produces. 'manual' indicates that the user is
            to observe the output at each step, and 'auto'
            indicates that the user is not interested in the
            results of each step, and only wishes to know how
            many steps are needed to reach a certain
            probability of being in the final state.
        """

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
                    see_out = input('Press the enter key to see the breakdown. ')
                    checkquit(see_out)
                    self.output(curr, groups, index)
                pull_count += 1

    def output(self, step, groups, index):
        """Displays the probability of being in each state.

        Parameters
        ----------
        step : array
            The state of the markov chain at the current step.
            Note - does not care about the actual step count.
        groups : int
            The number of 'groups' that the states of the chain
            can be lumped into. Alternatively, the number of 
            states used to generate the block superstructure of
            the chain.
        index : [FrozenMultiset]
            A list of sets describing the states used to
            generate the block superstructure of the markov
            chain. Each of the actual states is assigned to
            one of these superstates for display purposes.
        """

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
        """Manual advancement of one-by-one pulls."""

        another_one = input(': ')
        checkquit(another_one)
        if another_one.lower() == 'stop':
            return True
        return False

    def disp_conv(self, index):
        """Provides prettier state displays.
        
        Parameters
        ----------
        index : [FrozenMultiset]
            A list of sets describing the states used to
            generate the block superstructure of the markov
            chain. Each of the actual states is assigned to
            one of these superstates for display purposes.
        
        Returns
        -------
        [str]
            A sorted list containing the simplified strings.
        """

        out = []
        for (element, multiplicity) in index.items():
            cons = element + '(' + str(multiplicity) + ')'
            out.append(cons)
        return sorted(out)
        

class TenBlock(SingleBlock):
    """Constructs the markov chain for ten pulls.

    A subclass of SingleBlock that instead constructs the markov chain
    for tenpulls. Many methods are reusable, but some require minor
    alterations to account for the differences. Methods are included to
    construct several markov chains representing the results of certain
    types of single pulls at a particular pity level, and those chains
    may then be used to simulate the results of a tenpull at said pity
    level. Then, those results can be synthesized into a much larger
    markov chain that characterizes the entire state space. Methods
    for simulating pulls and finding the time spent in transient states
    are also included.

    Attributes
    ----------
    TYPE : str
        Indicates what this chain is meant to handle, singles
        or tenpulls. May be needed for external methods.
    MAX_PITY : int
        Indicates the number of pulls needed to reach maximum
        pity for the forced pity break.
    BASE_5 : Decimal
        Denotes the base 5* rate.
    INC_5 : Decimal
        Denotes the increment to the 5* rate based on pity.
    wants : {dict}
        A nested dictionary of a particular format, listing
        information on the units that the user wants from the
        gacha.
    universe : FrozenMultiset
        A multiset characterizing the set of units desired
        from the gacha.
    indices : [FrozenMultiset]
        A list of FrozenMultisets that represents the greater
        block structure of the complete markov chain.
    chain_indices : [FrozenMultiset]
        A list of FrozenMultisets that represents the state
        space of the single pull markov chains.
    n_chain_db : {int : array}
        A dictionary that maps pity level to the correct single
        pull markov chain.
    a_chain_db : {int : array}
        A dictionary that maps pity level to the correct
        alternative single pull markov chain.
    s_chain : array
        The single pull markov chain for the forced pity break.
    tenpull : {int : array}
        Maps pity level to the results of a 'simulated' tenpull
        at that pity level.
    block_struc : array
        A submatrix of the full markov chain containing only
        the transient states.
    full_struc : array
        The full markov chain, containing all of the information
        on transition probabilities to and from each state.
    absorption_p :
        The probability of absorption for a particular state
        of the markov chain. Appended to block_struc along with
        another similar vector to produce full_struc. This is
        made an attribute of the class so it can be used for
        diagnostics.

    Parameters
    ----------
    wants : {dict}
        A nested dictionary of a particular format, listing
        information on the units that the user wants from the
        gacha. This could conceivably be done manually, but
        generally it will be handled by the main program.
    """

    def __init__(self, wants):
        super().__init__(wants)
        self.TYPE = 'ten'

    def generate(self):
        """Calls the constructor methods."""

        self.create_chains()
        self.create_a_chains()
        self.find_p()
        self.construct_block()

    def find_p(self):
        """Creates and stores the outcomes of tenpulls for pity levels.

        Calls the sim_tenpull method to generate the results of a
        tenpull at a particular pity level, and maps those results
        to that pity level.
        """

        self.tenpull = {}
        for pity in range(0, MAX_PITY + 2):
            self.tenpull[pity] = self.sim_tenpull(pity)

    def sim_tenpull(self, pity):
        """Simulates the results of a tenpull given initial pity.

        'Simulates' a tenpull using a (somewhat ill defined)
        inhomogenous markov chain. This gives the conditional
        probabilities of being in each state at the end of a tenpull
        given that you started in a particular state.

        Parameters
        ----------
        pity : int
            Specifies the given pity level.

        Returns
        -------
        array
            The results of the simulated tenpull.
        """

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
        """Creates blocks used to construct the final markov chain.

        This method generates the substructure mentioned in
        construct_blocks. It uses the horizontal and vertical indices
        to determine which units are aquired in the transition to this
        set of states, and uses the rarities of the units acquired to
        determine the form of this particular block. The substates here
        are defined by pity rate, and the transition probabilities are
        retrieved from the tenpull dictionary. Please note that
        although the entries of this matrix are stochastic, it is
        merely a small part of a markov chain - not a markov chain
        itself.

        Parameters
        ----------
        horizontal : FrozenMultiset
            A multiset representing the horizontal index of the
            block superstructure under construction.
        vertical : FrozenMultiset
            A multiset representing the vertical index of the
            block superstructure under construction.

        Returns
        -------
        block : numpy array
            The matrix needed to fill the [vertical][horizontal]
            index of the block matrix under construction.
        """

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
        """Creates the vector of escape probabilities for the chain.

        Finds the probability of entering the final state of the
        markov chain from any particular state, and constructs two
        arrays to store that information.
        NOTE: Unlike SingleBlock, this is not done lazily, and should
        not cause any issues.

        Returns
        -------
        absorption_p : array
            An n x 1 array containing the escape probabilities
            of the full markov chain, where n is the vertical
            size of said markov chain.
        absorption_s : array
            An array that designates the final state as
            absorbing in the full markov chain.
        """

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
        """Creates a markov chain for the final pull of a tenpull.

        Generates a markov chain defining the transition probabilities
        between possesion states for the final pull of a tenpull.
        """

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