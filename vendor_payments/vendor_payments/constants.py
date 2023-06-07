import frappe

# Workflow States
APPROVER_REVIEW_PENDING = "Approver Review Pending"
APPROVER_REJECTED = "Approver Rejected"
ACCOUNT_MANAGER_REVIEW_PENDING = "Account Manager Review Pending"
ACCOUNT_MANAGER_REJECTED = "Account Manager Rejected"

AUDITOR_REVIEW_PENDING = "Auditor Review Pending"
AUDITOR_APPROVED = "Auditor Approved"
AUDITOR_MANAGER_REVIEW_PENDING = "Auditor Manager Review Pending"
AUDITOR_MANAGER_APPROVED = "Auditor Manager Approved"
AUDITOR_REJECTED = "Auditor Rejected"
AUDITOR_MANAGER_REJECTED = "Auditor Manager Rejected"

PAYMENT_IN_PROGRESS = "Payment In Progress"
PAYMENT_DONE = "Paid"

OPEN = "Open"

# Roles
AUDITOR = "Invoice Auditor"
AUDITOR_MANAGER = "Auditor Manager"
PAYOUT = "Payout"
ACCOUNTS_MANAGER = "Accounts Manager"

COMPANY_ABBR = {
    c.get("name"): c.get("abbr")
    for c in frappe.get_list("Company", fields=["name", "abbr"])
}


# Mode of payments
NEFT = "NEFT"
CASH = "CASH"
