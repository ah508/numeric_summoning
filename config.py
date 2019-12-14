"""Configuration settings.

This file isn't as fleshed out as I expected it to be. Most of
this stuff gets overwritten in the main program anyway.

Attributes
----------
MODE : str
    Indicates whether to use floats or decimals for the majority
    of operations. Floats are *significantly* faster, and the
    loss in accuracy is nearly imperceptible, so they are the
    default.
MAX_PITY : int
    The number of tenpulls (not singles) needed to reach maximum pity.
BASE_5 : Decimal
    The base rate of pulling any 5*.
INC_5 : Decimal
    The incriment in 5* rate per tenpull. Currently irrelevant,
    but could hypothetically be altered on future banners.
"""

import decimal
from decimal import Decimal as Dec
decimal.getcontext()
MODE = 'Approximate' #Approximate, Accurate
MAX_PITY = 10
BASE_5 = Dec('.04')
INC_5 = Dec('.005')