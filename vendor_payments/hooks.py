from . import __version__ as app_version

app_name = "vendor_payments"
app_title = "Vendor Payments"
app_publisher = "Frappe"
app_description = "Vendor Payments"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "vendor_payments@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/vendor_payments/css/vendor_payments.css"
# app_include_js = "/assets/vendor_payments/js/vendor_payments.js"

# include js, css files in header of web template
# web_include_css = "/assets/vendor_payments/css/vendor_payments.css"
# web_include_js = "/assets/vendor_payments/js/vendor_payments.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "vendor_payments/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Purchase Invoice": "public/js/purchase_invoice.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Tax Withholding Category": "public/js/tax_withholding_category.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

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

# Installation
# ------------

# before_install = "vendor_payments.install.before_install"
# after_install = "vendor_payments.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "vendor_payments.notifications.get_notification_config"

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
    "Bank Account": "vendor_payments.vendor_payments.hooks.bank_account.CustomBankAccount",
    "Supplier": "vendor_payments.vendor_payments.hooks.supplier.CustomSupplier",
    "Purchase Invoice": "vendor_payments.vendor_payments.hooks.purchase_invoice.CustomInvoiceDeatails",
    "Payment Entry": "vendor_payments.vendor_payments.hooks.payment_entry.CustomPaymentEntry",
}
# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Purchase Invoice": {
        "on_change": "vendor_payments.vendor_payments.reminders.notify",
    },
    "Purchase Order": {
        "on_change": "vendor_payments.vendor_payments.reminders.notify",
    },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"vendor_payments.tasks.all"
# 	],
# 	"daily": [
# 		"vendor_payments.tasks.daily"
# 	],
# 	"hourly": [
# 		"vendor_payments.tasks.hourly"
# 	],
# 	"weekly": [
# 		"vendor_payments.tasks.weekly"
# 	]
# 	"monthly": [
# 		"vendor_payments.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "vendor_payments.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "vendor_payments.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "vendor_payments.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
    {
        "doctype": "{doctype_1}",
        "filter_by": "{filter_by}",
        "redact_fields": ["{field_1}", "{field_2}"],
        "partial": 1,
    },
    {
        "doctype": "{doctype_2}",
        "filter_by": "{filter_by}",
        "partial": 1,
    },
    {
        "doctype": "{doctype_3}",
        "strict": False,
    },
    {"doctype": "{doctype_4}"},
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"vendor_payments.auth.validate"
# ]
