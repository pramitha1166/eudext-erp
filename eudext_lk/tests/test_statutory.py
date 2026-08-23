"""Boundary-value tests for eudext_lk.utils.statutory.

These import only the pure ``utils`` module -- no Frappe, no site, no
database -- so they run standalone under ``pytest`` (which fully supports
``unittest.TestCase``) as well as under ``bench run-tests --app eudext_lk``,
whose runner discovers tests via ``unittest.TestLoader``.
"""

import unittest
from decimal import Decimal

from eudext_lk.utils.statutory import (
    APITSlab,
    StatutoryRates,
    calc_apit,
    calc_epf_employee,
    calc_epf_employer,
    calc_etf,
    calc_gratuity,
)

RATES = StatutoryRates(
    employee_epf_rate=Decimal("8"),
    employer_epf_rate=Decimal("12"),
    etf_rate=Decimal("3"),
)

# Round, easy-to-hand-verify slabs used only for these tests -- real values
# live on the LK Statutory Config DocType, never hardcoded in application code.
SLABS = [
    APITSlab(Decimal("0"), Decimal("100000"), Decimal("0")),
    APITSlab(Decimal("100000"), Decimal("150000"), Decimal("6")),
    APITSlab(Decimal("150000"), Decimal("200000"), Decimal("12")),
    APITSlab(Decimal("200000"), None, Decimal("18")),
]


class TestEPF(unittest.TestCase):
    def test_zero_gross(self):
        assert calc_epf_employee(Decimal("0"), RATES) == Decimal("0.00")
        assert calc_epf_employer(Decimal("0"), RATES) == Decimal("0.00")

    def test_negative_gross_treated_as_zero(self):
        assert calc_epf_employee(Decimal("-500"), RATES) == Decimal("0.00")

    def test_typical_gross(self):
        gross = Decimal("100000")
        assert calc_epf_employee(gross, RATES) == Decimal("8000.00")
        assert calc_epf_employer(gross, RATES) == Decimal("12000.00")

    def test_rounding_half_up(self):
        # 33333.335 -> employee 8% = 2666.6668 -> rounds to 2666.67
        gross = Decimal("33333.335")
        assert calc_epf_employee(gross, RATES) == Decimal("2666.67")


class TestETF(unittest.TestCase):
    def test_zero_gross(self):
        assert calc_etf(Decimal("0"), RATES) == Decimal("0.00")

    def test_typical_gross(self):
        assert calc_etf(Decimal("100000"), RATES) == Decimal("3000.00")


class TestAPIT(unittest.TestCase):
    def test_zero_taxable(self):
        assert calc_apit(Decimal("0"), SLABS) == Decimal("0.00")

    def test_no_slabs_configured(self):
        assert calc_apit(Decimal("500000"), []) == Decimal("0.00")

    def test_within_relief_slab(self):
        assert calc_apit(Decimal("50000"), SLABS) == Decimal("0.00")

    def test_exact_relief_upper_edge(self):
        assert calc_apit(Decimal("100000"), SLABS) == Decimal("0.00")

    def test_just_above_relief_edge(self):
        assert calc_apit(Decimal("100001"), SLABS) == Decimal("0.06")

    def test_exact_second_slab_edge(self):
        # (150000 - 100000) * 6% = 3000
        assert calc_apit(Decimal("150000"), SLABS) == Decimal("3000.00")

    def test_exact_third_slab_edge(self):
        # 3000 + (200000 - 150000) * 12% = 3000 + 6000
        assert calc_apit(Decimal("200000"), SLABS) == Decimal("9000.00")

    def test_above_top_open_ended_slab(self):
        # 9000 + (250000 - 200000) * 18% = 9000 + 9000
        assert calc_apit(Decimal("250000"), SLABS) == Decimal("18000.00")


class TestGratuity(unittest.TestCase):
    def test_below_minimum_service(self):
        assert calc_gratuity(Decimal("50000"), Decimal("4")) == Decimal("0.00")

    def test_exact_minimum_service(self):
        assert calc_gratuity(Decimal("50000"), Decimal("5")) == Decimal("125000.00")

    def test_longer_service(self):
        assert calc_gratuity(Decimal("50000"), Decimal("10")) == Decimal("250000.00")

    def test_zero_basic(self):
        assert calc_gratuity(Decimal("0"), Decimal("10")) == Decimal("0.00")


if __name__ == "__main__":
    unittest.main()
