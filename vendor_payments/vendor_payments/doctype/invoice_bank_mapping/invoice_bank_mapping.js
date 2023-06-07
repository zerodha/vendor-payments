// Copyright (c) 2022, zerodha and contributors
// For license information, please see license.txt

frappe.ui.form.on("Invoice Bank Mapping", {
  refresh: function (frm) {
    frm.set_query("entry_name", () => {
      return {
        filters: {
          workflow_state: ["not in", ["Payment In Progress", "Payment Done"]],
        },
      };
    });
  },
});
