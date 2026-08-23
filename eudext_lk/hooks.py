app_name = "eudext_lk"
app_title = "Eudext LK"
app_publisher = "Eudext"
app_description = "Sri Lanka statutory payroll, tax, and bank payment localisation for ERPNext/HR"
app_email = "pramitha.wanigarathne@gmail.com"
app_license = "mit"

# Apps
# ------------------

required_apps = ["frappe", "erpnext", "hrms"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "eudext_lk",
# 		"logo": "/assets/eudext_lk/logo.png",
# 		"title": "Eudext LK",
# 		"route": "/eudext_lk",
# 		"has_permission": "eudext_lk.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/eudext_lk/css/eudext_lk.css"
# app_include_js = "/assets/eudext_lk/js/eudext_lk.js"

# include js, css files in header of web template
# web_include_css = "/assets/eudext_lk/css/eudext_lk.css"
# web_include_js = "/assets/eudext_lk/js/eudext_lk.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "eudext_lk/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "eudext_lk/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "eudext_lk.utils.jinja_methods",
# 	"filters": "eudext_lk.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "eudext_lk.install.before_install"
# after_install = "eudext_lk.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "eudext_lk.uninstall.before_uninstall"
# after_uninstall = "eudext_lk.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "eudext_lk.utils.before_app_install"
# after_app_install = "eudext_lk.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "eudext_lk.utils.before_app_uninstall"
# after_app_uninstall = "eudext_lk.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "eudext_lk.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	# HRMS's Salary Component formula sandbox does not expose `frappe`, so
	# there is no way for a formula to call a whitelisted method directly.
	# This subclass extends the sandbox's whitelisted_globals instead -- see
	# payroll/salary_slip_override.py.
	"Salary Slip": "eudext_lk.payroll.salary_slip_override.EudextSalarySlip",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Salary Slip": {
		"validate": "eudext_lk.payroll.salary_slip.inject_statutory_amounts",
	},
	"Payroll Entry": {
		"on_submit": "eudext_lk.payroll.payroll_entry.offer_bulk_payment_batch",
	},
}

# Fixtures
# --------

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			["dt", "in", ["Employee", "Supplier", "Salary Component"]],
			[
				"fieldname",
				"in",
				["epf_number", "bank_code", "branch_code", "bank_account_no", "lk_epf_eligible"],
			],
		],
	},
	{
		"dt": "Salary Component",
		"filters": [
			["name", "in", ["EPF Employee 8%", "EPF Employer 12%", "ETF 3%", "APIT"]],
		],
	},
]

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"eudext_lk.tasks.all"
# 	],
# 	"daily": [
# 		"eudext_lk.tasks.daily"
# 	],
# 	"hourly": [
# 		"eudext_lk.tasks.hourly"
# 	],
# 	"weekly": [
# 		"eudext_lk.tasks.weekly"
# 	],
# 	"monthly": [
# 		"eudext_lk.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "eudext_lk.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "eudext_lk.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "eudext_lk.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["eudext_lk.utils.before_request"]
# after_request = ["eudext_lk.utils.after_request"]

# Job Events
# ----------
# before_job = ["eudext_lk.utils.before_job"]
# after_job = ["eudext_lk.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"eudext_lk.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

