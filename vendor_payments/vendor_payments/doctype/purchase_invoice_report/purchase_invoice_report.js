// Copyright (c) 2022, zerodha and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Invoice Report", {
  refresh: function (frm) {
    frm.disable_save();
    if (!frm.is_new()) {
      frm.toggle_display("generate", false);
    }

    var $wrapper = $(frm.fields_dict.reconciliation_file.wrapper).empty();
    new frappe.ui.FileUploader({
      multiple: true,
      doctype: frm.doctype,
      docname: frm.docname,
      wrapper: $wrapper,
      method:
        "vendor_payments.vendor_payments.doctype.purchase_invoice_report.purchase_invoice_report.reconciliation_process",
    });

    // Only accounts team should be able to upload reconciliation file
    // This field will always be open to let any number of reconciliation files to be uploaded
    // for this particular from and to date. Since sometimes a single reconciliation file maynot have
    // all purchase invoice records at once.
    frm.toggle_display(
      "reconciliation_section",
      Boolean(frappe.user_roles.includes("Accounts Manager")) &&
      frm.doc.report_generated
    );
  },
  generate: function (frm) {
    frm.save();
  },
});
