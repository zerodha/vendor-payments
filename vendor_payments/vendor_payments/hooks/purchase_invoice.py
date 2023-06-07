import frappe
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from erpnext.accounts.doctype.tax_withholding_category.tax_withholding_category import (
    get_party_tax_withholding_details,
)
from vendor_payments.vendor_payments import constants


class CustomInvoiceDeatails(PurchaseInvoice):
    def validate_round_off(self):
        # if self.taxes
        old_doc = self.get_doc_before_save()
        for index, tax in enumerate(old_doc.taxes):
            if "TDS" in tax.account_head:
                if abs(tax.tax_amount - self.taxes[index].tax_amount) > 3:
                    frappe.throw("TDS amount cannot be changed by more than 3 rupees.")
            else:
                continue

    def validate(self):
        if (
            self.workflow_state == constants.ACCOUNT_MANAGER_REVIEW_PENDING
            and not self.edit_invoice_taxes
        ):
            # If tax rates are edited, then don't reset them.
            # Clear all taxes first on save so that any change can be re-calculated.
            self.taxes = []
        super(CustomInvoiceDeatails, self).validate()
        self.table_name = "`tabPurchase Invoice`"
        if not getattr(self, "_doc_before_save", None):
            # If no _doc_before_save, i.e if new doc only then this validation
            res = frappe.db.sql(
                """
            SELECT count(*)
            FROM {0}
            WHERE supplier=%s AND bill_no=%s AND financial_year=%s
            """.format(
                    self.table_name
                ),
                [self.supplier, self.bill_no, self.financial_year],
            )[0]
            if res[0] >= 1:
                frappe.throw(
                    "Duplicate invoice number not allowed in the given financial year under the given company for this supplier"
                )
        else:
            if "auditor" in self.workflow_state.lower():
                self.validate_round_off()

        if self.workflow_state == constants.ACCOUNT_MANAGER_REVIEW_PENDING:
            self.add_gst_taxes()
            # call parent method once all taxes are added in tax table.
            self.calculate_taxes_and_totals()

        # if (
        #     self.workflow_state == constants.AUDITOR_REVIEW_PENDING
        #     and len(getattr(self, "taxes_and_charges", [])) == 0
        #     and not self.is_tds_not_applicable
        # ):
        #     frappe.throw(
        #         "No TDS or GST entered by the Accounts team. Please have a look at it before sending to audit team"
        #     )

    def add_gst_credit_note_details(self):
        to_save = []
        for tax in self.taxes:
            if "GST Credit" in tax.account_head:
                continue
            to_save.append(tax)
        self.taxes = to_save

        for credit in self.gst_credit_note:
            self.append(
                "taxes",
                dict(
                    category="Total",
                    account_head=f"GST Credit - {constants.COMPANY_ABBR[self.company]}",
                    add_deduct_tax="Deduct",
                    charge_type="Actual",
                    tax_amount=credit.total_amount_including_gst,
                    description="GST Input Credit",
                ),
            )

    def add_gst_taxes(self):
        if (
            self.gst
            and len(self.taxes) == 1
            and "tds" in self.taxes[0].account_head.lower()
        ) or self.is_tds_not_applicable:
            if self.is_interstate:
                rates = [self.igst]
                account_types = ["IGST"]
            else:
                rates = [self.sgst, self.cgst]
                account_types = ["SGST", "CGST"]

            for tax in self.taxes:
                if "cgst" in tax.account_head.lower():
                    return
                elif "sgst" in tax.account_head.lower():
                    return
                elif "igst" in tax.account_head.lower():
                    return

            for index, rate in enumerate(rates):
                self.append(
                    "taxes",
                    dict(
                        category="Total",
                        account_head=f"{account_types[index]} - {constants.COMPANY_ABBR[self.company]}",
                        add_deduct_tax="Add",
                        charge_type="On Net Total",
                        rate=rate,
                        description="GST Taxes",
                    ),
                )

            temp1 = self.taxes[0].idx
            temp2 = self.taxes[-1].idx
            self.taxes[0].idx = temp2
            self.taxes[-1].idx = temp1
            self.taxes[0], self.taxes[-1] = self.taxes[-1], self.taxes[0]
            self.add_gst_credit_note_details()

    def on_change(self):
        if "reject" in self.workflow_state.lower() and not self.rejection_reason:
            frappe.throw(
                "Rejection reason is mandatory. Please enter a valid rejection reason."
            )

        old_doc = self.get_doc_before_save()
        if (
            old_doc
            and self.workflow_state
            in [
                constants.OPEN,
                constants.APPROVER_REVIEW_PENDING,
                constants.ACCOUNT_MANAGER_REVIEW_PENDING,
                constants.AUDITOR_MANAGER_REVIEW_PENDING,
            ]
            and "reject" in old_doc.workflow_state.lower()
        ):
            self.add_comment(
                "Comment",
                f"Rejection reason by {old_doc.modified_by} - {self.rejection_reason}",
            )
            self.db_set("rejection_reason", None)

    def set_tax_withholding(self):
        if not self.apply_tds:
            return

        tax_withholding_details = get_party_tax_withholding_details(
            self, self.tax_withholding_category
        )

        if not tax_withholding_details:
            return

        accounts = []
        for d in self.taxes:
            # d.update(tax_withholding_details)
            # if d.account_head == tax_withholding_details.get("account_head"):
            #     d.update(tax_withholding_details)

            accounts.append(d.account_head)

        if not accounts or tax_withholding_details.get("account_head") not in accounts:
            self.append("taxes", tax_withholding_details)

        to_remove = [
            d
            for d in self.taxes
            if not d.tax_amount
            and d.account_head == tax_withholding_details.get("account_head")
        ]

        for d in to_remove:
            self.remove(d)

        # calculate totals again after applying TDS
        self.calculate_taxes_and_totals()

    def before_save(self):
        if self.rejection_reason:
            self.rejection_workflow_state = self.workflow_state


@frappe.whitelist()
def fetch_bank_account_details(supplier):
    return {
        "bank_id": frappe.get_value(
            "Bank Account", {"party": supplier, "is_default": 1}, "name"
        ),
    }
