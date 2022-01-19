from __future__ import unicode_literals

import time

import frappe
import frappe.client
import frappe.handler
import jwt
from frappe import _
import base64
from passlib.context import CryptContext



@frappe.whitelist(allow_guest=True)
def login(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")

    frappe.local.lang = lang
    data = kwards


    if 'udid' not in data:
        frappe.local.response['status'] = {"message": _("Incorrect credentials"), "success": False,
                                           "code": 422}
        frappe.local.response['data'] = None
        return

    if 'email' not in data:
        frappe.local.response['status'] = {"message": _("Email Required"), "success": False,
                                           "code": 422}
        frappe.local.response['data'] = None
        return

    if 'password' not in data:
        frappe.local.response['status'] = {"message": _("Password Required"), "success": False,
                                           "code": 422}
        frappe.local.response['data'] = None
        return

    email = data['email']
    udid = data['udid']
    password = data['password']

    fcm = None
    if 'fcm' in data:
        fcm = data['fcm']

    log = frappe.get_doc({"doctype": "Api Log"})


    password = password.encode("utf-8")
    encoded = base64.b64encode(password)
    encoded = str(encoded)
    if not frappe.get_all("Customer", ['name'], filters={"email": email, "password": encoded}):
        print(encoded)
        frappe.local.response['http_status_code'] = 403
        log.response = "Incorrect credentials"
        log.request = "login"
        log.flags.ignore_permissions = True
        log.insert()
        frappe.db.commit();
        frappe.local.response['status'] = {"message": _("Incorrect credentials1"), "success": False,
                                           "code": 403}
        frappe.local.response['data'] = None
        return

    customer_list = frappe.get_all("Customer", ['name'], filters={"email": email, "password": encoded})
    customer_doc = frappe.get_doc("Customer", customer_list[0].name)
    full_name = customer_doc.customer_name
    name = customer_doc.name

    secret_key = "Me System";
    issuedat_claim = time.time()
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
    if customer_devices:
        customer_device = frappe.get_doc("User Device", customer_devices[0].name)
    else:
        customer_device = frappe.get_doc({"doctype": "User Device"})

    customer_device.user_type = "Customer"
    customer_device.user = customer_doc.name
    customer_device.udid = udid
    customer_device.fcm = fcm
    customer_device.access_token = token
    customer_device.enabled = 1
    customer_device.flags.ignore_permissions = True
    customer_device.save()

    ret_Customer = user(customer_doc.name);
    msg = _("Login Success")

    log.response = msg
    log.token = None
    log.Customer = customer_doc.name
    log.request = "login"
    log.flags.ignore_permissions = True
    log.insert()

    frappe.db.commit();

    frappe.local.response['status'] = {
        "message": _("Login Success"),
        "code": 1,
        "success": True
    }

    frappe.local.response['data'] = {
        "Customer": ret_Customer,
        "access_token": token
    }


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
    password = password.encode("utf-8")
    encoded = base64.b64encode(password)

    customer_doc = frappe.get_doc({"doctype": "Customer",
                                   "mobile_number": mobile,
                                   "email": email,
                                   "customer_name": full_name,
                                   "password":str(encoded),
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
def change_password(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang
    data = kwards

    check = check_token()
    user1 = None

    old_password = None
    new_password = None
    if 'old_password' in data:
        old_password = data['old_password']
    else:
        frappe.local.response['status'] = {"message": _("Old password required"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return

    if 'new_password' in data:
        new_password = data['new_password']
    else:
        frappe.local.response['status'] = {"message": _("New password required"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return


    if check and "user" in check:
        user1 = check['user']

    if not user1 or user1.customer_type != "Individual":
        frappe.local.response['http_status_code'] = 403
        frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return


    password = old_password.encode("utf-8")
    old_encoded = base64.b64encode(password)
    password = new_password.encode("utf-8")
    new_encoded = base64.b64encode(password)
    print(user1.password)
    print(old_encoded)
    if str(old_encoded) != user1.password:
        frappe.local.response['status'] = {"message": _("Old password not correct"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return

    customer = frappe.get_doc("Customer",user1.name)
    customer.set("password",str(new_encoded))
    customer.save(ignore_permissions=True)
    frappe.db.commit()

    name = customer.name
    secret_key = "Me System";
    issuedat_claim = time.time();
    notbefore_claim = issuedat_claim;
    expire_claim = issuedat_claim + (60 * 60 * 3 * 24 * 5);
    token = {
        "iat": issuedat_claim,
        "nbf": notbefore_claim,
        "exp": expire_claim,
        "data": {
            "full_name": customer.customer_name,
            "name": name
        }};
    token = jwt.encode(token, secret_key, algorithm="HS256")
    token = token.decode('utf-8')

    current_token = frappe.get_request_header("Authorization").replace('Bearer ', '');
    customer_devices = frappe.get_all("User Device", ['name'], filters={"access_token": current_token, "docstatus": ['<', 2]})
    customer_device = frappe.get_doc("User Device",customer_devices[0].name)
    customer_device.access_token = token
    customer_device.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.local.response['status'] = {"message": _("Password reset successfully"), "success": True, "code": 200}
    frappe.local.response['data'] = {
        "data":None,
        "access_token":token
    }
    return



@frappe.whitelist(allow_guest=True)
def get_profile(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang

    check = check_token()
    user1 = None
    if check and "user" in check:
        user1 = check['user']

    if not user1 or user1.customer_type != "Individual":
        frappe.local.response['http_status_code'] = 403
        frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return

    log = frappe.get_doc({"doctype": "Api Log"})


    msg = _("Profile info")

    log.response = msg
    log.token = None

    log.request = "profile info"
    log.flags.ignore_permissions = True
    log.insert()
    frappe.db.commit();

    frappe.local.response['status'] = {
        "message": msg,
        "code": 1,
        "success": True
    }

    frappe.local.response['data'] = {
        "id":user1.name,
        "full_name":user1.customer_name,
        "email":user1.email,
        "mobile_number":user1.mobile_number,
        "city":user1.city


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
