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

parser.add_argument(
    "-y",
    "--year",
    action="store",
    help="fiscal year",
    metavar="<year>",
    type=int,
    default=2023,
)

residence_group = parser.add_argument_group("residence options", "what kind of a residence status you have")
residence_exclusive_group = residence_group.add_mutually_exclusive_group(required=False)

residence_exclusive_group.add_argument(
    "-nr",
    "--non-resident",
    action="store_const",
    const="nr",
    help="specify if you are not a resident",
    metavar="<region>",
)
residence_exclusive_group.add_argument(
    "-nhr",
    "--non-habitual",
    action="store",
    nargs="?",
    const="Mainland",
    default=None,
    help="specify if you are a non-habitual resident and (optionaly) provide a region",
    metavar="<region>",
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
    help="specify the month and year when activity was opened",
    metavar="<activity opened on mm/yy>",
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

status_group = parser.add_argument_group("civil status", "is it a single or a joint delacration")

status_group.add_argument(
    "-j",
    "--joint",
    action="store_true",
    help="specify if you opt for joint declaration",
)

status_group.add_argument(
    "-k",
    "--kids",
    action="store",
    help="specify children's age in the end of the year",
    metavar="<children age>",
    type=str,
)

args = parser.parse_args()

if __name__ == "__main__":

    kwargs = {
        "year": args.year,
        "income": args.income,
        "opened_at": args.independent_worker,
        "expenses": args.activity_expenses,
        "status": 'joint' if args.joint else 'single',
        "kids": args.kids,
    }

    if args.non_resident:
        kwargs["residence"] = "nr"
    elif args.non_habitual:
        kwargs["residence"] = "nhr"
        kwargs["region"] = args.non_habitual
    elif args.residence:
        kwargs["region"] = args.residence

    income = Income(**kwargs)

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
