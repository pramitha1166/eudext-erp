"""doc_events hook: Salary Slip.validate.

Runs after HRMS's own Salary Slip controller has evaluated every component
formula, so it has the full ``earnings``/``deductions`` breakdown available.
It recomputes the LK statutory amounts authoritatively from
utils/statutory.py + utils/earnings.py (never trusting the formula preview
alone, since the formula only sees the scalar ``gross_pay`` while the real
EPF-eligible gross must exclude overtime/bonus/reimbursement per the
EPF-eligible component whitelist on LK Statutory Config) and overwrites the
matching deduction rows in place.
"""

from __future__ import annotations

from eudext_lk.tax.rates import (
	get_effective_apit_slabs,
	get_effective_rates,
	get_eligible_component_set,
)
from eudext_lk.utils.earnings import epf_eligible_gross
from eudext_lk.utils.statutory import calc_apit, calc_epf_employee, calc_epf_employer, calc_etf

EPF_EMPLOYEE_COMPONENT = "EPF Employee 8%"
EPF_EMPLOYER_COMPONENT = "EPF Employer 12%"
ETF_COMPONENT = "ETF 3%"
APIT_COMPONENT = "APIT"


def _set_row_amount(rows, component: str, amount: float) -> bool:
	for row in rows:
		if row.salary_component == component:
			row.amount = amount
			return True
	return False


def inject_statutory_amounts(doc, method=None):
	as_of = doc.start_date or doc.posting_date

	rates = get_effective_rates(as_of)
	slabs = get_effective_apit_slabs(as_of)
	eligible_components = get_eligible_component_set(as_of)

	eligible_gross = epf_eligible_gross(doc, eligible_components)

	epf_employee = calc_epf_employee(eligible_gross, rates)
	epf_employer = calc_epf_employer(eligible_gross, rates)
	etf = calc_etf(eligible_gross, rates)
	apit = calc_apit(eligible_gross, slabs)

	changed = False
	changed |= _set_row_amount(doc.deductions, EPF_EMPLOYEE_COMPONENT, float(epf_employee))
	changed |= _set_row_amount(doc.deductions, EPF_EMPLOYER_COMPONENT, float(epf_employer))
	changed |= _set_row_amount(doc.deductions, ETF_COMPONENT, float(etf))
	changed |= _set_row_amount(doc.deductions, APIT_COMPONENT, float(apit))

	if changed and hasattr(doc, "calculate_net_pay"):
		doc.calculate_net_pay()
