"""override_doctype_class target for Salary Slip.

HRMS's own formula sandbox (``SalarySlip.whitelisted_globals``, consumed by
its private ``_safe_eval``) is deliberately minimal -- it does not expose
``frappe`` at all, so a formula cannot call ``frappe.call(...)``. Since
hrms/salary_slip.py cannot be edited, this subclass is the sanctioned way to
extend that sandbox: it adds our whitelisted formula functions to
``whitelisted_globals`` as plain callables, so the fixture Salary Components
can call them by name directly, e.g. ``epf_employee_amount(gross_pay,
start_date)``.
"""

from __future__ import annotations

from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

from eudext_lk.payroll.formulas import (
	apit_amount,
	epf_employee_amount,
	epf_employer_amount,
	etf_amount,
)


class EudextSalarySlip(SalarySlip):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.whitelisted_globals.update(
			{
				"epf_employee_amount": epf_employee_amount,
				"epf_employer_amount": epf_employer_amount,
				"etf_amount": etf_amount,
				"apit_amount": apit_amount,
			}
		)
