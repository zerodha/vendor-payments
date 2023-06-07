import frappe
from erpnext.accounts.doctype.bank_account.bank_account import BankAccount

from vendor_payments.vendor_payments import queries


class CustomBankAccount(BankAccount):
    def validate(self):
        super(CustomBankAccount, self).validate()

        ba_details = frappe.db.sql(
            queries.FETCH_BANK_ACCOUNT_DETAILS,
            [self.party],
        )
        ba_account_name = None
        if ba_details:
            ba_account_name = ba_details[0][0]

        if (
            ba_account_name
            and ba_account_name != self.name
            and self.is_default
            and self.party
        ):
            frappe.throw("Only one default Bank Account is allowed for a supplier")

        if not ba_account_name:
            # Add a default bank account for a supplier if not already present
            self.is_default = 1
            frappe.msgprint(
                f"This bank account is set as default bank account for supplier {self.party}. Since there has to be 1 default bank account for every supplier"
            )
        else:
            self.docstatus = 0
            self.workflow_state = "Draft"

        self.company = None

    def autoname(self):
        pass
