from enum import Enum
import numpy as np

from datetime import datetime

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

    def __init__(
        self,
        income: float = None,
        residence: str = 'r',
        region: str = 'Mainland',
        opened_at: str = None,
        expenses: float = None,
    ) -> None:
        if income == None:
            raise ValueError(
                "Specify the Annual gross income"
            )
        else:
            self.income = income
        if residence not in {'r', 'nr', 'nhr'}:
            raise ValueError(
                "Incorrect type of residence, "
                "should be one of the following: r, nr, nhr}"
            )
        else:
            self.residence = residence
        if region not in {'Mainland', 'Madeira', 'Azores'}:
            raise ValueError(
                "Incorrect region of residence, "
                "should be one of the following: Mainland, Madeira, Azores"
            )
        else:
            self.region = region

        if not opened_at:
            self.category = 'A' # regular employee
        else:
            self.category = 'B' # independent worker (TI/ENI)
            try:
                self.opened_at = datetime.strptime(opened_at, '%m/%y')
                self.activity_expenses = 0 if not expenses else float(expenses)
            except ValueError:
                raise ValueError(
                "Incorrect activity opened month or expenses format, "
                "should be a date in `mm/yy` and a float value respectively"
            )

    @property
    def taxable_base(self) -> float:
        """
        Consider only TI providing services where standard taxable base - 75%
        For ENI supplies of goods the coeeficient is different.
        """
        if self.category == "B":
            # first two years of atividade with discount
            extra_discount = (
                0.5 if self.opened_at.year == 2023 else 0.25 if self.opened_at.year == 2022 else 0
            )
            # 15% are added as the discount of 75% reflects the costs for business
            # social security and other TI related costs are deducted, so it may be reduced to zero
            not_incurred_expenses = max(0, self.income * 0.15 - max(4104, self.social_security_tax) - self.activity_expenses)
            return self.income * 0.75 * (1 - extra_discount) + not_incurred_expenses
        else:
            return max(0, self.income - max(4104, self.social_security_tax))

    @property
    def income_tax(self) -> float:
        if self.residence == "nr":
           # social security payments discount is for residents only
           return self.income * 0.25
        elif self.residence == "nhr":
            return self.taxable_base * 0.20 * (1 - (0.3 if self.region == "Azores" else 0))
        else:
            return self.progressive_taxation(
                self.taxable_base,
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
        if self.category == "B":
            tax_year_end_at = datetime.strptime('01/24', '%m/%y')
            months_sice_opened = tax_year_end_at.month - self.opened_at.month + 12 * (tax_year_end_at.year - self.opened_at.year)
            # first 12 months after opening the social security is not paid
            invoiced_months = min(12, max(0, months_sice_opened - 12))
            return round(self.income * (invoiced_months / 12) * 0.1125, 2)
        else:
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
        return " ".join([
            f"<Portugal taxes for a {type[self.residence]}",
            f"living {'anywhere' if self.residence == 'nr' else 'on ' + self.region}",
            f"from {'regular employment' if self.category == 'A' else 'independent provision of services'}>"
        ])
