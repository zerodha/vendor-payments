frappe.ui.form.on("Purchase Order", {
  onload_post_render: function (frm) {
    frm.set_query("supplier", function () {
      return {
        filters: {
          workflow_state: "Approved",
        },
      };
    });
  },
  refresh: function (frm) {
    if (frm.is_new()) {
      frm.get_field("items").grid.grid_rows[0].remove();
    }
    var buttons = [
      "Purchase Receipt",
      "Block Invoice",
      "Payment",
      "Return / Debit Note",
      "Subscription",
      "Payment Request",
    ];
    if (!frappe.user_roles.includes("Funds")) {
      // Not funds team
      for (var i in buttons) {
        frm.remove_custom_button(i, "Create");
      }
    } else {
      // funds team
      if (frm.doc.workflow_state == "Rejected") {
        for (var i in buttons) {
          frm.remove_custom_button(i, "Create");
        }
      }
    }
  },
});

// frappe.ui.form.on("Purchase Invoice Item", {
//   items_add(frm, cdt, cdn) {
//   },
//   form_render(frm, cdt, cdn) {
//   },
// });
