import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry


class CustomPaymentEntry(PaymentEntry):
    def _validate(self):
        return

    def validate(self):
        pass

    def on_submit(self):
        pass
