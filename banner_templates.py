"""Templates for banners

Please note that the information contained here may be incomplete
or inaccurate. Do not assume that my handling of rates is identical
to how Cygames handles rates.

Attributes
----------
default_no_3f : dict
    'default, no 3* focus'
default_gala : dict
    'default gala'
dyule_refocus : dict
    the second dragonyule banner, which featured the units from
    the previous year as additional focuses. The rates were
    abnormal, so they're being recorded seperately.
"""

import decimal
decimal.getcontext()
Dec = decimal.Decimal

default_no_3f = {
    '5' : {
        'Focus' : {
            'base' : Dec('0.018'),
            'inc' : Dec('0.0033'),
            'adventurer' :  [5, 9],
            'dragon' : [4, 9]
        },
        'Non Focus' : {
            'base' : Dec('0.022'),
            'inc' : Dec('0.0017'),
            'adventurer' : [5, 11],
            'dragon' : [6, 11]
        }
    },
    '4' : {
        'Focus' : {
            'base' : Dec('0.07'),
            'inc' : Dec('0'),
            'adventurer' : [2, 3],
            'dragon' : [1, 3]
        },
        'Non Focus' : {
            'base' : Dec('0.09'),
            'inc' : Dec('0'),
            'adventurer' : [101, 180],
            'dragon' : [79, 180]
        }
    },
    '3' : {
        'Focus' : { #note, may not be accurtate
            'base' : Dec('0'),
            'inc' : Dec('0'),
            'adventurer' : [1, 2],
            'dragon' : [1, 2]
        },
        'Non Focus' : {
            'base' : Dec('0.8'),
            'inc' : Dec('-0.005'),
            'adventurer' : [3, 5],
            'dragon' : [2, 5]
        }
    },
    'max pity' : 10
}

default_gala = {
    '5' : {
        'Focus' : {
            'base' : Dec('0.005'),
            'inc' : Dec('0.0004'),
            'adventurer' :  [1, 1],
            'dragon' : [0, 1]
        },
        'Non Focus' : {
            'base' : Dec('0.055'),
            'inc' : Dec('0.0046'),
            'adventurer' : [5, 11],
            'dragon' : [6, 11]
        }
    },
    '4' : {
        'Focus' : {
            'base' : Dec('0'),
            'inc' : Dec('0'),
            'adventurer' : [2, 3],
            'dragon' : [1, 3]
        },
        'Non Focus' : {
            'base' : Dec('0.16'),
            'inc' : Dec('0'),
            'adventurer' : [171, 320],
            'dragon' : [149, 320]
        }
    },
    '3' : {
        'Focus' : { #note, may not be accurtate
            'base' : Dec('0'),
            'inc' : Dec('0'),
            'adventurer' : [1, 2],
            'dragon' : [1, 2]
        },
        'Non Focus' : {
            'base' : Dec('0.78'),
            'inc' : Dec('-0.005'),
            'adventurer' : [3, 5],
            'dragon' : [2, 5]
        }
    },
    'max pity' : 6
}

dyule_refocus = {
    '5' : {
        'Focus' : {
            'base' : Dec('0.026'),
            'inc' : Dec('0.0023'),
            'adventurer' :  [5, 13],
            'dragon' : [8, 13]
        },
        'Non Focus' : {
            'base' : Dec('0.014'),
            'inc' : Dec('0.0027'),
            'adventurer' : [5, 7],
            'dragon' : [2, 7]
        }
    },
    '4' : {
        'Focus' : {
            'base' : Dec('0.07'),
            'inc' : Dec('0'),
            'adventurer' : [3, 4],
            'dragon' : [1, 4]
        },
        'Non Focus' : {
            'base' : Dec('0.09'),
            'inc' : Dec('0'),
            'adventurer' : [101, 180],
            'dragon' : [79, 180]
        }
    },
    '3' : {
        'Focus' : { #note, may not be accurtate
            'base' : Dec('0'),
            'inc' : Dec('0'),
            'adventurer' : [1, 2],
            'dragon' : [1, 2]
        },
        'Non Focus' : {
            'base' : Dec('0.8'),
            'inc' : Dec('-0.005'),
            'adventurer' : [3, 5],
            'dragon' : [2, 5]
        }
    },
    'max pity' : 10
}


#NOTE: the nonfocus 4* rate is really weird. the true value is
#probably something else entirely.