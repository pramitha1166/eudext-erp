"""LK EPF Return (C Form): per-employee EPF-eligible gross, employee (8%)
and employer (12%) contributions for submitted Salary Slips in a period.
"""

from __future__ import annotations

import frappe
from frappe import _

from eudext_lk.tax.rates import get_effective_rates, get_eligible_component_set
from eudext_lk.utils.earnings import epf_eligible_gross
from eudext_lk.utils.statutory import calc_epf_employee, calc_epf_employer


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		{"label": _("EPF Number"), "fieldname": "epf_number", "fieldtype": "Data", "width": 120},
		{"label": _("Salary Slip"), "fieldname": "salary_slip", "fieldtype": "Link", "options": "Salary Slip", "width": 140},
		{"label": _("EPF-Eligible Gross"), "fieldname": "eligible_gross", "fieldtype": "Currency", "width": 150},
		{"label": _("Employee EPF (8%)"), "fieldname": "epf_employee", "fieldtype": "Currency", "width": 150},
		{"label": _("Employer EPF (12%)"), "fieldname": "epf_employer", "fieldtype": "Currency", "width": 150},
		{"label": _("Total EPF"), "fieldname": "total_epf", "fieldtype": "Currency", "width": 130},
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

		epf_employee = calc_epf_employee(eligible_gross, rates)
		epf_employer = calc_epf_employer(eligible_gross, rates)

		rows.append(
			{
				"employee": slip.employee,
				"employee_name": slip.employee_name,
				"epf_number": frappe.db.get_value("Employee", slip.employee, "epf_number"),
				"salary_slip": slip.name,
				"eligible_gross": float(eligible_gross),
				"epf_employee": float(epf_employee),
				"epf_employer": float(epf_employer),
				"total_epf": float(epf_employee + epf_employer),
			}
		)
	return rows
