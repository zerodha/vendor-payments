import csv
from random import randint

import frappe
from frappe.model.naming import make_autoname

from vendor_payments.vendor_payments import constants, queries


def import_vendor_list():
    filename = "/tmp/vendor_list.csv"
    # Vendor Name,Bank,Bank Account Number,IFSC Code,PAN,GST Number,Approver Email id,From which company
    with open(filename, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)
        for row in csvreader:
            if row[0] in ["Vendor Name", None, ""]:
                continue
            supplier_doc = frappe.get_doc(
                "Supplier",
                {"supplier_name": row[0], "from_company": ""},
            )
            if row[2] in []:
                continue

            bank_account_doc = frappe.get_doc(
                "Bank Account", {"bank_account_no": row[2]}
            )

            bank_account_doc.party_type = "Supplier"
            bank_account_doc.party = supplier_doc.name

            if frappe.db.sql(
                queries.FETCH_BANK_ACCOUNT_DETAILS,
                [supplier_doc.name],
            ):
                # If default account already assigned for a party then dont mark as is_default
                pass
            else:
                bank_account_doc.is_default = 1
            try:
                bank_account_doc.save()
            except Exception as e:
                pass

            # frappe.db.commit()


COMPANY_ABBR = {
    c.get("name"): c.get("abbr")
    for c in frappe.get_list("Company", fields=["name", "abbr"])
}


def _update_supplier_name_field(from_company):
    return make_autoname(f"{COMPANY_ABBR[from_company].upper()}_SUPL_")


def update_name_field():
    items = frappe.db.get_list("Supplier", fields=["name", "from_company"])
    for item in items:
        frappe.db.sql(
            """
        UPDATE `tabSupplier`
        SET name=%s
        WHERE name=%s
        """,
            [_update_supplier_name_field(item["from_company"]), item["name"]],
        )


def prepend_00_bank_account():
    filename = "/tmp/vendors.csv"
    # Vendor Name,Bank,Bank Account Number,IFSC Code,PAN,GST Number,Approver Email id,From which company
    with open(filename, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)

        for row in csvreader:
            if row[0] in ["Vendor Name", None, ""]:
                continue

            if row[2][0:2] == "00":
                records = frappe.db.sql(
                    """
                SELECT name
                FROM `tabBank Account`
                WHERE bank_account_no=%s
                """,
                    [row[2][2:]],
                )
                if not records:
                    continue
                for rec in records:
                    frappe.db.sql(
                        """
                    UPDATE `tabBank Account`
                    SET bank_account_no=%s
                    WHERE name=%s
                    """,
                        [row[2], rec[0]],
                    )
                frappe.db.commit()


def fix_supplier_mapping_with_bank():
    import itertools

    COMPANY_ABBR = {
        c.get("name"): c.get("abbr")
        for c in frappe.get_list("Company", fields=["name", "abbr"])
    }

    filename = "/tmp/vendorss.xlsx"
    # filename = "/Users/nikhilponnuru/Downloads/vendorss.xlsx"
    data = []
    # Vendor Name,Bank,Bank Account Number,IFSC Code,PAN,GST Number,Approver Email id,From which company
    import pandas as pd

    # NOTE: Use excel sheets and hence pandas because csv file trims away leading 00s
    df = pd.read_excel(
        filename, "Total Vendor list", engine="openpyxl", na_filter=False
    )
    # df.replace("nan", "")
    data = df.values.tolist()

    def keyfunc(value):
        return (value[0].replace("\xa0", " "), value[2], value[7])

    for key, group in itertools.groupby(sorted(data, key=lambda x: x[0]), key=keyfunc):
        if key[0] in ["", "Vendor Name"]:
            continue
        try:
            supplier_doc = frappe.get_doc(
                "Supplier", {"supplier_name": key[0], "from_company": key[2]}
            )
        except Exception as e:
            continue

        count = 0
        for g in list(group):
            count += 1
            bank_doc = frappe.new_doc("Bank Account")
            bank_doc.account_name = f"{g[0].lower().replace(' ', '_')}_{supplier_doc.name}"  # vendorname_bank_name
            bank_doc.bank = g[1]
            bank_doc.party_type = "Supplier"
            bank_doc.party = supplier_doc.name
            bank_doc.branch_code = g[3]
            bank_doc.bank_account_no = str(g[2])
            if count == 1:
                bank_doc.is_default = 1

            bank_doc.save()

    frappe.db.commit()
