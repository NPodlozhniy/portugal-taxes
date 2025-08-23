from datetime import datetime

import numpy as np

from config import get_tax_data


class Income():
    """
    Portugal Taxation Calculator
    
    Parameters
    ----------
    year : int, default=2023
        Fiscal year the taxes are calculated for
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
        year: int = 2023,
        income: float = None,
        residence: str = 'r',
        region: str = 'Mainland',
        opened_at: str = None,
        expenses: float = 0,
        # add joint declaration & children
        status: str = 'single',
        kids: str = None,
    ) -> None:
        if year < 2023 or year > 2025:
            raise ValueError(
                "Only years from 2023 to 2025 are currently supported"
            )
        else:
            self.year = year
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
            self.activity_expenses = 0 if not expenses else float(expenses)
            try:
                self.opened_at = datetime.strptime(opened_at, '%m/%y')
            except ValueError:
                raise ValueError(
                "Incorrect activity opened month or expenses format, "
                "should be a date in `mm/yy` and a float value respectively"
            )
            if self.opened_at.year > self.year:
                raise ValueError(
                    "The taxes can't be estimated for the year prior to when the activity was opened. "
                    "Consider the following years or adjust your income category"
                )

        if status not in {'single', 'joint'}:
            raise ValueError(
                "Incorrect submit status, "
                "should be either `single` or `joint`"
            )
        else:
            self.status = status
        if kids:
            try:
                self.ages = [int(age.strip()) for age in kids.split(',')]
            except ValueError:
                raise ValueError(
                "Incorrect format of children ages provided, "
                "should be integer numbers for the end of the year separated by a comma without spaces. "
                "Example: '3,10,1'"
            )

    @property
    def specific_deduction(self) -> float:
        tax_data = get_tax_data(self.year, self.region)
        if self.year == 2023:
            return 4104 # it was a fixed amount back then
        else:
            return 8.54 * tax_data["ias"]

    @property
    def taxable_base(self) -> float:
        """
        Consider only TI providing services where standard taxable base - 75%
        For ENI supplies of goods the coefficient is different.
        """
        if self.category == "B":
            # first two years of atividade with discount
            extra_discount = (
                0.5 if self.opened_at.year == self.year else 0.25 if self.opened_at.year == self.year - 1 else 0
            )
            # 15% are added as the discount of 75% reflects the costs for business
            # social security and other TI related costs are deducted, so it may be reduced to zero
            not_incurred_expenses = max(
                0, self.income * 0.15 - max(self.specific_deduction, self.social_security_tax) - self.activity_expenses
            )
            return self.income * 0.75 * (1 - extra_discount) + not_incurred_expenses
        else:
            return max(0, self.income - max(self.specific_deduction, self.social_security_tax))

    @property
    def family_quotient(self) -> float:
        quote = 1
        if self.status == 'single':
            return quote
        else:
            # joint declaration
            quote += 1
        # and extra for kids
        if hasattr(self, "ages"):
            # 0.5 for the first
            quote += 0.25
            for age in self.ages:
                # 0.25 for others
                quote += 0.25
        return quote

    @property
    def family_deduction(self) -> float:
        if not hasattr(self, "ages"):
            return 0
        # every dependent adds 600 euros
        expenses = 600 * len(self.ages)
        # every children under 3 get extra 126 euros
        for age in self.ages:
            if age <= 3:
                expenses += 126
        # the second and subsequent children under 6 get extra 300 euros
        for age in sorted(self.ages)[1:]:
            if age <= 6:
                expenses += 300
        # if a family submit separate declarations
        # choldren deducations are divided equally
        if self.status == 'single':
            expenses /= 2
        return expenses

    @property
    def income_tax(self) -> float:
        if self.residence == "nr":
           # social security payments discount is for residents only
           return self.income * 0.25
        elif self.residence == "nhr":
            return self.taxable_base * 0.20 * (1 - (0.3 if self.region == "Azores" else 0))
        else:
            tax_data = get_tax_data(self.year, self.region)
            return self.family_quotient * self.progressive_taxation(
                self.taxable_base / self.family_quotient,
                tax_data["brackets"],
                tax_data["rates"],
            ) - self.family_deduction

    @property
    def solidarity_tax(self) -> float:
        thresholds = [75000, 80000, 200000, 300000]
        rates = [0, 0.40, 0.025, 0.10, 0.05]
        return self.progressive_taxation(self.income, thresholds, rates) if self.residence == "r" else 0

    @property
    def social_security_tax(self) -> float:
        if self.category == "B":
            tax_year_end_at = datetime.strptime(f"01/{1 + self.year % 100}", '%m/%y')
            months_since_opened = tax_year_end_at.month - self.opened_at.month + 12 * (tax_year_end_at.year - self.opened_at.year)
            # first 12 months after opening the social security is not paid
            # then until the beginning of the new quarter it's fixed - 20€
            # as there is no income yet declared in a quarterly decalration
            months_to_first_declaration = 3 - (self.opened_at.month - 1) % 3
            invoiced_months = min(12, max(0, months_since_opened - 12 - months_to_first_declaration))
            return round(self.income * (invoiced_months / 12) * 0.1125 + months_to_first_declaration * 20, 2)
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
            'nr': 'Non-Resident',
            'nhr': 'Non-Habitual Resident'
            }
        return " ".join([
            f"<Portuguese IRS for a {type[self.residence]}",
            f"living {'anywhere' if self.residence == 'nr' else 'on ' + self.region}",
            f"from {'regular employment' if self.category == 'A' else 'independent provision of services'}",
            f"in {self.year}>"
        ])
