"""
File containing variables and setting to explain the period between 2000 and 2024 in the battle of the water futures data.
"""

DEF_POLICY_BUDG_ALL = {
    "policy": "by_population"
}

DEF_POLICY_NRW_MITIGATION = {
    'budget': 0,
    'policy': 'by_nrw_population'
}

DEF_POLICY_PRICING = {
    'policy': 'by_inflation'
}

DEF_POLICY_BOND = {
    'value': 1.5
}

def get_historical_masterplan() -> dict:
    mp = {
        'years': [
            {
                'year': 2000,
                'national_policies': {
                    'budget_allocation': DEF_POLICY_BUDG_ALL
                },
                'water_utilities': [
                    {
                        'water_utility': 'WU01',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 1600000,
                                'policy': 'by_population'
                            },
                            'pricing_adjustment': DEF_POLICY_PRICING,
                            'bond_ratio': DEF_POLICY_BOND
                        }
                    },
                    {
                        'water_utility': 'WU02',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 1800000,
                                'policy': 'by_population'
                            },
                            'pricing_adjustment': DEF_POLICY_PRICING,
                            'bond_ratio': DEF_POLICY_BOND
                        }
                    },
                    {
                        'water_utility': 'WU03',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 1400000,
                                'policy': 'by_population'
                            },
                            'pricing_adjustment': DEF_POLICY_PRICING,
                            'bond_ratio': DEF_POLICY_BOND
                        }
                    },
                    {
                        'water_utility': 'WU04',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 3000000,
                                'policy': 'by_population'
                            },
                            'pricing_adjustment': DEF_POLICY_PRICING,
                            'bond_ratio': DEF_POLICY_BOND
                        }
                    },
                    {
                        'water_utility': 'WU05',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 6200000,
                                'policy': 'by_population'
                            },
                            'pricing_adjustment': DEF_POLICY_PRICING,
                            'bond_ratio': DEF_POLICY_BOND
                        }
                    },
                    {
                        'water_utility': 'WU06',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 3500000,
                                'policy': 'by_population'
                            },
                            'pricing_adjustment': DEF_POLICY_PRICING,
                            'bond_ratio': DEF_POLICY_BOND
                        }
                    },
                    {
                        'water_utility': 'WU07',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 7000000,
                                'policy': 'by_population'
                            },
                            'pricing_adjustment': DEF_POLICY_PRICING,
                            'bond_ratio': DEF_POLICY_BOND
                        }
                    },
                    {
                        'water_utility': 'WU08',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 10000000,
                                'policy': 'by_population'
                            },
                            'pricing_adjustment': DEF_POLICY_PRICING,
                            'bond_ratio': DEF_POLICY_BOND
                        }
                    },
                    {
                        'water_utility': 'WU09',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 6300000,
                                'policy': 'by_population'
                            },
                            'pricing_adjustment': DEF_POLICY_PRICING,
                            'bond_ratio': DEF_POLICY_BOND
                        }
                    },
                    {
                        'water_utility': 'WU10',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 3000000,
                                'policy': 'by_population'
                            },
                            'pricing_adjustment': DEF_POLICY_PRICING,
                            'bond_ratio': DEF_POLICY_BOND
                        }
                    }
                ]
            },
            {
                'year': 2005,
                'water_utilities': [
                    {
                        'water_utility': 'WU01',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 2000000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU02',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 2500000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU03',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 1800000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU04',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 4000000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU05',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 7500000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU06',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 3800000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU07',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 8000000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU08',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 12000000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU09',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 6900000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU10',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 3400000,
                                'policy': 'by_population'
                            }
                        }
                    }
                ]
            },
            {
                'year': 2010,
                'water_utilities': [
                    {
                        'water_utility': 'WU01',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 2200000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU02',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 2700000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU03',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 2000000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU04',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 4500000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU05',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 8400000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU06',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 4200000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU07',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 9000000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU08',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 13000000,
                                'policy': 'by_nrw_class'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU09',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 7500000,
                                'policy': 'by_nrw_class'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU10',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 3500000,
                                'policy': 'by_nrw_class'
                            }
                        }
                    }
                ]
            },
            {
                'year': 2020,
                'water_utilities': [
                    {
                        'water_utility': 'WU01',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 3000000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU02',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 3500000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU03',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 2500000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU04',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 5000000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU05',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 10000000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU06',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 5000000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU07',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 11000000,
                                'policy': 'by_population'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU08',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 20000000,
                                'policy': 'by_nrw_class'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU09',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 9000000,
                                'policy': 'by_nrw_class'
                            }
                        }
                    },
                    {
                        'water_utility': 'WU10',
                        'policies': {
                            'nrw_mitigation': {
                                'budget': 4000000,
                                'policy': 'by_nrw_class'
                            }
                        }
                    }
                ]
            }
        ]
    }

    return mp