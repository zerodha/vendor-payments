import frappe
from erpnext.buying.doctype.supplier.supplier import Supplier
from frappe.model.naming import make_autoname
from frappe.utils import get_link_to_form

from vendor_payments.vendor_payments import constants


class CustomSupplier(Supplier):
    def autoname(self):
        self.name = make_autoname(
            f"{constants.COMPANY_ABBR[self.from_company].upper()}_SUPL_"
        )

    def validate(self):
        old_doc = getattr(self, "_doc_before_save", None)
        if getattr(old_doc, "workflow_state", None) == "Approved":
            self.docstatus = 0
            self.workflow_state = "Open"
            frappe.msgprint("Please get approval of the changes saved")

        # Validate default count of approvers. Only one default approver is allowed
        count = 0
        for approver in self.approvers:
            if approver.is_default == 1:
                count += 1
        if count > 1:
            frappe.throw(
                "Multiple default approvers are not allowed. Please set only one approver as default"
            )

    def on_change(self):
        recipients = []
        subject = message = None
        if self.workflow_state == constants.APPROVER_REVIEW_PENDING:
            approver = fetch_default_approver(self.name)["approver"]
            if not approver:
                frappe.throw("Please set atleast one default approver")

            frappe.share.add(
                self.doctype,
                self.name,
                approver,
                flags={"ignore_share_permission": True},
            )
            recipients = [approver]
            subject = (
                f"Supplier details of {self.supplier_name[:10]}.. needs your approval"
            )
            message = f"""
            Supplier details of {self.supplier_name} needs your approval. Please check at: {get_link_to_form('Supplier', self.name)}. 

            You get this email either 
            if a new supplier (vendor) is created and you are its approver 
            or
            if some detail is changed (or updated) in an already created supplier (vendor) to which you are the approver.
            """

        if recipients:
            frappe.sendmail(
                recipients=recipients,
                subject=subject,
                message=message,
            )


@frappe.whitelist()
def fetch_approvers(doctype, txt, searchfield, start, page_len, filters):
    # Return list of approvers for the given supplier
    return [
        [approver.approver]
        for approver in frappe.get_doc("Supplier", filters).approvers
    ]


@frappe.whitelist()
def fetch_default_approver(supplier):
    # Return default approver for the given supplier
    res = frappe.db.sql(
        """
    SELECT approver 
    FROM `tabSupplier Approver Details`
    WHERE parent=%s
    AND is_default=1
    """,
        [supplier],
    )
    if not res:
        return {"approver": None}

    return {"approver": res[0][0]}
