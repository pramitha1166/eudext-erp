"""doc_events hook: Payroll Entry.on_submit -- offer to create an
LK Bulk Payment Batch pre-populated from the submitted Salary Slips' net
pay and each employee's bank details.
"""

from __future__ import annotations

import frappe
from frappe import _


def offer_bulk_payment_batch(doc, method=None):
	link = (
		f'/app/lk-bulk-payment-batch/new?source_type=Payroll Entry'
		f"&payroll_entry={frappe.utils.quote(doc.name)}"
	)
	frappe.msgprint(
		_("Payroll Entry submitted.")
		+ " "
		+ f'<a href="{link}">{_("Create an LK Bulk Payment Batch")}</a>'
		+ " "
		+ _("to generate the bank payment file for these salary slips."),
		title=_("Bank Payment File"),
		indicator="blue",
	)


@frappe.whitelist()
def create_bulk_payment_batch(payroll_entry: str, bank_format: str, debit_account: str):
	slips = frappe.get_all(
		"Salary Slip",
		filters={"payroll_entry": payroll_entry, "docstatus": 1},
		fields=["name", "employee", "employee_name", "net_pay"],
	)
	if not slips:
		frappe.throw(_("No submitted Salary Slips found for Payroll Entry {0}").format(payroll_entry))

	batch = frappe.new_doc("LK Bulk Payment Batch")
	batch.source_type = "Payroll Entry"
	batch.payroll_entry = payroll_entry
	batch.bank_format = bank_format
	batch.debit_account = debit_account
	batch.value_date = frappe.utils.nowdate()

	for slip in slips:
		bank_details = (
			frappe.db.get_value(
				"Employee",
				slip.employee,
				["bank_code", "branch_code", "bank_account_no"],
				as_dict=True,
			)
			or {}
		)
		batch.append(
			"payee_lines",
			{
				"party_type": "Employee",
				"party": slip.employee,
				"party_name": slip.employee_name,
				"account_no": bank_details.get("bank_account_no"),
				"bank_code": bank_details.get("bank_code"),
				"branch_code": bank_details.get("branch_code"),
				"amount": slip.net_pay,
				"reference": slip.name,
			},
		)

	batch.insert()
	return batch.name
