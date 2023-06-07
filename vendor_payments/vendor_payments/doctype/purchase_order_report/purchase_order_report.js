// Copyright (c) 2022, zerodha and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Order Report", {
  refresh: function (frm) {
    frm.disable_save();
    if (!frm.is_new()) {
      frm.toggle_display("generate", false);
    }

    var $wrapper = $(frm.fields_dict.reconciliation_file.wrapper).empty();
    new frappe.ui.FileUploader({
      doctype: frm.doctype,
      docname: frm.docname,
      wrapper: $wrapper,
      method:
        "vendor_payments.vendor_payments.doctype.purchase_order_report.purchase_order_report.reconciliation_process",
    });
  },
  generate: function (frm) {
    frm.save();
  },
});
