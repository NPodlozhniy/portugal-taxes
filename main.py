import argparse

from model import Income

parser = argparse.ArgumentParser(
    description="Portugal net income calculator for 2023"
    )

group = parser.add_mutually_exclusive_group(required=False)

parser.add_argument(
    "income",
    action="store",
    help="gross annual income",
    metavar="<income>",
    type=float,
)
group.add_argument(
    "-nr",
    "--non-resident",
    action="store_const",
    const="nr",
    help="specify if you are a non-resident",
)
group.add_argument(
    "-nhr",
    "--non-habitual",
    action="store_const",
    const="nhr",
    help="specify if you are a non-habitual resident",
)
group.add_argument(
    "-r",
    "--residence",
    action="store",
    help="specify the region of residence if any",
    metavar="<region>",
)
args = parser.parse_args()

if __name__ == "__main__":

    residence = args.non_resident or args.non_habitual
    region = args.residence

    if residence:
        income = Income(args.income, residence=residence)
    elif region:
        income = Income(args.income, region=region)
    else:
        income = Income(args.income)

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
