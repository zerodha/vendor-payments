"""Custom google login flow"""
import frappe
import json
from frappe.utils.oauth import login_via_oauth2


def decoder_compat(b):
    # https://github.com/litl/rauth/issues/145#issuecomment-31199471
    return json.loads(bytes(b).decode("utf-8"))


@frappe.whitelist(allow_guest=True)
def login_via_google(code, state):
    """
    Step1: Choose custom provider in social login page
    Step2: Give provider name as 'Google audit team
    Step3: Give this login_via_google api endpoint address in redirect url field
    i.e redirect url will be '<base_url>/api/method/vendor_payments.api.login.login_via_google'
    """
    login_via_oauth2(
        "replace_this_with_name_from_ui", code, state, decoder=decoder_compat
    )
