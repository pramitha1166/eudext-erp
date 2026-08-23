import frappe
from frappe.model.document import Document


class LKStatutoryConfigVersion(Document):
	"""Read-mostly historical snapshot of LK Statutory Config, one per
	effective_from date. Written exclusively via
	LKStatutoryConfig.publish_version -- see that class for details.
	"""

	pass
