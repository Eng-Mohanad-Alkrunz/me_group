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
    encoded = base64.b64encode(password).decode("utf-8")

    if not frappe.get_all("Supervisor", ['name'], filters={"email": email, "password": str(encoded)}):

        frappe.local.response['http_status_code'] = 403
        log.response = "Incorrect credentials"
        log.request = "login"
        log.flags.ignore_permissions = True
        log.insert()
        frappe.db.commit()
        frappe.local.response['status'] = {"message": _("Incorrect credentials1"), "success": False,
                                           "code": 403}
        frappe.local.response['data'] = None
        return

    supervisor_list = frappe.get_all("Supervisor", ['name'], filters={"email": email, "password": encoded})
    supervisor_doc = frappe.get_doc("Supervisor", supervisor_list[0].name)
    full_name = supervisor_doc.supervisor
    name = supervisor_doc.name

    secret_key = "Me System"
    issuedat_claim = time.time()
    notbefore_claim = issuedat_claim
    expire_claim = issuedat_claim + (60 * 60 * 3 * 24 * 5)
    token = {
        "iat": issuedat_claim,
        "nbf": notbefore_claim,
        "exp": expire_claim,
        "data": {
            "full_name": full_name,
            "name": name
        }}
    try:
        token = jwt.encode(token, secret_key, algorithm="HS256").decode()
    except:
        token = jwt.encode(token, secret_key, algorithm="HS256")
    supervisor_devices = frappe.get_all("User Device", ['name'], filters={"udid": udid, "docstatus": ['<', 2]})
    supervisor_device = None
    if supervisor_devices:
        supervisor_device = frappe.get_doc("User Device", supervisor_devices[0].name)
    else:
        supervisor_device = frappe.get_doc({"doctype": "User Device"})

    supervisor_device.user_type = "Supervisor"
    supervisor_device.user = supervisor_doc.name
    supervisor_device.udid = udid
    supervisor_device.fcm = fcm
    supervisor_device.access_token = str(token)
    supervisor_device.enabled = 1
    supervisor_device.flags.ignore_permissions = True
    supervisor_device.save()

    ret_supervisor = user(supervisor_doc.name)
    msg = _("Login Success")

    log.response = msg
    log.token = None
    log.Customer = supervisor_doc.name
    log.request = "login"
    log.flags.ignore_permissions = True
    log.insert()

    frappe.db.commit()

    frappe.local.response['status'] = {
        "message": _("Login Success"),
        "code": 200,
        "success": True
    }

    frappe.local.response['data'] = {
        "User": ret_supervisor,
        "user_type": "Supervisor",
        "access_token": str(token)
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

    if not user1 :
        frappe.local.response['http_status_code'] = 403
        frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return


    password = old_password.encode("utf-8")
    old_encoded = base64.b64encode(password).decode("utf-8")
    password = new_password.encode("utf-8")
    new_encoded = base64.b64encode(password).decode("utf-8")

    if str(old_encoded) != user1.password:
        frappe.local.response['status'] = {"message": _("Old password not correct"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return

    supervisor = frappe.get_doc("Supervisor",user1.name)
    supervisor.set("password",str(new_encoded))
    supervisor.save(ignore_permissions=True)
    frappe.db.commit()

    name = supervisor.name
    secret_key = "Me System"
    issuedat_claim = time.time()
    notbefore_claim = issuedat_claim
    expire_claim = issuedat_claim + (60 * 60 * 3 * 24 * 5)
    token = {
        "iat": issuedat_claim,
        "nbf": notbefore_claim,
        "exp": expire_claim,
        "data": {
            "full_name": supervisor.supervisor,
            "name": name
        }}
    try:
        token = jwt.encode(token, secret_key, algorithm="HS256").decode()
    except:
        token = jwt.encode(token, secret_key, algorithm="HS256")
    # token = token.decode('utf-8')

    current_token = frappe.get_request_header("Authorization").replace('Bearer ', '')
    customer_devices = frappe.get_all("User Device", ['name'], filters={"access_token": current_token, "docstatus": ['<', 2]})
    customer_device = frappe.get_doc("User Device",customer_devices[0].name)
    customer_device.access_token = str(token)
    customer_device.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.local.response['status'] = {"message": _("Password reset successfully"), "success": True, "code": 200}
    frappe.local.response['data'] = {
        "data":None,
        "access_token":str(token)
    }
    return

@frappe.whitelist(allow_guest=True)
def logout(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang
    request = frappe.request
    secret_key = "ME System"
    if frappe.get_request_header("Authorization"):

        authorization_header = frappe.get_request_header("Authorization").split(" ")
        if authorization_header[0] != "Bearer" and len(authorization_header) != 2:
            frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 15}
            frappe.local.response['data'] = None
            return
        token = frappe.get_request_header("Authorization").replace('Bearer ', '')
        customerDevices = frappe.get_all("User Device", ['name'],
                                         filters={"access_token": token, "docstatus": ['<', 2]})
        if not customerDevices:
            frappe.local.response['http_status_code'] = 403
            frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 15}
            frappe.local.response['data'] = None
            return

        try:
            token = jwt.decode(token, secret_key, algorithms="HS256")

        except Exception:
            frappe.local.response['http_status_code'] = 401
            frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 15}
            frappe.local.response['data'] = None
            return

        customer_device = frappe.get_doc("User Device", customerDevices[0].name)

        frappe.db.sql(
            """update `tabUser Device` set access_token = "" where name = '{0}' """.format(customer_device.name))
        frappe.db.commit()

        msg = _("Logout")
        frappe.local.response['status'] = {"message": msg,
                                           "success": True,
                                           "code": 15}
        frappe.local.response['data'] = None
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

    if not user1 :
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
    frappe.db.commit()

    frappe.local.response['status'] = {
        "message": msg,
        "code": 1,
        "success": True
    }

    frappe.local.response['data'] = {
        "id":user1.name,
        "full_name":user1.supervisor,
        "email":user1.email,
        "mobile_number":user1.mobile_number,
        "city":user1.city,
        "image":user1.image


    }


@frappe.whitelist(allow_guest=True)
def update_profile(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang

    check = check_token()
    user1 = None
    data = kwards

    if check and "user" in check:
        user1 = check['user']

    mobile = None
    email = None
    full_name = None
    city = None

    if "email" in data:
        email = data['email']


    if "mobile_number" in data:
        mobile = data['mobile_number']

    if "city" in data:
        city = data['city']
    else:
        city = user1.city

    if "full_name" in data:
        full_name = data['full_name']
    else :
        full_name = user1.supervisor

    image = None
    if 'image' in frappe.request.files:
        res = uploadfile()
        image = res.file_url


    if not user1 :
        frappe.local.response['http_status_code'] = 403
        frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return

    log = frappe.get_doc({"doctype": "Api Log"})


    if email is not None and mobile is not None:
        if(len(frappe.get_all("Customer",filters={"email":data['email'],"mobile_number":mobile})) > 0):
            if email != user1.email:
                if mobile != user1.mobile_number:
                    frappe.local.response['status'] = {"message": _("Email or Mobile is already exists"), "success": False, "code": 403}
                    frappe.local.response['data'] = None
                    return

        elif (len(frappe.get_all("Supervisor", filters={"email": data['email'], "mobile_number": mobile})) > 0):
            if email != user1.email:
                if mobile != user1.mobile_number:
                    frappe.local.response['status'] = {"message": _("Email or Mobile is already exists"),
                                                       "success": False, "code": 403}
                    frappe.local.response['data'] = None
                    return

    if email is None:
        email = user1.email
    if mobile is None:
        mobile = user1.mobile_number

    supervisor = frappe.get_doc("Supervisor",user1.name)
    supervisor.email = email
    supervisor.mobile_number = mobile
    supervisor.supervisor = full_name
    supervisor.city = city
    if image is not None:
        supervisor.image = image
    supervisor.save(ignore_permissions = True)
    frappe.db.commit()

    msg = _("Profile edit")

    log.response = msg
    log.token = None

    log.request = "profile updated successful"
    log.flags.ignore_permissions = True
    log.insert()
    frappe.db.commit()

    frappe.local.response['status'] = {
        "message": msg,
        "code": 1,
        "success": True
    }

    frappe.local.response['data'] = {
        "id":user1.name,
        "full_name":full_name,
        "email":email,
        "mobile_number":mobile,
        "city":city,
        "image":image
    }


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
            frappe.db.commit()
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
            frappe.db.commit()
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
def me(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang
    data = kwards
    user_data = None
    check = check_token()
    if check and "user" in check:
        user_data = check['user']
    if user_data:
        ret_supervisor = user(user_data.name)
        frappe.local.response['status'] = {
            "message": _("Profile info"),
            "code": 1,
            "success": True
        }

        frappe.local.response['data'] = ret_supervisor
    else:
        frappe.local.response['status'] = {
            "message": _("Incorrect credentials"),
            "code": 404,
            "success": False
        }
        frappe.local.response['data'] = None


@frappe.whitelist(allow_guest=True)
def user(user_name):
    supervisor = frappe.get_doc("Supervisor", user_name)

    isDisabled = False
    if supervisor.disabled == 1:
        isDisabled = True
    elif supervisor.disabled == 0:
        isDisabled = False

    supervisor_doc = {
        "id": supervisor.name,
        "supervisor_name": supervisor.supervisor,
        "email": supervisor.email,
        "mobile_number": supervisor.mobile_number,
        "is_disabled": isDisabled,
        "city" : supervisor.city,
        "image":supervisor.image
    }
    return supervisor_doc

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

    ret = frappe.new_doc("File")
    ret.folder = folder
    ret.file_name = filename
    ret.content = content
    ret.is_private = cint(is_private)
    ret.save(ignore_permissions=True)
    frappe.db.commit()
    return ret