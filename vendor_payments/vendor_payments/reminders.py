from datetime import datetime

import frappe
from frappe.utils.user import get_users_with_role
from frappe.utils import get_link_to_form

from vendor_payments.vendor_payments import queries
from vendor_payments.vendor_payments import constants


@frappe.whitelist()
def payments_reminder():
    """
    This should be run as a cron job, everyday.
    command: `bench execute vendor_payments.vendor_payments.reminders.payments_reminder`

    Send reminders after 2 days to respective persons
    """
    res = frappe.db.sql(
        queries.FETCH_INVOICE_DETAILS_FOR_REMINDER.format(
            constants.OPEN, constants.PAYMENT_IN_PROGRESS, constants.PAYMENT_DONE
        ),
        as_dict=True,
    )
    for r in res:
        # is modified >2 days (in seconds =172800)
        if (datetime.now() - r["modified"]).total_seconds() > 172800:
            # reminder_sent format is - '<workflow_state>'
            if r["reminder_sent"] == r["workflow_state"]:
                # If a reminder was already sent for current workflow state, then don't send again.
                continue
        else:
            # If less than 2 days.
            continue

        recipients = []
        subject = f"Reminder: Please take a look at purchase order {r['name']} and take necessary action"
        message = f"""
            Reminder: Please take a look at purchase order {r['name']} 
            and take necessary action. {frappe.utils.get_link_to_form(r['type'], r['name'])}
        """
        if r["workflow_state"] == constants.APPROVER_REVIEW_PENDING:
            recipients = [frappe.db.get_value("Supplier", r["supplier"], "approver")]

        elif r["workflow_state"] == constants.AUDITOR_REVIEW_PENDING:
            recipients = get_users_with_role(constants.AUDITOR)

        elif r["workflow_state"] == constants.AUDITOR_MANAGER_REVIEW_PENDING:
            recipients = get_users_with_role(constants.AUDITOR_MANAGER)

        elif r["workflow_state"] == constants.AUDITOR_MANAGER_APPROVED:
            recipients = get_users_with_role(constants.PAYOUT)

        elif r["workflow_state"] == constants.PAYMENT_IN_PROGRESS:
            recipients = get_users_with_role(constants.ACCOUNTS_MANAGER)

        if recipients:
            frappe.sendmail(
                recipients=recipients,
                subject=subject,
                message=message,
                send_priority=10,
            )

            # set reminder_sent with a <workflow state> name that it was sent at.
            # use plain sql update like this instead of doc orm so that modified time is not disturbed.
            # since reminders depend on modified time, its important its only modified because of workflow states
            frappe.db.sql(
                queries.UPDATE_REMINDER_SENT.format("`tab" + r["type"] + "`"),
                [r["workflow_state"], r["name"]],
                as_dict=True,
            )


def notify(doc, method):
    """
    Send emails in this flow
    Approver -> Email Receiver:
        user -> approver
        approver -> auditor

    Rejected -> Email Receiver:
        auditor -> account managers and user
        approver -> user
    """

    recipients = []
    subject = message = None

    if doc.workflow_state == constants.APPROVER_REVIEW_PENDING:
        if not frappe.db.exists(
            "File",
            {"attached_to_doctype": doc.doctype, "attached_to_name": doc.name},
        ):
            frappe.throw("Please attach invoice file before sending for approval.")

        # if not doc.tax_withholding_category:
        #     frappe.throw("Tax withholding category is must before sending for approval")

        frappe.share.add(
            doc.doctype,
            doc.name,
            doc.invoice_approver,
            submit=1,
            flags={"ignore_share_permission": True},
        )
        recipients = [doc.invoice_approver]
        subject = (
            f"A purchase invoice raised by {doc.owner} needs your approval: {doc.name}"
        )
        message = f"A purchase invoice raised by {doc.owner} needs your approval: {get_link_to_form('Purchase Invoice', doc.name)}"

    elif doc.workflow_state == constants.APPROVER_REJECTED:
        recipients = [doc.owner]
        subject = f"Purchase invoice {doc.name} is rejected."
        message = f"Your purchase invoice is rejected by invoice approver."

    elif doc.workflow_state == constants.ACCOUNT_MANAGER_REVIEW_PENDING:
        recipients = get_users_with_role(constants.ACCOUNTS_MANAGER)
        subject = f"Purchase invoice {doc.name} is approved. Need account manager verification"
        message = f"A purchase invoice raised by {doc.owner} is approved by approver. Now needs Account Manager verification. {get_link_to_form('Purchase Invoice', doc.name)}"

    elif doc.workflow_state == constants.ACCOUNT_MANAGER_REJECTED:
        recipients = [doc.owner]
        subject = f"Purchase invoice {doc.name} is rejected."
        message = f"Your purchase invoice is rejected by account manager."

    elif doc.workflow_state == constants.AUDITOR_REVIEW_PENDING:
        auditor_reminder_doc = frappe.get_doc(
            "Invoice Auditor Notifications", {"company": doc.company_}
        )
        recipients = [u.user for u in auditor_reminder_doc.user]
        subject = f"{auditor_reminder_doc.company_abbr}_Payout File_{doc.posting_date}"
        message = f"{auditor_reminder_doc.company_abbr}_Payout File_{doc.posting_date}"

    elif doc.workflow_state == constants.AUDITOR_MANAGER_REJECTED:
        auditor_reminder_doc = frappe.get_doc(
            "Invoice Auditor Notifications", {"company": doc.company_}
        )
        recipients = [u.user for u in auditor_reminder_doc.user]
        subject = f"Auditor Manager Rejected: {doc.name}"
        message = f"""
            Auditor Manager Rejected this invoice {doc.name}
            {get_link_to_form('Purchase Invoice', doc.name)}
        """

    elif doc.workflow_state == constants.AUDITOR_MANAGER_REVIEW_PENDING:
        pass
        # recipients = get_users_with_role(constants.AUDITOR_MANAGER)
        # subject = f"A purchase invoice {doc.name} is auditor approved. Need auditor manager approval"
        # message = f"A purchase invoice raised by {doc.owner} is approved by auditor. Now needs Auditor Manager approval. {get_link_to_form('Purchase Invoice', doc.name)}"

    elif doc.workflow_state == constants.AUDITOR_REJECTED:
        # Get all account manager role users
        supplier_approver = frappe.db.get_value("Supplier", doc.supplier, "approver")
        recipients = list(
            set(
                [doc.owner, supplier_approver]
                + get_users_with_role(constants.ACCOUNTS_MANAGER)
            )
        )
        subject = f"Audior rejected purchase invoice: {doc.name}"
        message = f"A purchase invoice {doc.name} is rejected by auditor. Check remarks to know the reason. {get_link_to_form('Purchase Invoice', doc.name)}"

    elif doc.workflow_state == constants.PAYMENT_DONE:
        recipients = [doc.owner]
        subject = f"Purchase invoice {doc.name} is paid"
        message = f"A purchase invoice raised by you is paid. {get_link_to_form('Purchase Invoice', doc.name)}"

    if recipients:
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            send_priority=10,  # As high as possible
            now=True,  # Send immediately
        )
