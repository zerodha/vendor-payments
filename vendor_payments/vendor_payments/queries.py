UPDATE_WORKFLOW_STATE = """
    UPDATE {0}
    SET workflow_state=%s, modified=NOW(), invoice_report_name=%s
    WHERE name=%s
"""

FETCH_BANK_ADDRESS_DETAILS = """
    SELECT ad.address_title
    FROM tabAddress ad
    JOIN `tabDynamic Link` dl
    ON dl.parent=ad.name
    WHERE dl.link_name=%s;
"""

FETCH_INVOICE_DETAILS = """
    SELECT p.name AS record_id, "N", null as 'a', p.bank_account AS account_no, p.company_ AS company,
    p.grand_total AS amount, IF(LENGTH(s.supplier_name)>30, SUBSTRING_INDEX(s.supplier_name, ' ', 2), s.supplier_name) AS vendor_name, 
    null as 'b', null as 'c', null as 'd', null as 'e', null as 'f', null as 'g', null as 'h', null as 'i',
    CONCAT(SUBSTRING(s.supplier_name, 1, 14), DATE_FORMAT(p.creation, "%%m%%d%%s")) AS bank_narration,
    null as 'j', null as 'k', null as 'l', null as 'm', null as 'n', null as 'o', null as 'p', null as 'q',
    DATE_FORMAT(DATE(p.modified), '%%d/%%m/%%Y') AS date, null as "r", p.ifsc AS ifsc, p.bank_name AS bank_name,
    '' AS bank_branch, 'accountsteam@zerodha.com' AS client_email,
    ba.name AS bank_record_name
    FROM {0} p
    JOIN `tabSupplier` s
    ON s.name = p.supplier
    JOIN `tabBank Account` ba
    ON ba.name = p.bank_id
    WHERE DATE(p.creation) BETWEEN  %s AND %s
    AND p.workflow_state='{1}'
;
"""

FETCH_PAYMENT_ENTRY_DETAILS = """
    SELECT per.parent as payment_entry_name
    FROM {0} p
    JOIN `tabPayment Entry Reference` per ON p.name = per.reference_name
    WHERE p.name=%s
"""

FETCH_BANK_ACCOUNT_DETAILS = """
    SELECT name
    FROM `tabBank Account`
    WHERE is_default=1 AND party=%s
"""

FETCH_INVOICE_DETAILS_FOR_REMINDER = """
    SELECT name, owner, workflow_state, 'Purchase Invoice' AS type, supplier, modified, reminder_sent
    FROM `tabPurchase Invoice`
    WHERE workflow_state NOT IN ('{0}', '{1}', '{2}')

    UNION ALL

    SELECT name, owner, workflow_state, 'Purchase Order' AS type, supplier, modified, reminder_sent
    FROM `tabPurchase Order`
    WHERE workflow_state NOT IN ('{0}', '{1}', '{2}')
    ;
"""

UPDATE_REMINDER_SENT = """
    UPDATE {0}
    SET reminder_sent=%s
    WHERE name=%s
"""
