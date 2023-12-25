from enum import Enum
import numpy as np

class Thresholds(Enum):
    Mainland = [7479, 11284, 15992, 20700, 26355, 38632, 50483, 78834]
    Madeira = [7479, 11284, 15992, 20700, 26355, 38632, 50483, 78834]
    Azores = [7479, 11284, 15992, 20700, 26355, 38632, 50483, 78834]

class Rates(Enum):
    Mainland = [0.145, 0.21, 0.265, 0.285, 0.35, 0.37, 0.435, 0.45, 0.48]
    Madeira = [0.1015, 0.147, 0.1855, 0.1995, 0.2975, 0.3367, 0.422, 0.4365, 0.4752]
    Azores = [0.1015, 0.147, 0.1855, 0.1995, 0.245, 0.259, 0.3045, 0.315, 0.336]

class Income():
    """
    Portugal Taxation Calculator
    
    Parameters
    ----------
    income : float, default=None
        Annual gross income
    residence : {'r', 'nr', 'nhr'}, default='r'
        Type of residence
        - `'r'`: Resident
        - `'nr'`: Non-resident
        - `'nhr'`: Non-Habitual Resident
    region : {'Mainland', 'Madeira', 'Azores'}, default='Mainland'
        The region of residence
    """

    def __init__(self, income=None, residence='r', region='Mainland'):
        if income == None:
            raise ValueError(
                "Specify the Annual gross income"
            )
        self.income = income
        if residence not in {'r', 'nr', 'nhr'}:
            raise ValueError(
                "Incorrect type of residence, "
                "should be one of the following: r, nr, nhr}"
            )
        self.residence = residence
        if region not in {'Mainland', 'Madeira', 'Azores'}:
            raise ValueError(
                "Incorrect region of residence, "
                "should be one of the following: Mainland, Madeira, Azores"
            )
        self.region = region
    
    @property
    def income_tax(self) -> float:
        if self.residence == "nr":
           return self.income * 0.25
        elif self.residence == "nhr":
            return self.income * 0.20
        else:
            return self.progressive_taxation(
                max(0, self.income - max(4104, self.social_security_tax)),
                Thresholds[self.region].value,
                Rates[self.region].value
            )

    @property
    def solidarity_tax(self) -> float:
        thresholds = [75000, 80000, 200000, 300000]
        rates = [0, 0.40, 0.025, 0.10, 0.05]
        return self.progressive_taxation(self.income, thresholds, rates) if self.residence == "r" else 0

    @property
    def social_security_tax(self) -> float:
        return round(self.income * 0.11, 2)

    @staticmethod
    def progressive_taxation(income: float, thresholds: list, rates: list) -> float:
        """
        rates[i] correspond to taxes applied to income
        between thresholds[i - 1] and thresholds[i]
        """
        thresholds = np.array(thresholds)
        rates = np.array(rates)
        difference = thresholds - np.hstack((0, thresholds[:-1]))  
        indexes = thresholds <= income
        return round(
            sum(
                [threshold * rate for threshold, rate
                in zip(difference[indexes], rates[:-1][indexes])]
            ) + (
                rates[sum(indexes)] * (
                    income - (
                        thresholds[sum(indexes) - 1]
                        if sum(indexes) != 0 else 0
                    )
                )
            )
        , 2)

    def __repr__(self) -> str:
        type = {
            'r': 'Resident',
            'nr': 'Non-resident',
            'nhr': 'Non-Habitual Resident'
            }
        return f"<Portugal taxes for a {type[self.residence]} living in {self.region}>"
