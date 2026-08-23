"""LK ETF Return: per-employee EPF-eligible gross and employer ETF (3%)
contribution for submitted Salary Slips in a period.
"""

from __future__ import annotations

import frappe
from frappe import _

from eudext_lk.tax.rates import get_effective_rates, get_eligible_component_set
from eudext_lk.utils.earnings import epf_eligible_gross
from eudext_lk.utils.statutory import calc_etf


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		{"label": _("Salary Slip"), "fieldname": "salary_slip", "fieldtype": "Link", "options": "Salary Slip", "width": 140},
		{"label": _("EPF-Eligible Gross"), "fieldname": "eligible_gross", "fieldtype": "Currency", "width": 150},
		{"label": _("ETF (3%)"), "fieldname": "etf", "fieldtype": "Currency", "width": 130},
	]


def get_data(filters):
	conditions = {"docstatus": 1}
	if filters.get("company"):
		conditions["company"] = filters.company
	if filters.get("from_date"):
		conditions["start_date"] = [">=", filters.from_date]
	if filters.get("to_date"):
		conditions["end_date"] = ["<=", filters.to_date]
	if filters.get("employee"):
		conditions["employee"] = filters.employee

	slip_names = frappe.get_all("Salary Slip", filters=conditions, pluck="name")

	rows = []
	for name in slip_names:
		slip = frappe.get_doc("Salary Slip", name)
		as_of = slip.start_date
		rates = get_effective_rates(as_of)
		eligible_components = get_eligible_component_set(as_of)
		eligible_gross = epf_eligible_gross(slip, eligible_components)
		if eligible_gross <= 0:
			continue

		etf = calc_etf(eligible_gross, rates)

		rows.append(
			{
				"employee": slip.employee,
				"employee_name": slip.employee_name,
				"salary_slip": slip.name,
				"eligible_gross": float(eligible_gross),
				"etf": float(etf),
			}
		)
	return rows
