"""Whitelisted entry points that the fixture Salary Components' ``formula``
fields call directly by name (e.g. ``epf_employee_amount(gross_pay,
start_date)``), so the formula text never hardcodes a rate -- it always
delegates to config-driven calculation in utils/statutory.py.

HRMS's own formula sandbox does not expose ``frappe``, so these functions
reach the formula not via ``frappe.call`` but by being injected into
``SalarySlip.whitelisted_globals`` by the ``override_doctype_class`` in
payroll/salary_slip_override.py. They stay ``@frappe.whitelist()``-decorated
so they are still independently callable/testable via the API.

The authoritative EPF-eligible-gross computation (which needs the full
earnings breakdown, not just the scalar ``gross_pay`` a formula sees) still
happens in payroll/salary_slip.py's validate hook; these formulas give a
reasonable live preview while the form is being edited.
"""

from __future__ import annotations

from decimal import Decimal

import frappe

from eudext_lk.tax.rates import get_effective_apit_slabs, get_effective_rates
from eudext_lk.utils.statutory import (
	calc_apit,
	calc_epf_employee,
	calc_epf_employer,
	calc_etf,
)


@frappe.whitelist()
def epf_employee_amount(gross_pay=0, posting_date=None) -> float:
	rates = get_effective_rates(posting_date)
	return float(calc_epf_employee(Decimal(str(gross_pay or 0)), rates))


@frappe.whitelist()
def epf_employer_amount(gross_pay=0, posting_date=None) -> float:
	rates = get_effective_rates(posting_date)
	return float(calc_epf_employer(Decimal(str(gross_pay or 0)), rates))


@frappe.whitelist()
def etf_amount(gross_pay=0, posting_date=None) -> float:
	rates = get_effective_rates(posting_date)
	return float(calc_etf(Decimal(str(gross_pay or 0)), rates))


@frappe.whitelist()
def apit_amount(gross_pay=0, posting_date=None) -> float:
	slabs = get_effective_apit_slabs(posting_date)
	return float(calc_apit(Decimal(str(gross_pay or 0)), slabs))
