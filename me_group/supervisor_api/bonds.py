from __future__ import unicode_literals

import time

import frappe
import frappe.client
import frappe.handler
import jwt
from frappe import _
import base64
from passlib.context import CryptContext
from mimetypes import guess_type
from frappe.utils import add_days, cint

@frappe.whitelist(allow_guest=True)
def create_bound(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")

    frappe.local.lang = lang
    data = kwards

    check = check_token()
    user1 = None
    invoice_name = None
    contract = None
    date = None
    if check and "user" in check:
        user1 = check['user']

    if not user1:
        frappe.local.response['http_status_code'] = 403
        frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return

    if "contract" in data:
        contract = data['contract']
    else:
        frappe.local.response['status'] = {"message": _("contract id required"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return
    id_no = None
    if "id_no" in data:
        id_no = data['id_no']

    if "date" in data:
        date = data['date']

    amount = 0
    if "amount" in data:
        amount = data['amount']

    reason = ""
    if 'reason' in data:
        reason = data['reason']
    try:
        new_bond = frappe.new_doc("Bond Application")
        new_bond.set("supervisor", user1.name)
        new_bond.set("contract", contract)
        new_bond.set("id_no", id_no)
        new_bond.set("amount", amount)
        new_bond.set("reason", reason)
        if date is not None:
            new_bond.set("date", date)
        new_bond.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.local.response['status'] = {"message": _("Bound created successfully"), "success": True, "code": 200}
        frappe.local.response['data'] = None
    except:
        frappe.local.response['status'] = {"message": _("Failed to create Bound"), "success": True, "code": 200}
        frappe.local.response['data'] = None


@frappe.whitelist(allow_guest=True)
def get_bonds(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")

    frappe.local.lang = lang
    data = kwards

    check = check_token()
    user1 = None
    contract = None
    if check and "user" in check:
        user1 = check['user']

    if not user1:
        frappe.local.response['http_status_code'] = 403
        frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return

    result = []
    bonds = frappe.get_all("Bond Application",fields =["*"],filters= {"supervisor":user1.name})
    for bond in bonds:
        result.append({
            "id":bond.name,
            "contract":bond.contract,
            "date":bond.date,
            "status" :_(bond.status),
            "amount" : bond.amount,
            "reason" :bond.reason
        })


    frappe.local.response['status'] = {"message": _("Bonds list"), "success": True, "code": 200}
    frappe.local.response['data'] = result

@frappe.whitelist(allow_guest=True)
def check_token():
    request = frappe.request
    secret_key = "Me System"
    frappe.local.lang = "ar"
    log = frappe.get_doc({"doctype": "Api Log"})
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang

    if frappe.get_request_header("Authorization"):
        authorization_header = frappe.get_request_header("Authorization").split(" ")
        if authorization_header[0] != "Bearer" and len(authorization_header) != 2:
            log.response = _("Not Authorized")
            log.flags.ignore_permissions = True
            log.insert()
            frappe.db.commit()
            frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
            frappe.local.response['data'] = None
            return
        token = frappe.get_request_header("Authorization").replace('Bearer ', '')
        log.token = token

        user_devices = frappe.get_all("User Device", ['name'],
                                         filters={"access_token": token, "docstatus": ['<', 2]})
        if not user_devices:
            frappe.local.response['http_status_code'] = 403
            log.response = _("Not Authorized")
            log.flags.ignore_permissions = True
            log.insert()
            frappe.db.commit();
            frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
            frappe.local.response['data'] = None
            return
        try:
            token = jwt.decode(token, secret_key, algorithms="HS256")
        except Exception:
            frappe.local.response['http_status_code'] = 401
            log.response = _("Not Authorized")
            log.flags.ignore_permissions = True
            log.insert()
            frappe.db.commit();
            frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
            frappe.local.response['data'] = None
            return
        user_device = frappe.get_doc("User Device", user_devices[0].name)
        if not user_device.user:
            frappe.local.response['http_status_code'] = 403
            log.response = _("Not Authorized")
            log.flags.ignore_permissions = True
            log.insert()
            frappe.db.commit()
            frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
            frappe.local.response['data'] = None
            return

        supervisor = frappe.get_doc("Supervisor", user_device.user)
        log.response = "success login"
        log.flags.ignore_permissions = True
        log.insert()
        frappe.db.commit()
        return {"user": supervisor}
    else:
        frappe.local.response['http_status_code'] = 403
        log.response = _("Not Authorized")
        log.flags.ignore_permissions = True
        log.insert()
        frappe.db.commit()
        frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return
