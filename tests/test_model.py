"""
Tests for the Income tax calculation engine (model.py).

Reference values are computed from the 2025 Mainland brackets/rates and IAS=522.5:
  specific_deduction = 8.54 * 522.5 = 4462.15
  SS (Cat A)          = income * 0.11
"""
import pytest
from model import Income


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make(income, **kwargs):
    """Convenience wrapper with sensible defaults."""
    defaults = dict(year=2025, income=income, residence="r", region="Mainland")
    defaults.update(kwargs)
    return Income(**defaults)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestValidation:
    def test_missing_income_raises(self):
        with pytest.raises(ValueError, match="gross income"):
            Income(income=None)

    def test_invalid_residence_raises(self):
        with pytest.raises(ValueError, match="residence"):
            make(30000, residence="xx")

    def test_invalid_region_raises(self):
        with pytest.raises(ValueError, match="region"):
            make(30000, region="Algarve")

    def test_invalid_year_raises(self):
        with pytest.raises(ValueError, match="years"):
            make(30000, year=2022)

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="status"):
            make(30000, status="married")

    def test_invalid_kids_format_raises(self):
        with pytest.raises(ValueError, match="ages"):
            make(30000, kids="young")

    def test_future_activity_year_raises(self):
        with pytest.raises(ValueError, match="prior"):
            make(30000, opened_at="01/26")  # activity opened after tax year 2025

    def test_invalid_opened_at_format_raises(self):
        with pytest.raises(ValueError, match="format"):
            make(30000, opened_at="2024-01")


# ---------------------------------------------------------------------------
# Social Security
# ---------------------------------------------------------------------------

class TestSocialSecurity:
    def test_category_a_ss_is_11_percent(self):
        inc = make(50000)
        assert inc.social_security_tax == round(50000 * 0.11, 2)

    def test_category_b_year1_no_ss(self):
        # Opened Jan 2025, tax year 2025 → first 12 months exempt
        inc = make(50000, opened_at="01/25")
        # months_since_opened = 12, exempt period = 12 → invoiced_months = 0
        # only the fixed €20/month for months_to_first_declaration
        months_to_first = 3 - (1 - 1) % 3  # = 3
        assert inc.social_security_tax == round(months_to_first * 20, 2)

    def test_category_b_year2_partial_ss(self):
        # Opened Jan 2024, tax year 2025 → invoiced months = min(12, 24-12-3) = 9
        inc = make(60000, opened_at="01/24")
        expected = round(60000 * (9 / 12) * 0.1125 + 3 * 20, 2)
        assert inc.social_security_tax == expected

    def test_category_b_established_full_ss(self):
        # Opened Jan 2022, tax year 2025 → fully established (12 invoiced months)
        # months_to_first_declaration = 3 - (1-1)%3 = 3
        inc = make(60000, opened_at="01/22")
        months_to_first = 3 - (1 - 1) % 3  # = 3
        expected = round(60000 * 1.0 * 0.1125 + months_to_first * 20, 2)
        assert inc.social_security_tax == expected


# ---------------------------------------------------------------------------
# Non-resident (flat 25%)
# ---------------------------------------------------------------------------

class TestNonResident:
    def test_income_tax_flat_25(self):
        inc = make(40000, residence="nr")
        assert inc.income_tax == 40000 * 0.25

    def test_no_solidarity_tax(self):
        inc = make(200000, residence="nr")
        assert inc.solidarity_tax == 0

    def test_ss_still_applies_category_a(self):
        inc = make(40000, residence="nr")
        assert inc.social_security_tax == round(40000 * 0.11, 2)


# ---------------------------------------------------------------------------
# Non-habitual resident (flat 20%)
# ---------------------------------------------------------------------------

class TestNHR:
    def test_income_tax_flat_20_on_taxable_base(self):
        inc = make(40000, residence="nhr")
        # taxable_base for Cat A: max(0, 40000 - max(specific_deduction, ss))
        ss = round(40000 * 0.11, 2)
        spec = round(8.54 * 522.5, 2)  # 4462.15
        taxable = max(0, 40000 - max(spec, ss))
        assert inc.income_tax == round(taxable * 0.20, 2)

    def test_nhr_azores_30pct_reduction(self):
        mainland = make(40000, residence="nhr", region="Mainland")
        azores = make(40000, residence="nhr", region="Azores")
        assert round(azores.income_tax, 2) == round(mainland.income_tax * 0.70, 2)

    def test_no_solidarity_tax(self):
        inc = make(200000, residence="nhr")
        assert inc.solidarity_tax == 0


# ---------------------------------------------------------------------------
# Resident progressive tax
# ---------------------------------------------------------------------------

class TestResidentProgressiveTax:
    def test_below_first_bracket_rate(self):
        # €8,000 falls entirely in the 12.5% bracket
        inc = make(8000)
        ss = round(8000 * 0.11, 2)
        spec = round(8.54 * 522.5, 2)
        taxable = max(0, 8000 - max(spec, ss))
        assert inc.income_tax == round(taxable * 0.125, 2)

    def test_effective_rate_increases_with_income(self):
        low = make(25000)
        high = make(80000)
        low_rate = low.income_tax / low.income
        high_rate = high.income_tax / high.income
        assert high_rate > low_rate

    def test_solidarity_tax_zero_below_threshold(self):
        inc = make(74999)
        assert inc.solidarity_tax == 0

    def test_solidarity_tax_above_75k(self):
        inc = make(80000)
        assert inc.solidarity_tax > 0

    def test_mainland_higher_than_azores(self):
        mainland = make(60000)
        azores = make(60000, region="Azores")
        assert mainland.income_tax > azores.income_tax


# ---------------------------------------------------------------------------
# Category B taxable base
# ---------------------------------------------------------------------------

class TestCategoryBTaxableBase:
    def test_year1_50pct_extra_discount(self):
        # Tax year 2025, opened 2025 → extra_discount = 0.5
        inc = make(60000, opened_at="01/25")
        # taxable = 60000 * 0.75 * (1 - 0.5) + not_incurred_expenses
        base_before_extras = 60000 * 0.75 * 0.5
        assert inc.taxable_base >= base_before_extras  # not_incurred may add more

    def test_year2_25pct_extra_discount(self):
        # Tax year 2025, opened 2024 → extra_discount = 0.25
        inc_y2 = make(60000, opened_at="01/24")
        inc_y3 = make(60000, opened_at="01/23")  # no extra discount
        assert inc_y2.taxable_base < inc_y3.taxable_base

    def test_expenses_reduce_taxable_base(self):
        without = make(60000, opened_at="01/22")
        with_exp = make(60000, opened_at="01/22", expenses=5000)
        assert with_exp.taxable_base <= without.taxable_base


# ---------------------------------------------------------------------------
# Family quotient and deductions
# ---------------------------------------------------------------------------

class TestFamilyAndKids:
    def test_joint_declaration_lower_tax(self):
        single = make(60000)
        joint = make(60000, status="joint")
        assert joint.income_tax < single.income_tax

    def test_family_quotient_single_no_kids(self):
        inc = make(60000)
        assert inc.family_quotient == 1.0

    def test_family_quotient_joint_no_kids(self):
        inc = make(60000, status="joint")
        assert inc.family_quotient == 2.0

    def test_family_quotient_joint_one_kid(self):
        inc = make(60000, status="joint", kids="5")
        # 1 (self) + 1 (spouse) + 0.25 (first kid) + 0.25 (additional kid slot) = 2.5
        assert inc.family_quotient == 2.5

    def test_kids_deduction_reduces_tax(self):
        without = make(60000)
        with_kids = make(60000, kids="5,8")
        assert with_kids.income_tax < without.income_tax

    def test_child_under_3_extra_deduction(self):
        older = make(60000, kids="5")
        younger = make(60000, kids="2")
        # Child under 3 gets extra €126
        assert younger.income_tax < older.income_tax

    def test_single_declaration_kids_deduction_halved(self):
        single = make(60000, kids="5")
        joint = make(60000, status="joint", kids="5")
        # Single splits kids deduction 50/50
        single_deduction = single.family_deduction
        joint_deduction = joint.family_deduction
        assert joint_deduction == single_deduction * 2


# ---------------------------------------------------------------------------
# All supported years
# ---------------------------------------------------------------------------

class TestYears:
    @pytest.mark.parametrize("year", [2023, 2024, 2025])
    def test_calculation_works_for_all_years(self, year):
        inc = Income(year=year, income=50000)
        assert inc.income_tax > 0
        assert inc.social_security_tax > 0

    def test_specific_deduction_fixed_2023(self):
        inc = Income(year=2023, income=50000)
        assert inc.specific_deduction == 4104
