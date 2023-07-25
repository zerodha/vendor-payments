frappe.ui.form.on("Tax Withholding Category", {
    onload_post_render: function (frm) {
        // frm.get_field("accounts").grid.cannot_add_rows = true;
        if (frm.is_new()) {

            let companies = {
                "Zerodha Technology Pvt Ltd": "Zt",
                "Zerodha Broking Limited": "ZBL",
                "Zerodha": "Zer",
                "Zerodha Capital": "ZCap",
                "Zerodha Commodities": "ZCom",
                "Zerodha Securities": "ZSec",
                "Rainmatter Foundation": "RF",
            }
            let count = 0
            frm.fields_dict.accounts.grid.remove_all();
            for (const [key, value] of Object.entries(companies)) {
                let child = frm.add_child("accounts");
                child.company = key
                child.account = `TDS - ${value}`
                // frm.refresh('accounts');
            }
        }
    }
});