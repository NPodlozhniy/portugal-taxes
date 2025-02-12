import argparse

from model import Income

parser = argparse.ArgumentParser(
    description="Portugal net income calculator for 2023"
    )

parser.add_argument(
    "income",
    action="store",
    help="gross annual income",
    metavar="<income>",
    type=float,
)

residence_group = parser.add_argument_group("residence options", "what kind of a residence status you have")
residence_exclusive_group = residence_group.add_mutually_exclusive_group(required=False)

residence_exclusive_group.add_argument(
    "-nr",
    "--non-resident",
    action="store_const",
    const="nr",
    help="specify if you are not a resident",
)
residence_exclusive_group.add_argument(
    "-nhr",
    "--non-habitual",
    action="store_const",
    const="nhr",
    help="specify if you are a non-habitual resident",
)
residence_exclusive_group.add_argument(
    "-r",
    "--residence",
    action="store",
    help="specify the region of residence",
    metavar="<region>",
)

category_group = parser.add_argument_group("income categories", "what is the income category: A or B")
category_exclusive_group = category_group.add_mutually_exclusive_group(required=True)

category_exclusive_group.add_argument(
    "-a",
    "--regular-employee",
    action="store_true",
    help="specify if you have income category A",
)

category_exclusive_group.add_argument(
    "-b",
    "--independent-worker",
    action="store",
    help="specify the month and date when activity was opened",
    metavar="<activity opened at>",
)

category_group.add_argument(
    "-e",
    "--activity-expenses",
    action="store",
    help="specify the amount of business related expenses",
    metavar="<activity expenses>",
    type=float,
    default=0,
)

args = parser.parse_args()

if __name__ == "__main__":

    residence = args.non_resident or args.non_habitual
    region = args.residence
    opened_at = args.independent_worker

    if residence:
        income = Income(args.income, residence=residence, opened_at=opened_at, expenses=args.activity_expenses)
    elif region:
        income = Income(args.income, region=region, opened_at=opened_at, expenses=args.activity_expenses)
    else:
        income = Income(args.income, opened_at=opened_at, expenses=args.activity_expenses)

    print(f"\n{income}\n")

    i = income.income
    it = income.income_tax
    sst = income.social_security_tax
    st = income.solidarity_tax

    print(f"Wages:{i:30,.2f}€")
    print(f"\nPersonal Income Tax:{it:15,.2f}€")
    print(f"Social Security:{sst:19,.2f}€")
    if st > 0:
        print(f"Solidarity Tax:{st:20,.2f}€")
    print(f"\nTotal Tax:{it + sst + st:25,.2f}€")
    print(f"Effective Rate:{(it + sst + st)/i:21.2%}")
    print(f"\nMonthly Net Salary:{(i - (it + sst + st))/12:16,.2f}€")
