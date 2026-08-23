from decimal import Decimal

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate
from frappe.utils.file_manager import save_file

# Importing the concrete generator module registers it into
# GENERATOR_REGISTRY (see banking/base.py); add new banks by importing their
# module here the same way -- see README.md.
import eudext_lk.banking.commercial_bank  # noqa: F401
from eudext_lk.banking.base import (
	BankFileContext,
	BankValidationError,
	PayeeLine,
	get_generator,
)


class LKBulkPaymentBatch(Document):
	def validate(self):
		total = Decimal("0")
		for row in self.payee_lines:
			total += Decimal(str(row.amount or 0))
		self.total_amount = float(total)

	def on_submit(self):
		self.status = "Submitted"

	def on_cancel(self):
		self.status = "Cancelled"

	def missing_bank_detail_rows(self):
		return [
			row
			for row in self.payee_lines
			if not (row.account_no and row.bank_code and row.branch_code)
		]

	@frappe.whitelist()
	def generate_file(self):
		missing = self.missing_bank_detail_rows()
		if missing:
			rows = ", ".join(str(row.idx) for row in missing)
			frappe.throw(
				_(
					"Cannot generate file: payee row(s) {0} are missing "
					"account number, bank code, or branch code."
				).format(rows)
			)

		bank_format = frappe.get_doc("LK Bank File Format", self.bank_format)
		generator_cls = get_generator(bank_format.format_code)

		context = BankFileContext(
			bank_name=bank_format.bank_name,
			format_code=bank_format.format_code,
			debit_account=self.debit_account,
			value_date=getdate(self.value_date).strftime(bank_format.date_format or "%d/%m/%Y"),
			payees=[
				PayeeLine(
					party_name=row.party_name or row.party or "",
					account_no=row.account_no,
					bank_code=row.bank_code,
					branch_code=row.branch_code,
					amount=Decimal(str(row.amount or 0)),
					reference=row.reference or "",
				)
				for row in self.payee_lines
			],
			delimiter=bank_format.delimiter or ",",
			has_header=bool(bank_format.has_header),
			has_trailer=bool(bank_format.has_trailer),
			amount_in_cents=(bank_format.amount_format == "Cents"),
		)

		try:
			content = generator_cls(context).generate()
		except BankValidationError as e:
			frappe.throw(str(e))

		filename = f"{self.name}-{bank_format.format_code}.{bank_format.file_extension or 'csv'}"
		file_doc = save_file(filename, content, self.doctype, self.name, is_private=1)

		self.db_set("generated_file", file_doc.file_url)
		self.db_set("status", "File Generated")
		return file_doc.file_url
