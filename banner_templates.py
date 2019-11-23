import decimal
decimal.getcontext()
Dec = decimal.Decimal

Default = {
    '5' : {
        'Focus' : {
            'rate' : Dec('0.018'),
            'adventurer' :  [5, 9],
            'dragon' : [4, 9]
        },
        'Non Focus' : {
            'rate' : Dec('0.022'),
            'adventurer' : [5, 11],
            'dragon' : [6, 11]
        }
    },
    '4' : {
        'Focus' : {
            'rate' : Dec('0.07'),
            'adventurer' : [2, 3],
            'dragon' : [1, 3]
        },
        'Non Focus' : {
            'rate' : Dec('0.09'),
            'adventurer' : [101, 180],
            'dragon' : [79, 180]
        }
    },
    '3' : {
        'Focus' : { #note, may not be accurtate
            'rate' : Dec('0'),
            'adventurer' : [1, 2],
            'dragon' : [1, 2]
        },
        'Non Focus' : {
            'rate' : Dec('0.80'),
            'adventurer' : [3, 5],
            'dragon' : [2, 5]
        }
    }
}

Gala = {
    '5' : {
        'Focus' : {
            'rate' : Dec('0.018'),
            'adventurer' :  Dec(5/9),
            'dragon' : Dec(4/9)
        },
        'Non Focus' : {
            'rate' : Dec('0.022'),
            'adventurer' : Dec(5/11),
            'dragon' : Dec(6/11)
        }
    },
    '4' : {
        'Focus' : {
            'rate' : Dec('0.07'),
            'adventurer' : Dec(2/3),
            'dragon' : Dec(1/3)
        },
        'Non Focus' : {
            'rate' : Dec('0.09'),
            'adventurer' : Dec(101/180),
            'dragon' : Dec(79/180)
        }
    },
    '3' : {
        'Focus' : { #note, may not be accurtate
            'rate' : Dec('0'),
            'adventurer' : Dec(1/2),
            'dragon' : Dec(1/2)
        },
        'Non Focus' : {
            'rate' : Dec('0.80'),
            'adventurer' : Dec(3/5),
            'dragon' : Dec(2/5)
        }
    }
}