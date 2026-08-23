import frappe
from frappe.model.document import Document


class LKStatutoryConfig(Document):
	"""Single DocType holding the *current* statutory rates/slabs.

	On every save this publishes a dated snapshot to `LK Statutory Config
	Version` (autonamed by ``effective_from``) so that a payroll run for a
	past period keeps recalculating with the rates that were actually in
	force then, even after this Single has moved on to newer rates -- see
	``eudext_lk.tax.rates.get_effective_config_doc``.
	"""

	def on_update(self):
		self.publish_version()

	def publish_version(self):
		# Nothing to snapshot yet -- e.g. the blank Single record Frappe
		# creates automatically when this app is installed.
		if not self.effective_from:
			return

		version_name = frappe.db.exists(
			"LK Statutory Config Version", {"effective_from": self.effective_from}
		)
		version = (
			frappe.get_doc("LK Statutory Config Version", version_name)
			if version_name
			else frappe.new_doc("LK Statutory Config Version")
		)

		version.effective_from = self.effective_from
		version.employee_epf_rate = self.employee_epf_rate
		version.employer_epf_rate = self.employer_epf_rate
		version.etf_rate = self.etf_rate

		version.set("apit_slabs", [])
		for row in self.apit_slabs:
			version.append(
				"apit_slabs",
				{
					"from_amount": row.from_amount,
					"to_amount": row.to_amount,
					"rate": row.rate,
				},
			)

		version.set("epf_eligible_components", [])
		for row in self.epf_eligible_components:
			version.append(
				"epf_eligible_components", {"salary_component": row.salary_component}
			)

		version.save(ignore_permissions=True)
