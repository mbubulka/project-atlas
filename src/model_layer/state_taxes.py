"""
State Income Tax Calculator with Progressive Brackets

Source: 2025 Tax Foundation, State Tax Agency Websites, IRS Publication 17
https://taxfoundation.org/state-income-tax-rates-2024/

Implements proper progressive tax bracket calculations for all 50 states and DC.
Standard deductions and brackets based on 2025 tax year data.

Each state includes:
- Standard deduction (single, married joint, married separate, head of household)
- Progressive tax brackets for income-based states
- Flat rate for flat-tax states
- $0 for no income tax states
"""


def get_state_tax_brackets():
    """
    Return 2025 state income tax brackets for all 50 states and DC.

    Format: {
        'STATE': {
            'name': 'State Name',
            'standard_deduction': {'single': amount, 'married_joint': amount, ...},
            'type': 'progressive' | 'flat' | 'none',
            'brackets': [
                {'min': 0, 'max': amount, 'rate': 0.XX},
                ...
            ]
        }
    }
    """
    state_data = {
        "AL": {
            "name": "Alabama",
            "standard_deduction": {
                "single": 3900,
                "married_joint": 7800,
                "married_separate": 3900,
                "head_of_household": 5850,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 500, "rate": 0.02},
                {"min": 500, "max": 3000, "rate": 0.04},
                {"min": 3000, "max": 6000, "rate": 0.05},
                {"min": 6000, "max": float("inf"), "rate": 0.0575},
            ],
        },
        "AK": {
            "name": "Alaska",
            "standard_deduction": {
                "single": 0,
                "married_joint": 0,
                "married_separate": 0,
                "head_of_household": 0,
            },
            "type": "none",
            "brackets": [],
        },
        "AZ": {
            "name": "Arizona",
            "standard_deduction": {
                "single": 15000,
                "married_joint": 30000,
                "married_separate": 15000,
                "head_of_household": 22500,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 32350, "rate": 0.0259},
                {"min": 32350, "max": 81900, "rate": 0.0359},
                {"min": 81900, "max": 252450, "rate": 0.0449},
                {"min": 252450, "max": float("inf"), "rate": 0.0459},
            ],
        },
        "AR": {
            "name": "Arkansas",
            "standard_deduction": {
                "single": 4500,
                "married_joint": 9000,
                "married_separate": 4500,
                "head_of_household": 6750,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 4600, "rate": 0.02},
                {"min": 4600, "max": 9200, "rate": 0.04},
                {"min": 9200, "max": 14100, "rate": 0.0575},
                {"min": 14100, "max": float("inf"), "rate": 0.0675},
            ],
        },
        "CA": {
            "name": "California",
            "standard_deduction": {
                "single": 5202,
                "married_joint": 10404,
                "married_separate": 5202,
                "head_of_household": 7801,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 10099, "rate": 0.01},
                {"min": 10099, "max": 23942, "rate": 0.02},
                {"min": 23942, "max": 37788, "rate": 0.04},
                {"min": 37788, "max": 52455, "rate": 0.06},
                {"min": 52455, "max": 66295, "rate": 0.08},
                {"min": 66295, "max": 340328, "rate": 0.093},
                {"min": 340328, "max": 410042, "rate": 0.103},
                {"min": 410042, "max": 680656, "rate": 0.113},
                {"min": 680656, "max": float("inf"), "rate": 0.123},
            ],
        },
        "CO": {
            "name": "Colorado",
            "standard_deduction": {
                "single": 15000,
                "married_joint": 30000,
                "married_separate": 15000,
                "head_of_household": 22500,
            },
            "type": "flat",
            "brackets": [{"min": 0, "max": float("inf"), "rate": 0.0449}],
        },
        "CT": {
            "name": "Connecticut",
            "standard_deduction": {
                "single": 15000,
                "married_joint": 30000,
                "married_separate": 15000,
                "head_of_household": 22500,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 21600, "rate": 0.03},
                {"min": 21600, "max": 54000, "rate": 0.05},
                {"min": 54000, "max": 183150, "rate": 0.055},
                {"min": 183150, "max": float("inf"), "rate": 0.065},
            ],
        },
        "DE": {
            "name": "Delaware",
            "standard_deduction": {
                "single": 3250,
                "married_joint": 6500,
                "married_separate": 3250,
                "head_of_household": 4875,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 2000, "rate": 0.022},
                {"min": 2000, "max": 5000, "rate": 0.039},
                {"min": 5000, "max": 10000, "rate": 0.048},
                {"min": 10000, "max": 20000, "rate": 0.052},
                {"min": 20000, "max": float("inf"), "rate": 0.0655},
            ],
        },
        "FL": {
            "name": "Florida",
            "standard_deduction": {
                "single": 0,
                "married_joint": 0,
                "married_separate": 0,
                "head_of_household": 0,
            },
            "type": "none",
            "brackets": [],
        },
        "GA": {
            "name": "Georgia",
            "standard_deduction": {
                "single": 4100,
                "married_joint": 8200,
                "married_separate": 4100,
                "head_of_household": 6150,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 1000, "rate": 0.01},
                {"min": 1000, "max": 3000, "rate": 0.02},
                {"min": 3000, "max": 5000, "rate": 0.03},
                {"min": 5000, "max": 7000, "rate": 0.04},
                {"min": 7000, "max": 10000, "rate": 0.05},
                {"min": 10000, "max": float("inf"), "rate": 0.0575},
            ],
        },
        "HI": {
            "name": "Hawaii",
            "standard_deduction": {
                "single": 5400,
                "married_joint": 10800,
                "married_separate": 5400,
                "head_of_household": 8100,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 2400, "rate": 0.014},
                {"min": 2400, "max": 5600, "rate": 0.032},
                {"min": 5600, "max": 8800, "rate": 0.055},
                {"min": 8800, "max": 12000, "rate": 0.064},
                {"min": 12000, "max": 20000, "rate": 0.068},
                {"min": 20000, "max": float("inf"), "rate": 0.0685},
            ],
        },
        "ID": {
            "name": "Idaho",
            "standard_deduction": {
                "single": 15000,
                "married_joint": 30000,
                "married_separate": 15000,
                "head_of_household": 22500,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 1920, "rate": 0.01},
                {"min": 1920, "max": 4462, "rate": 0.03},
                {"min": 4462, "max": 7134, "rate": 0.04},
                {"min": 7134, "max": 10216, "rate": 0.05},
                {"min": 10216, "max": float("inf"), "rate": 0.0575},
            ],
        },
        "IL": {
            "name": "Illinois",
            "standard_deduction": {
                "single": 0,
                "married_joint": 0,
                "married_separate": 0,
                "head_of_household": 0,
            },
            "type": "flat",
            "brackets": [{"min": 0, "max": float("inf"), "rate": 0.0495}],
        },
        "IN": {
            "name": "Indiana",
            "standard_deduction": {
                "single": 0,
                "married_joint": 0,
                "married_separate": 0,
                "head_of_household": 0,
            },
            "type": "flat",
            "brackets": [{"min": 0, "max": float("inf"), "rate": 0.0315}],
        },
        "IA": {
            "name": "Iowa",
            "standard_deduction": {
                "single": 2340,
                "married_joint": 4680,
                "married_separate": 2340,
                "head_of_household": 3510,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 1902, "rate": 0.0405},
                {"min": 1902, "max": 9653, "rate": 0.0810},
                {"min": 9653, "max": float("inf"), "rate": 0.0925},
            ],
        },
        "KS": {
            "name": "Kansas",
            "standard_deduction": {
                "single": 3400,
                "married_joint": 6800,
                "married_separate": 3400,
                "head_of_household": 5100,
            },
            "type": "flat",
            "brackets": [{"min": 0, "max": float("inf"), "rate": 0.057}],
        },
        "KY": {
            "name": "Kentucky",
            "standard_deduction": {
                "single": 3190,
                "married_joint": 6380,
                "married_separate": 3190,
                "head_of_household": 4785,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 3100, "rate": 0.02},
                {"min": 3100, "max": 7500, "rate": 0.04},
                {"min": 7500, "max": float("inf"), "rate": 0.0575},
            ],
        },
        "LA": {
            "name": "Louisiana",
            "standard_deduction": {
                "single": 1250,
                "married_joint": 2500,
                "married_separate": 1250,
                "head_of_household": 1875,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 12500, "rate": 0.0175},
                {"min": 12500, "max": 50000, "rate": 0.03},
                {"min": 50000, "max": float("inf"), "rate": 0.06},
            ],
        },
        "ME": {
            "name": "Maine",
            "standard_deduction": {
                "single": 15000,
                "married_joint": 30000,
                "married_separate": 15000,
                "head_of_household": 22500,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 23000, "rate": 0.055},
                {"min": 23000, "max": float("inf"), "rate": 0.065},
            ],
        },
        "MD": {
            "name": "Maryland",
            "standard_deduction": {
                "single": 3750,
                "married_joint": 7500,
                "married_separate": 3750,
                "head_of_household": 5625,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 1000, "rate": 0.02},
                {"min": 1000, "max": 2000, "rate": 0.03},
                {"min": 2000, "max": 3000, "rate": 0.04},
                {"min": 3000, "max": 150000, "rate": 0.0475},
                {"min": 150000, "max": 250000, "rate": 0.05},
                {"min": 250000, "max": float("inf"), "rate": 0.0575},
            ],
        },
        "MA": {
            "name": "Massachusetts",
            "standard_deduction": {
                "single": 0,
                "married_joint": 0,
                "married_separate": 0,
                "head_of_household": 0,
            },
            "type": "flat",
            "brackets": [{"min": 0, "max": float("inf"), "rate": 0.05}],
        },
        "MI": {
            "name": "Michigan",
            "standard_deduction": {
                "single": 15000,
                "married_joint": 30000,
                "married_separate": 15000,
                "head_of_household": 22500,
            },
            "type": "flat",
            "brackets": [{"min": 0, "max": float("inf"), "rate": 0.0425}],
        },
        "MN": {
            "name": "Minnesota",
            "standard_deduction": {
                "single": 13850,
                "married_joint": 27700,
                "married_separate": 13850,
                "head_of_household": 20750,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 32110, "rate": 0.0535},
                {"min": 32110, "max": 82204, "rate": 0.068},
                {"min": 82204, "max": 174600, "rate": 0.0785},
                {"min": 174600, "max": float("inf"), "rate": 0.0985},
            ],
        },
        "MS": {
            "name": "Mississippi",
            "standard_deduction": {
                "single": 3150,
                "married_joint": 6300,
                "married_separate": 3150,
                "head_of_household": 4725,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 1000, "rate": 0.03},
                {"min": 1000, "max": 5000, "rate": 0.04},
                {"min": 5000, "max": float("inf"), "rate": 0.05},
            ],
        },
        "MO": {
            "name": "Missouri",
            "standard_deduction": {
                "single": 4200,
                "married_joint": 8400,
                "married_separate": 4200,
                "head_of_household": 6300,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 1000, "rate": 0.015},
                {"min": 1000, "max": 2000, "rate": 0.02},
                {"min": 2000, "max": 3000, "rate": 0.025},
                {"min": 3000, "max": 4000, "rate": 0.03},
                {"min": 4000, "max": 5000, "rate": 0.035},
                {"min": 5000, "max": 6000, "rate": 0.04},
                {"min": 6000, "max": float("inf"), "rate": 0.0575},
            ],
        },
        "MT": {
            "name": "Montana",
            "standard_deduction": {
                "single": 5700,
                "married_joint": 11400,
                "married_separate": 5700,
                "head_of_household": 8550,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 3300, "rate": 0.02},
                {"min": 3300, "max": 7900, "rate": 0.04},
                {"min": 7900, "max": 10200, "rate": 0.06},
                {"min": 10200, "max": float("inf"), "rate": 0.0675},
            ],
        },
        "NE": {
            "name": "Nebraska",
            "standard_deduction": {
                "single": 7250,
                "married_joint": 14500,
                "married_separate": 7250,
                "head_of_household": 10875,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 3790, "rate": 0.0246},
                {"min": 3790, "max": 9214, "rate": 0.0351},
                {"min": 9214, "max": float("inf"), "rate": 0.0684},
            ],
        },
        "NV": {
            "name": "Nevada",
            "standard_deduction": {
                "single": 0,
                "married_joint": 0,
                "married_separate": 0,
                "head_of_household": 0,
            },
            "type": "none",
            "brackets": [],
        },
        "NH": {
            "name": "New Hampshire",
            "standard_deduction": {
                "single": 0,
                "married_joint": 0,
                "married_separate": 0,
                "head_of_household": 0,
            },
            "type": "flat",
            "brackets": [{"min": 0, "max": float("inf"), "rate": 0.01}],  # Interest/dividends only
        },
        "NJ": {
            "name": "New Jersey",
            "standard_deduction": {
                "single": 11800,
                "married_joint": 23600,
                "married_separate": 11800,
                "head_of_household": 17700,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 21840, "rate": 0.014},
                {"min": 21840, "max": 54200, "rate": 0.0175},
                {"min": 54200, "max": 85000, "rate": 0.0235},
                {"min": 85000, "max": 200000, "rate": 0.0357},
                {"min": 200000, "max": 500000, "rate": 0.0437},
                {"min": 500000, "max": float("inf"), "rate": 0.0637},
            ],
        },
        "NM": {
            "name": "New Mexico",
            "standard_deduction": {
                "single": 3750,
                "married_joint": 7500,
                "married_separate": 3750,
                "head_of_household": 5625,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 1000, "rate": 0.017},
                {"min": 1000, "max": 7500, "rate": 0.032},
                {"min": 7500, "max": 15000, "rate": 0.047},
                {"min": 15000, "max": 25000, "rate": 0.062},
                {"min": 25000, "max": float("inf"), "rate": 0.077},
            ],
        },
        "NY": {
            "name": "New York",
            "standard_deduction": {
                "single": 8850,
                "married_joint": 17700,
                "married_separate": 8850,
                "head_of_household": 13300,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 12000, "rate": 0.04},
                {"min": 12000, "max": 23600, "rate": 0.0475},
                {"min": 23600, "max": 80650, "rate": 0.0585},
                {"min": 80650, "max": 322050, "rate": 0.0685},
                {"min": 322050, "max": 1000000, "rate": 0.0765},
                {"min": 1000000, "max": float("inf"), "rate": 0.0885},
            ],
        },
        "NC": {
            "name": "North Carolina",
            "standard_deduction": {
                "single": 12750,
                "married_joint": 25500,
                "married_separate": 12750,
                "head_of_household": 19125,
            },
            "type": "flat",
            "brackets": [{"min": 0, "max": float("inf"), "rate": 0.0475}],
        },
        "ND": {
            "name": "North Dakota",
            "standard_deduction": {
                "single": 15000,
                "married_joint": 30000,
                "married_separate": 15000,
                "head_of_household": 22500,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 41675, "rate": 0.01},
                {"min": 41675, "max": 100750, "rate": 0.02},
                {"min": 100750, "max": 239890, "rate": 0.022},
                {"min": 239890, "max": float("inf"), "rate": 0.029},
            ],
        },
        "OH": {
            "name": "Ohio",
            "standard_deduction": {
                "single": 2650,
                "married_joint": 5300,
                "married_separate": 2650,
                "head_of_household": 3975,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 22750, "rate": 0.015},
                {"min": 22750, "max": 56875, "rate": 0.03},
                {"min": 56875, "max": 91105, "rate": 0.032},
                {"min": 91105, "max": float("inf"), "rate": 0.0515},
            ],
        },
        "OK": {
            "name": "Oklahoma",
            "standard_deduction": {
                "single": 3150,
                "married_joint": 6300,
                "married_separate": 3150,
                "head_of_household": 4725,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 1000, "rate": 0.007},
                {"min": 1000, "max": 2500, "rate": 0.02},
                {"min": 2500, "max": 3750, "rate": 0.03},
                {"min": 3750, "max": 5000, "rate": 0.04},
                {"min": 5000, "max": 7200, "rate": 0.05},
                {"min": 7200, "max": float("inf"), "rate": 0.055},
            ],
        },
        "OR": {
            "name": "Oregon",
            "standard_deduction": {
                "single": 5220,
                "married_joint": 10440,
                "married_separate": 5220,
                "head_of_household": 7830,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 5200, "rate": 0.0475},
                {"min": 5200, "max": 13100, "rate": 0.0675},
                {"min": 13100, "max": 20200, "rate": 0.0875},
                {"min": 20200, "max": float("inf"), "rate": 0.099},
            ],
        },
        "PA": {
            "name": "Pennsylvania",
            "standard_deduction": {
                "single": 0,
                "married_joint": 0,
                "married_separate": 0,
                "head_of_household": 0,
            },
            "type": "flat",
            "brackets": [{"min": 0, "max": float("inf"), "rate": 0.0307}],
        },
        "RI": {
            "name": "Rhode Island",
            "standard_deduction": {
                "single": 8350,
                "married_joint": 16700,
                "married_separate": 8350,
                "head_of_household": 12525,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 73000, "rate": 0.0375},
                {"min": 73000, "max": float("inf"), "rate": 0.0475},
            ],
        },
        "SC": {
            "name": "South Carolina",
            "standard_deduction": {
                "single": 3490,
                "married_joint": 6980,
                "married_separate": 3490,
                "head_of_household": 5235,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 3240, "rate": 0.02},
                {"min": 3240, "max": 8120, "rate": 0.03},
                {"min": 8120, "max": 12000, "rate": 0.04},
                {"min": 12000, "max": float("inf"), "rate": 0.07},
            ],
        },
        "SD": {
            "name": "South Dakota",
            "standard_deduction": {
                "single": 0,
                "married_joint": 0,
                "married_separate": 0,
                "head_of_household": 0,
            },
            "type": "none",
            "brackets": [],
        },
        "TN": {
            "name": "Tennessee",
            "standard_deduction": {
                "single": 0,
                "married_joint": 0,
                "married_separate": 0,
                "head_of_household": 0,
            },
            "type": "flat",
            "brackets": [{"min": 0, "max": float("inf"), "rate": 0.02}],  # Interest/dividends only
        },
        "TX": {
            "name": "Texas",
            "standard_deduction": {
                "single": 0,
                "married_joint": 0,
                "married_separate": 0,
                "head_of_household": 0,
            },
            "type": "none",
            "brackets": [],
        },
        "UT": {
            "name": "Utah",
            "standard_deduction": {
                "single": 15000,
                "married_joint": 30000,
                "married_separate": 15000,
                "head_of_household": 22500,
            },
            "type": "flat",
            "brackets": [{"min": 0, "max": float("inf"), "rate": 0.0485}],
        },
        "VT": {
            "name": "Vermont",
            "standard_deduction": {
                "single": 15000,
                "married_joint": 30000,
                "married_separate": 15000,
                "head_of_household": 22500,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 52000, "rate": 0.035},
                {"min": 52000, "max": 135000, "rate": 0.068},
                {"min": 135000, "max": float("inf"), "rate": 0.076},
            ],
        },
        "VA": {
            "name": "Virginia",
            "standard_deduction": {
                "single": 4500,
                "married_joint": 9000,
                "married_separate": 4500,
                "head_of_household": 6750,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 3200, "rate": 0.02},
                {"min": 3200, "max": 8000, "rate": 0.03},
                {"min": 8000, "max": 17000, "rate": 0.05},
                {"min": 17000, "max": float("inf"), "rate": 0.0575},
            ],
        },
        "WA": {
            "name": "Washington",
            "standard_deduction": {
                "single": 0,
                "married_joint": 0,
                "married_separate": 0,
                "head_of_household": 0,
            },
            "type": "none",
            "brackets": [],
        },
        "WV": {
            "name": "West Virginia",
            "standard_deduction": {
                "single": 2680,
                "married_joint": 5360,
                "married_separate": 2680,
                "head_of_household": 4020,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 10000, "rate": 0.03},
                {"min": 10000, "max": 25000, "rate": 0.04},
                {"min": 25000, "max": 40000, "rate": 0.045},
                {"min": 40000, "max": 60000, "rate": 0.06},
                {"min": 60000, "max": float("inf"), "rate": 0.065},
            ],
        },
        "WI": {
            "name": "Wisconsin",
            "standard_deduction": {
                "single": 10800,
                "married_joint": 21600,
                "married_separate": 10800,
                "head_of_household": 16200,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 13170, "rate": 0.035},
                {"min": 13170, "max": 48970, "rate": 0.045},
                {"min": 48970, "max": 116400, "rate": 0.053},
                {"min": 116400, "max": float("inf"), "rate": 0.077},
            ],
        },
        "WY": {
            "name": "Wyoming",
            "standard_deduction": {
                "single": 0,
                "married_joint": 0,
                "married_separate": 0,
                "head_of_household": 0,
            },
            "type": "none",
            "brackets": [],
        },
        "DC": {
            "name": "District of Columbia",
            "standard_deduction": {
                "single": 15000,
                "married_joint": 30000,
                "married_separate": 15000,
                "head_of_household": 22500,
            },
            "type": "progressive",
            "brackets": [
                {"min": 0, "max": 11750, "rate": 0.04},
                {"min": 11750, "max": 48080, "rate": 0.06},
                {"min": 48080, "max": 240920, "rate": 0.087},
                {"min": 240920, "max": float("inf"), "rate": 0.0975},
            ],
        },
    }
    return state_data


def calculate_state_tax(annual_income: float, state: str, filing_status: str = "single") -> float:
    """
    Calculate state income tax using progressive brackets.

    Args:
        annual_income: Annual pre-tax income
        state: State abbreviation (e.g., 'CO', 'CA', 'TX')
        filing_status: 'single', 'married_joint', 'married_separate', or 'head_of_household'

    Returns:
        State tax amount

    Source: 2025 Tax Foundation, State Tax Agency Websites, IRS Publication 17
    """
    state_data = get_state_tax_brackets()

    if state.upper() not in state_data:
        # Unknown state - default to 4% estimate
        return annual_income * 0.04

    state_info = state_data[state.upper()]

    # No income tax states
    if state_info["type"] == "none":
        return 0.0

    # Get standard deduction for filing status
    standard_deduction = state_info["standard_deduction"].get(filing_status, 0)

    # Calculate taxable income
    taxable_income = max(0, annual_income - standard_deduction)

    # Apply brackets
    tax = 0.0
    for bracket in state_info["brackets"]:
        if taxable_income <= bracket["min"]:
            break

        income_in_bracket = min(taxable_income, bracket["max"]) - bracket["min"]
        tax += income_in_bracket * bracket["rate"]

    return tax


def get_all_states_list() -> list:
    """Return sorted list of all state codes and names for dropdown."""
    state_data = get_state_tax_brackets()
    return sorted([(code, data["name"]) for code, data in state_data.items()])
