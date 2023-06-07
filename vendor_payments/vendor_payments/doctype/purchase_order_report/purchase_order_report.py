# Copyright (c) 2022, zerodha and contributors
# For license information, please see license.txt
from datetime import datetime

import frappe
from frappe.model.document import Document
from vendor_payments.vendor_payments.doctype.purchase_invoice_report.purchase_invoice_report import (
    PurchaseInvoiceReport,
    reconciliation,
)


class PurchaseOrderReport(PurchaseInvoiceReport):
    def __init__(self, *args, **kwargs):
        super(PurchaseOrderReport, self).__init__(*args, **kwargs)
        self.reporting_doctype = "Purchase Order"
        self.table_name = "`tabPurchase Order`"
        self.report_name = "Purchase Order Report"
        self.filename = f"purchase_order_report_{datetime.now().strftime('%s')}.csv"
        self.bill_name = "order_confirmation_no"
        self.bill_label = "purchase_order_id"

    def before_save(self):
        super(PurchaseOrderReport, self).before_save()


@frappe.whitelist()
def reconciliation_process():
    table_name = "`tabPurchase Order`"
    report_name = "Purchase Order Report"
    fname = f"reconciliation_upload_purchase_order_{datetime.now().strftime('%s')}.csv"
    reconciliation(table_name, report_name, fname)
