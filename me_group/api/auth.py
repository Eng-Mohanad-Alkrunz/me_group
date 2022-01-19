from __future__ import unicode_literals

import time

import frappe
import frappe.client
import frappe.handler
import jwt
from frappe import _
from passlib.context import CryptContext


@frappe.whitelist(allow_guest=True)
def register(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang
    data = kwards


    if 'udid' not in data:
        frappe.local.response['status'] = {"message": _("Incorrect credentials"), "success": False, "code": 422}
        frappe.local.response['data'] = None
        return

    mobile = data['mobile_number']
    udid = data['udid']
    fcm = None
    email = None
    full_name = None
    city = None
    password = None

    if 'email' in data:
        email = data['email']
    else:
        frappe.local.response['status'] = {
            "message": _("Email required"),
            "code": 1,
            "success": False
        }
        frappe.local.response['data'] = None

    if 'password' in data:
        password = data['password']
    else:
        frappe.local.response['status'] = {
            "message": _("Password required"),
            "code": 1,
            "success": False
        }
        frappe.local.response['data'] = None

    if 'udid' in data:
        udid = data['udid']
    else:
        frappe.local.response['status'] = {
            "message": _("Device Id required"),
            "code": 1,
            "success": False
        }
        frappe.local.response['data'] = None

    if 'full_name' in data:
        full_name = data['full_name']
    else:
        frappe.local.response['status'] = {
            "message": _("Full name required"),
            "code": 1,
            "success": False
        }
        frappe.local.response['data'] = None
    if 'fcm' in data:
        fcm = data['fcm']
    if 'city' in data:
        city = data['city']

    if 'gender' in data:
        gender = data['gender']

    log = frappe.get_doc({"doctype": "Api Log"})

    if (len(frappe.get_all('Customer', ['email'], filters={"email": email, "mobile_number": mobile})) > 0):
        frappe.local.response['status'] = {"message": _("This user is already exist"), "success": False, "code": 422}
        frappe.local.response['data'] = None
        return
    passlibctx = CryptContext(
        schemes=[
            "pbkdf2_sha256",
            "argon2",
            "frappe_legacy",
        ],
        deprecated=[
            "frappe_legacy",
        ],
    )
    hashPwd = passlibctx.hash(password)

    customer_doc = frappe.get_doc({"doctype": "Customer",
                                   "mobile_number": mobile,
                                   "email": email,
                                   "customer_name": full_name,
                                   "password":hashPwd,
                                   "city":city,
                                   "customer_type":"Individual",
                                   "gender":gender
                                   }).save(ignore_permissions=True)
    frappe.db.commit()
    cus_list = frappe.get_all("Customer", ['name'], filters={"mobile_number": mobile, "email": email})
    name = cus_list[0].name
    secret_key = "Me System";
    issuedat_claim = time.time();
    notbefore_claim = issuedat_claim;
    expire_claim = issuedat_claim + (60 * 60 * 3 * 24 * 5);
    token = {
        "iat": issuedat_claim,
        "nbf": notbefore_claim,
        "exp": expire_claim,
        "data": {
            "full_name": full_name,
            "name": name
        }};
    token = jwt.encode(token, secret_key, algorithm="HS256")
    token = token.decode('utf-8')

    customer_devices = frappe.get_all("User Device", ['name'], filters={"udid": udid, "docstatus": ['<', 2]})
    customer_device = None
    if customer_device:
        customer_device = frappe.get_doc("User Device", customer_devices[0].name)
    else:
        customer_device = frappe.get_doc({"doctype": "User Device"})

    customer_device.user_type = "Customer"
    customer_device.user = name
    customer_device.udid = udid
    customer_device.fcm = fcm
    customer_device.access_token = token
    customer_device.enabled = 1
    customer_device.flags.ignore_permissions = True
    customer_device.save()

    ret_Customer = user(name)
    msg = _("Register Success")

    log.response = msg
    log.token = None
    log.Customer = name
    log.request = "register"
    log.flags.ignore_permissions = True
    log.insert()
    frappe.db.commit();
    frappe.local.response['status'] = {
        "message": msg,
        "code": 1,
        "success": True
    }
    frappe.local.response['data'] = {
        "Customer": ret_Customer,
        "access_token": token
    }



@frappe.whitelist(allow_guest=True)
def check_token():
    request = frappe.request
    secret_key = "Me System";
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
            frappe.db.commit();
            frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
            frappe.local.response['data'] = None
            return
        token = frappe.get_request_header("Authorization").replace('Bearer ', '');
        log.token = token

        customerDevices = frappe.get_all("User Device", ['name'],
                                         filters={"access_token": token, "docstatus": ['<', 2]})
        if not customerDevices:
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
        customerdevice = frappe.get_doc("User Device", customerDevices[0].name)
        if not customerdevice.user:
            frappe.local.response['http_status_code'] = 403
            log.response = _("Not Authorized")
            log.flags.ignore_permissions = True
            log.insert()
            frappe.db.commit();
            frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
            frappe.local.response['data'] = None
            return

        customer = frappe.get_doc("Customer", customerdevice.user)
        log.response = "success login"
        log.flags.ignore_permissions = True
        log.insert()
        frappe.db.commit();
        return {"user": customer}
    else:
        frappe.local.response['http_status_code'] = 403
        log.response = _("Not Authorized")
        log.flags.ignore_permissions = True
        log.insert()
        frappe.db.commit();
        frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return


@frappe.whitelist(allow_guest=True)
def me(**kwards):
    Lang = "ar"
    if frappe.get_request_header("Language"):
        Lang = frappe.get_request_header("Language")
    frappe.local.lang = Lang
    data = kwards
    user_data = None
    check = check_token()
    if check and "user" in check:
        user_data = check['user']
    if user_data:
        ret_Customer = user(user_data.name)
        frappe.local.response['status'] = {
            "message": _("Profile info"),
            "code": 1,
            "success": True
        }

        frappe.local.response['data'] = ret_Customer
    else:
        frappe.local.response['status'] = {
            "message": _("Incorrect credentials"),
            "code": 404,
            "success": False
        }
        frappe.local.response['data'] = None


@frappe.whitelist(allow_guest=True)
def user(user_name):
    customer = frappe.get_doc("Customer", user_name)

    isDisabled = False
    if customer.disabled == 1:
        isDisabled = True
    elif customer.disabled == 0:
        isDisabled = False

    customer_doc = {
        "id": customer.name,
        "customer_name": customer.customer_name,
        "email": customer.email,
        "mobile_number": customer.mobile_number,
        "is_disabled": isDisabled,
        "city" : customer.city
    }
    return customer_doc
