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
def create_invoice(**kwards):
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


    if "invoice_name" in data:
        invoice_name = data['invoice_name']
    else:
        frappe.local.response['status'] = {"message": _("Invoice name required"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return

    if "contract" in data:
        contract = data['contract']
    else:
        frappe.local.response['status'] = {"message": _("contract id required"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return

    if "date" in data:
        date = data['date']

    new_invoice = frappe.new_doc("Invoice Application")
    new_invoice.set("invoice_name",invoice_name)
    new_invoice.set("supervisor", user1.name)
    new_invoice.set("contract", contract)
    if date is not None:
        new_invoice.set("date", date)
    res = uploadfile()
    new_invoice.set("image", res.file_url)
    new_invoice.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.local.response['status'] = {"message": _("Invoice created successfully"), "success": True, "code": 200}
    frappe.local.response['data'] = None


@frappe.whitelist(allow_guest=True)
def get_invoices(**kwards):
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

    if "contract" in data:
        contract = data['contract']
    else:
        frappe.local.response['status'] = {"message": _("contract id required"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return

    result = []
    invoices = frappe.get_all("Invoice Application",fields =["*"],filters= {"contract":contract})
    for invoice in invoices:
        invoice_doc = frappe.get_doc("Invoice Application",invoice.name)
        status = _("Pending")
        if invoice_doc.docstatus == 1:
            status = _("Submitted")
        else:
            status = _("Pending")
        result.append({
            "id":invoice_doc.name,
            "contract":invoice_doc.contract,
            "date":invoice_doc.date,
            "status" :status,
            "image" : invoice_doc.image
        })


    frappe.local.response['status'] = {"message": _("Invoices list"), "success": True, "code": 200}
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

@frappe.whitelist(allow_guest=True)
def uploadfile():
    user = frappe.get_doc("User", frappe.session.user)

    file = frappe.request.files['image']
    is_private = 0
    fieldname = ""
    folder = 'Home'
    filename = ""
    content = None

    if file:
        content = file.stream.read()
        filename = file.filename
        content_type = guess_type(filename)[0]
    frappe.local.uploaded_file = content
    frappe.local.uploaded_filename = filename


    # print(frappe.db.sql(f"""INSERT into `tabFile` (folder,file_name,is_private,content)
    #                 Values = ('{folder}' , '{filename}' , '{cint(is_private)}' , '{content}' )"""))

    ret = frappe.get_doc({
        "doctype": "File",
        "attached_to_doctype": "",
        "attached_to_name": "",
        "attached_to_field": "",
        "folder": folder,
        "file_name": filename,
        "file_url": "",
        "is_private": cint(is_private),
        "content": content
    })

    ret.save(ignore_permissions=True)
    return ret