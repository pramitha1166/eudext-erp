"""Frappe-aware adapter that turns LK Statutory Config (or the historic
LK Statutory Config Version applicable to a given date) into the plain
dataclasses consumed by eudext_lk.utils.statutory. This is the
only place in the app that decides *which* config record applies to a
payroll date -- calculation logic itself stays in utils/.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional, Set

import frappe

from eudext_lk.utils.statutory import APITSlab, StatutoryRates


def get_effective_config_doc(as_of_date=None):
	as_of_date = frappe.utils.getdate(as_of_date) if as_of_date else frappe.utils.getdate()

	version_name = frappe.db.get_value(
		"LK Statutory Config Version",
		{"effective_from": ["<=", as_of_date]},
		"name",
		order_by="effective_from desc",
	)
	if version_name:
		return frappe.get_doc("LK Statutory Config Version", version_name)
	return frappe.get_single("LK Statutory Config")


def get_effective_rates(as_of_date=None) -> StatutoryRates:
	config = get_effective_config_doc(as_of_date)
	return StatutoryRates(
		employee_epf_rate=Decimal(str(config.employee_epf_rate or 0)),
		employer_epf_rate=Decimal(str(config.employer_epf_rate or 0)),
		etf_rate=Decimal(str(config.etf_rate or 0)),
	)


def get_effective_apit_slabs(as_of_date=None) -> List[APITSlab]:
	config = get_effective_config_doc(as_of_date)
	slabs = []
	for row in config.apit_slabs:
		slabs.append(
			APITSlab(
				from_amount=Decimal(str(row.from_amount or 0)),
				to_amount=Decimal(str(row.to_amount)) if row.to_amount else None,
				rate=Decimal(str(row.rate or 0)),
			)
		)
	return slabs


def get_eligible_component_set(as_of_date=None) -> Set[str]:
	config = get_effective_config_doc(as_of_date)
	return {row.salary_component for row in config.epf_eligible_components}
