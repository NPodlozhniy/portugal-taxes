from enum import Enum
import numpy as np

class Thresholds(Enum):
    Mainland = [7479, 11284, 15992, 20700, 26355, 38632, 50483, 78834]
    Madeira = [7116, 10736, 20322, 25075, 36967, 80882]
    Azores = [7116, 10736, 20322, 25075, 36967, 80882]

class Rates(Enum):
    Mainland = [0.145, 0.21, 0.265, 0.285, 0.35, 0.37, 0.435, 0.45, 0.48]
    Madeira = [0.116, 0.207, 0.265, 0.3375, 0.3587, 0.4495, 0.48]
    Azores = [0.105, 0.1725, 0.2138, 0.28, 0.296, 0.36, 0.38]

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
                self.income,
                Thresholds[self.region].value,
                Rates[self.region].value
            )

    @property
    def solidarity_tax(self) -> float:
        thresholds = [75000, 80000, 200000, 300000]
        rates = [0, 0.40, 0.025, 0.10, 0.05]
        return self.progressive_taxation(self.income, thresholds, rates)

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
