frappe.ui.form.on("Purchase Invoice", {
  after_save: function (frm) {
    frm.save()
  },
  onload: function (frm) {
    frm.get_field("taxes").grid.cannot_add_rows = true;
    frm.trigger('hide_fields');
  },

  hide_fields: function (frm) {
    if (frm.doc.workflow_state === 'Open' || frm.doc.workflow_state === 'Approver Review Pending') {
      frm.set_df_property("tax_withholding_category", "hidden", 1);
      frm.set_df_property("bank_details", "hidden", 1)
      frm.set_df_property("gst_and_tds_details", "hidden", 1)
      frm.set_df_property("is_tds_not_applicable", "hidden", 1)
      if (frm.doc.workflow_state === 'Open') {
        frm.set_df_property("remarks_section", "hidden", 1)
      }

    }
    if (frm.doc.workflow_state !== 'Account Manager Review Pending') {
      frm.set_df_property("edit_invoice_taxes", "hidden", 1)
    }
    if (!frm.doc.reason_to_edit_purchase_taxes) {
      frm.set_df_property("reason_to_edit_purchase_taxes", "hidden", 1)
    }
  },
  is_tds_not_applicable: function (frm) {
    frm.set_value("tax_withholding_category", '');
  },
  edit_invoice_taxes: function (frm) {
    let value = ''
    if (frm.doc.edit_invoice_taxes) {
      frm.set_df_property("reason_to_edit_purchase_taxes", "hidden", 0)
      frm.set_df_property("reason_to_edit_purchase_taxes", "reqd", 1)

      value = 'Actual'
    } else {
      frm.set_df_property("reason_to_edit_purchase_taxes", "hidden", 1)
      frm.set_df_property("reason_to_edit_purchase_taxes", "reqd", 0)

      value = 'On Net Total'
    }
    for (let i = 0; i < frm.doc.taxes.length; i++) {
      frm.get_field("taxes").grid.grid_rows[i].doc.charge_type = value
    }
  },

  supplier: function (frm) {
    // Fetch default approver for the selected supplier
    if (frm.doc.supplier) {
      frappe.call({
        method: "vendor_payments.vendor_payments.hooks.supplier.fetch_default_approver",
        args: {
          "supplier": frm.doc.supplier
        },
        callback: function (r) {
          if ("message" in r) {
            frm.set_value("invoice_approver", r.message["approver"]);
          }
        },
      });
    }
  },

  onload_post_render: function (frm) {
    frm.trigger('hide_fields')

    frm.set_query("supplier", function () {
      return {
        filters: {
          workflow_state: "Approved",
        },
      };
    });
    if (frm.is_new() || frm.doc.workflow_state === 'Open') {
      // Fetch all approvers
      frm.set_query("invoice_approver", function () {
        return {
          query: "vendor_payments.vendor_payments.hooks.supplier.fetch_approvers",
          filters: { "name": frm.doc.supplier }
        }
      })
    }
    else {
      frm.set_df_property("invoice_approver", "hidden", 1)
    }
  },

  refresh: function (frm) {
    frm.trigger('hide_fields')
    if (frm.doc.workflow_state === 'Account Manager Review Pending' && Boolean(frappe.user_roles.includes("Accounts Manager"))) {
      frm.set_df_property("apply_tds", "read_only", 1);
      frm.set_value('apply_tds', 1);

      frm.set_query("bank_id", () => {
        return {
          filters: {
            party: frm.doc.supplier,
          },
        };
      });

      if (!frm.doc.bank_account) {
        // Fetch bank details only during 'Account Manager Review Pending' stage.
        // Once Account manager approves, it should never be changed again
        frappe.call({
          method: "vendor_payments.vendor_payments.hooks.purchase_invoice.fetch_bank_account_details",
          args: {
            "supplier": frm.doc.supplier
          },
          callback: function (r) {
            if ("message" in r) {
              frm.set_value("bank_id", r.message["bank_id"]);
            }
          },
        });
      }


    }
    // frm.get_field("taxes").grid.cannot_add_rows = true;

    if (frm.is_new()) {
      frm.get_field("items").grid.grid_rows[0]?.remove();
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

    if (frappe.user_roles.includes("Accounts Manager") && frm.doc.workflow_state === 'Paid') {
      // This section should be visible only to Account manager team after paid status
      frm.toggle_display(
        "post_payment",
        1
      );
    }
  },
});


frappe.ui.form.on("Purchase Taxes and Charges", {
  form_render: function (frm) {
    const grids = [
      ".grid-delete-row",
      ".grid-insert-row-below",
      ".grid-insert-row",
      ".grid-move-row",
      ".grid-duplicate-row",
      ".grid-append-row",
      ".grid-row-check",
      ".grid-remove-rows",
    ];
    for (let i = 0; i < grids.length; i++) {
      frm.get_field("taxes").grid.wrapper.find(grids[i]).hide();
    }
  },
});
