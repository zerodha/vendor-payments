# Copyright (c) 2022, zerodha and contributors
# For license information, please see license.txt
import csv
import re
import os
from datetime import datetime, timedelta
from collections import defaultdict

import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
from frappe.exceptions import DoesNotExistError
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
from frappe.utils.csvutils import read_csv_content
from frappe.utils.file_manager import save_file

from vendor_payments.vendor_payments import constants, queries


class PurchaseInvoiceReport(Document):
    """
    If for a supplier, non default bank account has to be used, then funds team
    have to be update the `Payment Entry` when it's in draft to non-default account
    and also update the downloaded report. This will be tracked and
    hence should be done before `Payment Entry` is submitted
    """

    def __init__(self, *args, **kwargs):
        super(PurchaseInvoiceReport, self).__init__(*args, **kwargs)
        self.reporting_doctype = "Purchase Invoice"
        self.table_name = "`tabPurchase Invoice`"
        self.report_name = "Purchase Invoice Report"
        self.bill_name = "bill_no"
        self.bill_label = "purchase_invoice_id"
        self.company_wise_data = defaultdict(list)  # this initialised as- {<key>: []}

    def update_status(self, status):
        self.db_set("status", status)

    def write_to_file(self, labels, data):
        # Classify the report data based on a row belonging to respective company
        for d in data:
            company = d["company"]
            del d["company"]
            self.company_wise_data[company].append(d)

        # Generate multiple files each for one of the company
        for company in self.company_wise_data.keys():
            filename = f"{constants.COMPANY_ABBR[company]}_purchase_invoice_report_{datetime.now().strftime('%s')}.csv"
            self.file_path = frappe.utils.get_site_path() + "/private/" + filename
            with open(self.file_path, "w") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=labels)
                writer.writeheader()
                writer.writerows(self.company_wise_data[company])

            save_file(
                filename,
                open(self.file_path, "r").read(),
                self.doctype,
                self.name,
                is_private=1,
            )
            # Delete file from local system (pod or node) once uploaded to s3
            os.remove(self.file_path)

    def fetch_bank_mapping(self, entry_name):
        try:
            doc = frappe.get_doc("Invoice Bank Mapping", {"entry_name": entry_name})
            ba_doc = frappe.get_doc("Bank Account", doc.bank_account)
            return {
                "account_no": ba_doc.bank_account_no,
                "ifsc": ba_doc.branch_code,
                "bank_name": ba_doc.bank,
                "bank_record_name": ba_doc.name,
            }
        except DoesNotExistError:
            return None

    def process(self):
        def bank_narration_unique_id(bank_narration):
            # Call recursively till a unique id is finalised which is not in the system
            # This can happen only when even second matches in the mysql regex of DATE_FORMAT(p.creation, "%%m%%d%%s"))
            if frappe.db.exists("Purchase Invoice", {"bank_narration": bank_narration}):
                number_start_index = re.search("\d", bank_narration).start()
                return bank_narration_unique_id(
                    f"{bank_narration[0:number_start_index]}{int(bank_narration[number_start_index:])+1}"[
                        :20
                    ]
                )
            return bank_narration

        res = frappe.db.sql(
            queries.FETCH_INVOICE_DETAILS.format(
                self.table_name,
                constants.AUDITOR_MANAGER_APPROVED,
            ),
            [self.from_date, self.to_date],
            as_dict=True,
        )
        if not res:
            # If no purchase invoices with 'Auditor Manager Approved', then don't let user create a report,
            # since the file generated wont have any data other than column headings
            frappe.throw(
                "Currently there are no invoices to which a report can be generated. Please try later"
            )

        for i, r in enumerate(res):
            self.create_payment_order(r["record_id"])

            # Update with unique bank narration id.
            r["bank_narration"] = bank_narration_unique_id(r["bank_narration"])

            # Store bank narration value in the respective purchase invoice
            frappe.db.sql(
                """
                UPDATE `tabPurchase Invoice` 
                SET bank_narration=%s 
                WHERE name=%s
                """,
                [r["bank_narration"], r["record_id"]],
            )

            mapping = self.fetch_bank_mapping(r["record_id"])
            if mapping:
                # account_no, ifsc, bank_name, bank_record_name
                r.update(mapping)

            # Add bank branch address
            address = frappe.db.sql(
                queries.FETCH_BANK_ADDRESS_DETAILS,
                [r["bank_record_name"]],
            )

            if address:
                # If bank branch address available, add it
                r["bank_branch"] = address[0][0]
            else:
                r["bank_branch"] = r["bank_name"]

            # delete bank record name field in the result
            r.pop("bank_record_name", None)
            r.pop("record_id", None)
            res[i] = r

        # write to file
        self.write_to_file(self.labels, res)

    def purchase_doc_workflow_update(self, status, record_name):
        frappe.db.sql(
            queries.UPDATE_WORKFLOW_STATE.format(self.table_name),
            [status, self.name, record_name],
        )
        frappe.db.commit()

    def create_payment_order(self, name):
        purchase_doc = frappe.get_doc("Purchase Invoice", name)
        doc = get_payment_entry(self.reporting_doctype, name)
        # Should be only in draft
        doc.mode_of_payment = constants.NEFT
        doc.paid_to = f"Creditors - {constants.COMPANY_ABBR[purchase_doc.company]}"
        doc.paid_from = f"Cash - {constants.COMPANY_ABBR[purchase_doc.company]}"
        doc.payment_type = "Pay"
        doc.paid_from_account_currency = "INR"
        doc.paid_to_account_currency = "INR"
        doc.save()

        self.purchase_doc_workflow_update(constants.PAYMENT_IN_PROGRESS, name)
        frappe.db.commit()

    def generate_report(self):
        self.process()
        self.report_generated = 1
        self.update_status("Completed")

    def before_save(self):
        self.labels = (
            ["N", "a", "account_no", "amount", "vendor_name"]
            + ["b", "c", "d", "e", "f", "g", "h", "i"]
            + ["bank_narration"]
            + ["j", "k", "l", "m", "n", "o", "p", "q"]
            + [
                "date",
                "r",
                "ifsc",
                "bank_name",
                "bank_branch",
                "client_email",
            ]
        )

        if not self.report_generated:
            self.update_status("Pending")
            # TODO: uncomment this
            # enqueue(self.generate_report)
            self.generate_report()


def reconciliation(table_name, report_name, fname):
    if getattr(frappe, "uploaded_file", None):
        with open(frappe.uploaded_file, "rb") as upfile:
            fcontent = upfile.read()
    else:
        fcontent = frappe.local.uploaded_file

    form_dict = frappe.local.form_dict
    pr_doc = frappe.get_doc(report_name, form_dict["docname"])
    pr_doc.db_set("status", "Reconciliation Started")

    if frappe.safe_encode(fname).lower().endswith("csv".encode("utf-8")):
        rows = read_csv_content(fcontent, False)
        for row in rows[1:]:
            # Reading from second row, first row will be column names.
            invoice_doc_name = frappe.db.get_value(
                "Purchase Invoice", {"bank_narration": row[1]}, "name"
            )
            # submit payment entry by fetching its name from purchase invoice details
            payment_er = frappe.db.sql(
                queries.FETCH_PAYMENT_ENTRY_DETAILS.format(table_name),
                [invoice_doc_name],  # record_id
                as_dict=True,
            )[0]
            payment_doc = frappe.get_doc(
                "Payment Entry", payment_er["payment_entry_name"]  # purchase_invoice_id
            )
            payment_doc.submit()

            # update purchase invoice status as done.
            frappe.db.sql(
                queries.UPDATE_WORKFLOW_STATE.format(table_name),
                ["Paid", report_name, invoice_doc_name],
            )

    frappe.db.commit()
    save_file(
        fname,
        fcontent,
        report_name,
        form_dict["docname"],
        is_private=1,
    )

    pr_doc.db_set("reconciliation_completed", 1)
    pr_doc.db_set("status", "Reconciliation Done")


@frappe.whitelist()
def reconciliation_process():
    """
    A file will be uploaded by say Accounts team and it will ONLY have records of successful payments
    whose purchase invoice status have to be updated as 'Payment Done'

    A record not in this file, will have its purchase invoice status in its previous state i.e Auditor Approved
    Payments team will fix issues and make sure it is present in future reconciliation file, until then status wont be changed in purchase invoice.

    Multiple reconciliation files can be uploaded, since reports are generated on a company basis
    Also only single reconciliation file also can be uploaded. i.e filename doesn't matter, only bank_narration inside it matters.
    """

    table_name = "`tabPurchase Invoice`"
    report_name = "Purchase Invoice Report"
    # When multiple reconciliation files are uploaded at once, having only seconds in filename will lead to collison
    # So also use values after dot in e.g '2023-05-22 15:20:21.1233' using %f, just to have an unique id
    fname = f"reconciliation_upload_purchase_invoice_{datetime.now().strftime('%s')+datetime.now().strftime('%f')}.csv"
    reconciliation(table_name, report_name, fname)


@frappe.whitelist()
def create_purchase_invoice_report():
    from frappe.utils.data import convert_utc_to_user_timezone
    from frappe.utils.user import get_users_with_role
    from frappe.utils import get_link_to_form

    """
    This should be called from a cron job to create a purchase invoice report for all purchase invoices 
    created the previous day which have workflow state = 'Auditor Manager Approved'
    """
    previous_day = datetime.today() - timedelta(days=1)
    _date = convert_utc_to_user_timezone(previous_day).strftime("%Y-%m-%d")
    res = frappe.db.sql(
        """
    SELECT COUNT(*)
    FROM `tabPurchase Invoice`
    WHERE DATE(modified)=%s
    AND workflow_state='{0}'
    """.format(
            constants.AUDITOR_MANAGER_APPROVED
        ),
        [_date],
    )
    if res[0][0]:
        # Only if there are purchase invoice entries for that date
        doc = frappe.new_doc("Purchase Invoice Report")
        doc.from_date = _date
        doc.to_date = _date
        doc.save()

        frappe.sendmail(
            recipients=get_users_with_role(constants.ACCOUNTS_MANAGER),
            subject=f"Purchase Invoice report is generated for date: {_date}",
            message=f"Purchase Invoice report is generated for date: {_date}. {get_link_to_form('Purchase Invoice', doc.name)}",
        )
        frappe.db.commit()
