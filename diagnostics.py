import constructors
Ten = constructors.TenBlock
One = constructors.SingleBlock
import os
import numpy as np
import decimal
Dec = decimal.Decimal
decimal.getcontext()
from config import MAX_PITY, MODE
try:
    import PIL
    from PIL import Image
    pillowtalk = True
except ModuleNotFoundError:
    print('pillow not installed, imaging capabilities disabled')
    pillowtalk = False

class SingleTester(One):
    """Diagnostic methods for single pulls.

    Includes methods to test incongruencies in escape probabilities,
    test whether a chain is stochastic with some degree of tolerance,
    and generate images to check the structure of a particular feature.
    This is a subclass of SingleBlock, and as such inherits all of the
    same attributes and methods.

    Attributes
    ----------
    chain_gen : bool
        Indicates whether or not chains have been generated yet.
    block_gen : bool
        Indicates whether or not blocks have been generated yet.
    check_gen : bool
        Indicates whether or not the check vector has been
        generated yet.
    error_gen : bool
        Indicates whether or not row errors have been computed
        yet.

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
        self.clear()
        if not os.path.exists(os.getcwd() + '\\diagnostic_images'):
            os.makedirs(os.getcwd() + '\\diagnostic_images')
        if not os.path.exists(os.getcwd() + '\\diagnostic_images\\blocks'):
            os.makedirs(os.getcwd() + '\\diagnostic_images\\blocks')
        if not os.path.exists(os.getcwd() + '\\diagnostic_images\\chains'):
            os.makedirs(os.getcwd() + '\\diagnostic_images\\chains')
        self.chain_gen = False
        self.block_gen = False
        self.check_gen = False
        self.error_gen = False

    def clear(self):
        path = os.getcwd() + '\\diagnostic_images'
        for (directory, subdirectories, filenames) in os.walk(path):
            for filename in filenames:
                if filename.endswith('.png'):
                    os.remove(os.path.join(directory, filename))

    def imagesaver(self, initial_array, path):
        holding_array = np.copy(initial_array)
        for row in range(0, len(holding_array)):
            for entry in range(0, len(holding_array)):
                if holding_array[row][entry] != 0:
                    holding_array[row][entry] = 1
        holding_array = (255*holding_array).astype(np.uint8)
        holding_image = Image.fromarray(holding_array, 'L')
        holding_image.save(path)

    def tolerance_check(self, source, tolerance, fail_type):
        try:
            for chain in source.keys():
                for row in range(0, len(source[chain])):
                    if abs(sum(source[chain][row]) - 1) > tolerance:
                        print(f'{fail_type} failure at pity {chain} on row {row} with value {sum(source[chain][row])}')
        except AttributeError:
            for row in range(0, len(source)):
                if abs(sum(source[row]) - 1) > tolerance:
                    print(f'{fail_type} failure on row {row} with value {sum(source[row])}')
        
    def test_chains(self, tolerance=0.000001):
        self.create_chains()
        self.chain_gen = True
        self.tolerance_check(self.n_chain_db, tolerance, 'norm')
        self.tolerance_check(self.s_chain, tolerance, 'spec')
        self.image_chains()
        
    def image_chains(self):
        if pillowtalk:
            if not self.chain_gen:
                self.create_chains()
                self.chain_gen = True
            self.image_n_chains()
            self.image_s_chains()
        else:
            print('imaging is disabled.')
            print('if you want, you can write your own script to check them manually')
            print("but I don't recommend that")

    def image_n_chains(self):
        if pillowtalk:
            if not self.chain_gen:
                self.create_chains()
                self.chain_gen = True
            gen_path = os.getcwd() + '\\diagnostic_images\\chains'
            for pity_level in self.n_chain_db.keys():
                n_path = gen_path + '\\n_chain_' + str(pity_level) + '.png'
                self.imagesaver(self.n_chain_db[pity_level], n_path)

    def image_s_chains(self):
        if pillowtalk:
            if not self.chain_gen:
                self.create_chains()
                self.chain_gen = True
            s_path = os.getcwd() + '\\diagnostic_images\\chains\\s_chain.png'
            self.imagesaver(self.s_chain, s_path)
    
    def test_struc(self):
        if not self.chain_gen:
            self.create_chains()
            self.chain_gen = True
        if not self.block_gen:
            self.construct_block()
            self.block_gen = True
        self.checkvec = []
        for vertical in self.indices:
            self.checkvec.append(self.n_chain_db[0][self.chain_indices.index(vertical)][self.chain_indices.index(self.universe | frozenset('5'))]
                                + self.n_chain_db[0][self.chain_indices.index(vertical)][self.chain_indices.index(self.universe)])
            for i in range(1, MAX_PITY*10 + 1):
                self.checkvec.append(self.n_chain_db[(i-1)//10][self.chain_indices.index(vertical)][self.chain_indices.index(self.universe | frozenset('5'))]
                                    + self.n_chain_db[(i-1)//10][self.chain_indices.index(vertical)][self.chain_indices.index(self.universe)])
            self.checkvec.append(self.s_chain[self.chain_indices.index(vertical)][self.chain_indices.index(self.universe | frozenset('5'))]
                                + self.s_chain[self.chain_indices.index(vertical)][self.chain_indices.index(self.universe)])
        self.check_gen = True
        
    def image_struc(self):
        if pillowtalk:
            if not self.check_gen:
                self.test_struc()
                self.check_gen = True
            block_path = os.getcwd() + '\\diagnostic_images\\blocks\\block_struc.png'
            full_path = os.getcwd() + '\\diagnostic_images\\blocks\\full_struc.png'
            self.imagesaver(self.block_struc, block_path)
            self.imagesaver(self.full_struc, full_path)
        else:
            print('imaging is disabled.')
            print('if you want, you can write your own script to check them manually')
            print("but I don't recommend that")

    def error_loc(self):
        self.error = []
        for item in range(0, len(self.block_struc)):
            if MODE == 'Accurate':
                self.error.append(Dec(self.absorption_p[item][0]) - self.checkvec[item])
            else:
                self.error.append(self.absorption_p[item][0] - self.checkvec[item])
        self.error_gen = True
        
    def show_error(self):
        if not self.check_gen:
            self.test_struc()
        if not self.error_gen:
            self.error_loc()
            self.error_gen = True
        print(f'Sum of row errors: {sum(self.error)}')
        print(f'Sum of squared row errors: {sum([x**2 for x in self.error])}')

    def show_individ_error(self, tolerance):
        if not self.check_gen:
            self.test_struc()
            self.check_gen = True
        if not self.error_gen:
            self.error_loc()
            self.error_gen = True
        for i in range(0, len(self.error)):
            if abs(self.error[i]) >= tolerance:
                print(f'error of {self.error[i]} on row {i}')
    
class TenTester(Ten, SingleTester):
    """Diagnostic methods for tenpulls.

    Includes methods to test incongruencies in escape probabilities,
    test whether a chain is stochastic with some degree of tolerance,
    and generate images to check the structure of a particular feature.
    This is a subclass of TenBlock, and as such inherits all of the
    same attributes and methods.

    Attributes
    ----------
    chain_gen : bool
        Indicates whether or not chains have been generated yet.
    a_chain_gen : bool
        Indicates whether or not alt chains have been generated
        yet.
    tenpull_gen : bool
        Indicates whether or not tenpulls have been computed
        yet.
    block_gen : bool
        Indicates whether or not blocks have been generated yet.
    check_gen : bool
        Indicates whether or not the check vector has been
        generated yet.
    error_gen : bool
        Indicates whether or not row errors have been computed
        yet.

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
        self.clear()
        if not os.path.exists(os.getcwd() + '\\diagnostic_images\\tens'):
            os.makedirs(os.getcwd() + '\\diagnostic_images\\tens')
        self.tenpull_gen = False
        self.a_chain_gen = False

    def test_chains(self, tolerance=0.000001):
        self.create_chains()
        self.create_a_chains()
        self.chain_gen = True
        self.a_chain_gen = True
        self.tolerance_check(self.n_chain_db, tolerance, 'norm')
        self.tolerance_check(self.a_chain_db, tolerance, 'alt')
        self.tolerance_check(self.s_chain, tolerance, 'spec')
        self.image_chains()

    def image_chains(self):
        if pillowtalk:
            if not self.chain_gen:
                self.create_chains()
            if not self.a_chain_gen:
                self.create_a_chains()
            self.image_n_chains()
            self.image_a_chains()
            self.image_s_chains()
        else:
            print('imaging is disabled.')
            print('if you want, you can write your own script to check them manually')
            print("but I don't recommend that")

    def image_a_chains(self):
        if pillowtalk:
            if not self.a_chain_gen:
                self.create_a_chains()
                self.a_chain_gen = True
            gen_path = os.getcwd() + '\\diagnostic_images\\chains'
            for pity_level in self.a_chain_db.keys():
                a_path = gen_path + '\\a_chain_' + str(pity_level) + '.png'
                self.imagesaver(self.a_chain_db[pity_level], a_path)

    def image_tenpull(self):
        if pillowtalk:
            gen_path = os.getcwd() + '\\diagnostic_images\\tens'
            self.find_p()
            for pity in range(0, MAX_PITY + 2):
                specific_path = gen_path + '\\pity_' + str(pity)
                end_path = specific_path + '\\sim.png'
                if not os.path.exists(specific_path):
                    os.makedirs(specific_path)
                self.recursive_image(10, pity, specific_path)
                self.imagesaver(self.tenpull[pity], end_path)
    
    def recursive_image(self, step, pity, file_path):
        if pity == 11:
            p_correct = 0
        else:
            p_correct = pity
        if step <= 1:
            if pity == 11:
                chain = self.s_chain
            else:
                chain = self.n_chain_db[pity]
        elif step == 10:
            chain = self.recursive_image(step-1, pity, file_path) @ self.a_chain_db[p_correct]
        elif step > 10:
            print("That's not supposed to be permitted.")
        else:
            chain = self.recursive_image(step-1, pity, file_path) @ self.n_chain_db[p_correct]
        path = file_path + '\\' + str(step) + '.png'
        self.imagesaver(chain, path)
        return chain

    def test_struc(self):
        if not self.chain_gen:
            self.create_chains()
            self.chain_gen = True
        if not self.a_chain_gen:
            self.create_a_chains()
            self.a_chain_gen = True
        if not self.tenpull_gen:
            self.find_p()
            self.tenpull_gen = True
        if not self.block_gen:
            self.construct_block()
            self.block_gen = True
        self.checkvec = []
        for i in range(0, len(self.block_struc)):
            self.checkvec.append(1 - sum(self.block_struc[i]))
        self.check_gen = True