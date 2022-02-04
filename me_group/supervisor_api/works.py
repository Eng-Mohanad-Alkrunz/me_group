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
def create_work(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")

    frappe.local.lang = lang
    data = kwards

    check = check_token()
    user1 = None
    work_name = None
    contract = None
    date = None
    if check and "user" in check:
        user1 = check['user']

    if not user1:
        frappe.local.response['http_status_code'] = 403
        frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return


    if "work_name" in data:
        work_name = data['work_name']
    else:
        frappe.local.response['status'] = {"message": _("Work name required"), "success": False, "code": 403}
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

    new_work = frappe.new_doc("Work Application")
    new_work.set("work_name",work_name)
    new_work.set("supervisor", user1.name)
    if date is not None:
        new_work.set("date", date)
    new_work.set("contract", contract)
    new_work.set("images", updatefile(data))
    new_work.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.local.response['status'] = {"message": _("Work created successfully"), "success": True, "code": 200}
    frappe.local.response['data'] = None


@frappe.whitelist(allow_guest=True)
def create_work_management(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")

    frappe.local.lang = lang
    data = kwards

    check = check_token()
    user1 = None
    contract = None
    date = None
    work_name = None
    if check and "user" in check:
        user1 = check['user']

    if not user1:
        frappe.local.response['http_status_code'] = 403
        frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return

    work_name = data['work_name']
    if "contract" in data:
        contract = data['contract']
    else:
        frappe.local.response['status'] = {"message": _("contract id required"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return

    if "date" in data:
        date = data['date']

    email = data['email']
    new_work = frappe.new_doc("Work Management Application")
    work = frappe.get_all("Work Application",filters={"work_name":work_name})
    if len(work) == 1 :
        new_work.set("work", work[0].name)
    new_work.set("supervisor", user1.name)
    if date is not None:
        new_work.set("date", date)
    new_work.set("contract", contract)
    new_work.set("email", email)
    new_work.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.local.response['status'] = {"message": _("Work created successfully"), "success": True, "code": 200}
    frappe.local.response['data'] = None


@frappe.whitelist(allow_guest=True)
def get_management_works(**kwards):
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
    works = frappe.get_all("Work Management Application",fields =["*"],filters= {"supervisor":user1.name})
    for work in works:
        work_doc = frappe.get_doc("Work Management Application",work.name)
        result.append({
            "id":work.name,
            "contract":work.contract,
            "date":work.date,
            "customer" :work.customer,
            "work": work.work,
            "email": work.email,
        })


    frappe.local.response['status'] = {"message": _("Works list "), "success": True, "code": 200}
    frappe.local.response['data'] = result



@frappe.whitelist(allow_guest=True)
def get_works(**kwards):
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
    works = frappe.get_all("Work Application",fields =["*"],filters= {"contract":contract})
    for work in works:
        work_doc = frappe.get_doc("Work Application",work.name)
        images = []
        if work_doc.images is not None:
            for image in work_doc.images:
                images.append({
                    "image" : image.images
                })
        result.append({
            "id":work.name,
            "contract":work.contract,
            "date":work.date,
            "status" :_(work.status),
            "images" : images
        })


    frappe.local.response['status'] = {"message": _("Works list "), "success": True, "code": 200}
    frappe.local.response['data'] = result


@frappe.whitelist(allow_guest=True)
def get_done_works(**kwards):
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

    contract_doc = frappe.get_doc("Contract Application",contract)
    if contract_doc.contract_status == "end of the contract":

        result = []
        works = frappe.get_all("Work Application",fields =["*"],filters= {"contract":contract})
        for work in works :
            images = []
            for image in work.images:
                images.append({
                    "image" : image.images
                })
            result.append({
                "id":work.name,
                "contract":work.contract,
                "date":work.date,
                "status" :_(work.status),
                "images" : images
            })


        frappe.local.response['status'] = {"message": _("Work created successfully"), "success": True, "code": 200}
        frappe.local.response['data'] = result
    else :
        frappe.local.response['status'] = {"message": _("Contract Not completed yet "), "success": True, "code": 200}
        frappe.local.response['data'] = None

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
def updatefile(data):
    gallery =[]
    user = frappe.get_doc("User", frappe.session.user)
    i = 0
    for i in range(len(frappe.request.files)):

        file = frappe.request.files['image['+str(i)+']']

        is_private = 0
        fieldname = ""
        folder = 'Home'
        filename = ""
        content = None

        content = file.stream.read()
        filename = file.filename
        content_type = guess_type(filename)[0]
        frappe.local.uploaded_file = content
        frappe.local.uploaded_filename = filename
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

        gallery.append({
            'images':ret.file_url,
        })

    return gallery