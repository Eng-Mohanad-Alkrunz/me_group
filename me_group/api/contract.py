from __future__ import unicode_literals

import sys
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
import json

ALLOWED_MIMETYPES = ('image/png', 'image/jpeg', 'application/pdf', 'application/msword',
			'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
			'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
			'application/vnd.oasis.opendocument.text', 'application/vnd.oasis.opendocument.spreadsheet')
@frappe.whitelist(allow_guest=True)
def get_conditions():
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang

    result = []

    conditions = frappe.get_all("Contract Condition",fields =["name","condition"],filters={"enabled":1})

    for condition in conditions:
        result.append({
            "id":condition.name,
            "condition":condition.condition
        })

    frappe.local.response['status'] = {"message": _("Conditions list"), "success": True, "code": 200}
    frappe.local.response['data'] = result


@frappe.whitelist(allow_guest=True)
def create_contract(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang
    data = kwards


    check = check_token()
    user1 = None
    if check and "user" in check:
        user1 = check['user']

    id_no = None
    id_release_date = data['id_release_date']
    id_issuer = data['id_issuer']
    instrument_no = data['instrument_no']
    instrument_date = data['instrument_date']
    license_no = data['license_no']
    license_date = data['license_date']
    office_name = data['office_name']
    engineer_name = data['engineer_name']
    engineer_contact = data['engineer_contact']
    conditions = json.loads(data['conditions'])
    customer = user1.name

    id_image = None
    if 'id_image' in frappe.request.files:
        res = upload_file("id_image")
        id_image = res.file_url
    instrument_image = None
    if 'instrument_image' in frappe.request.files:
        res = upload_file("instrument_image")
        instrument_image = res.file_url
    license_image = None
    if 'license_image' in frappe.request.files:
        res = upload_file("license_image")
        license_image = res.file_url
    # diagrams = None
    # if 'diagrams' in frappe.request.files:
    #     res = upload_file("diagrams")
    #     diagrams = res.file_url




    if "id_no" in data:
        id_no = data['id_no']
    else:
        frappe.local.response['status'] = {"message": _("ID NO. Required"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return

    contract = frappe.get_doc(dict(
        doctype='Contract Application',
        customer=user1.name,
        id_no=id_no,
        id_release_date=id_release_date,
        id_issuer=id_issuer,
        instrument_date=instrument_date,
        license_no=license_no,
        license_date=license_date,
        office_name=office_name,
        engineer_name=engineer_name,
        conditions=conditions,
        id_image=id_image,
        license_image=license_image,
        instrument_image=instrument_image,
        diagrams=updatefile(data),
        engineer_contact=engineer_contact,
        instrument_no=instrument_no,
        docstatus=0,
    )).insert(ignore_permissions=True)
    contract.save(ignore_permissions=True)
    frappe.db.commit()

    frappe.local.response['status'] = {"message": _("Contract Created Successfully"), "success": True, "code": 200}
    frappe.local.response['data'] = None


@frappe.whitelist(allow_guest=True)
def get_contracts(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang
    data = kwards
    search = None
    if "search" in data:
        search = data['search']

    check = check_token()
    user1 = None
    if check and "user" in check:
        user1 = check['user']
    contracts = None
    if search is not None:
        print(search)
        contracts = frappe.db.sql(f"SELECT name  FROM `tabContract Application` where customer = '{user1.name}' AND (name LIKE '%{search}%' OR id_no LIKE '%{search}%')", as_dict=True)
    else:
        contracts = frappe.get_all("Contract Application",filters={"customer":user1.name})

    frappe.local.response['status'] = {"message": _("Contracts List"), "success": True, "code": 200}
    frappe.local.response['data'] = contracts


@frappe.whitelist(allow_guest=True)
def get_contract_status(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang
    data = kwards
    id = None
    if "id" in data:
        id = data['id']
    else:
        frappe.local.response['status'] = {"message": _("ID Required"), "success": False, "code": 403}
        frappe.local.response['data'] = None

    check = check_token()
    user1 = None
    if check and "user" in check:
        user1 = check['user']

    contract = frappe.get_doc("Contract Application",id)
    pending_status = 0
    management_status = 0
    customer_status = 0
    approved_status = 0
    end_status = 0

    if contract.contract_status == "pending":
        pending_status = 1
    elif contract.contract_status == "approved by management":
        management_status = 1
    elif contract.contract_status == "approved by the customer":
        customer_status = 1
    elif contract.contract_status == "final approved":
        approved_status = 1
    elif contract.contract_status == "end of the contract":
        end_status = 1


    frappe.local.response['status'] = {"message": _("Contracts List"), "success": True, "code": 200}

    frappe.local.response['data'] = {
        "pending":{
            "status":pending_status
        },
        "approved by management": {
            "status": management_status
        },
        "approved by the customer": {
            "status": customer_status
        },
        "final approved": {
            "status": approved_status
        },
        "end of the contract": {
            "status": end_status
        },

    }

@frappe.whitelist(allow_guest=True)
def get_contract_details(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang
    data = kwards
    id = None
    if "id" in data:
        id = data['id']
    else:
        frappe.local.response['status'] = {"message": _("ID Required"), "success": False, "code": 403}
        frappe.local.response['data'] = None

    check = check_token()
    user1 = None
    if check and "user" in check:
        user1 = check['user']

    contract = frappe.get_doc("Contract Application",id)
    conditions = []

    for condition in contract.conditions:
        conditions.append({
            "condition":condition.condition_details,
            "check":_(condition.base_select)
        })



    frappe.local.response['status'] = {"message": _("Contract Details"), "success": True, "code": 200}

    frappe.local.response['data'] = {
            "id" :contract.name,
            "ID_no" :contract.id_no,
            "id_release_date":contract.id_release_date,
            "id_issuer":contract.id_issuer,
            "id_image":contract.id_image,
        "instrument_no":contract.instrument_no,
        "instrument_date":contract.instrument_date,
        "instrument_image":contract.instrument_image,
        "license_no":contract.license_no,
        "license_date":contract.license_date,
        "license_image":contract.license_image,
        "office_name":contract.office_name,
        "engineer_name":contract.engineer_name,
        "engineer_contact":contract.engineer_contact,
        "diagrams":contract.diagrams,
        "details":contract.details,
        "customer_response":_(contract.customer_response),
        "customer_note":contract.customer_note,
        "price" : contract.price,
        "conditions":conditions
    }


@frappe.whitelist(allow_guest=True)
def update_customer_status(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang
    data = kwards
    id = None
    response = "Agree"
    note = ""

    if "response" in data:
        response = data['response']
    if "note" in data:
        note = data['note']

    if "id" in data:
        id = data['id']
    else:
        frappe.local.response['status'] = {"message": _("ID Required"), "success": False, "code": 403}
        frappe.local.response['data'] = None

    check = check_token()
    user1 = None
    if check and "user" in check:
        user1 = check['user']

    # contract = frappe.get_doc("Contract Application",id)
    frappe.db.sql(f"""Update `tabContract Application` set customer_response ='{response}',customer_note ='{note}' where name='{id}'""")
    frappe.db.commit()

    frappe.local.response['status'] = {"message": _("contract updated successful"), "success": True, "code": 200}

    frappe.local.response['data'] = None


@frappe.whitelist(allow_guest=True)
def update_contract_financial(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang
    data = kwards
    id = None
    agree = 0
    if "id" in data:
        id = data['id']
    else:
        frappe.local.response['status'] = {"message": _("ID Required"), "success": False, "code": 403}
        frappe.local.response['data'] = None

    if "agree" in data:
        agree = data['agree']


    check = check_token()
    user1 = None
    if check and "user" in check:
        user1 = check['user']
    frappe.db.sql(f"""update `tabFinancial Clearance` set agreement = {agree} , docstatus = 1""")


    frappe.db.commit()
    financial_agreement = frappe.get_doc("Financial Clearance",id)
    frappe.db.sql(f"""update `tabContract Application` set financial_agreement = 1 """)

    result ={}
    agree = False
    if financial_agreement.agreement == 1:
        agree = True
    else:
        agree = False
    result = {
        "id" : financial_agreement.name,
        "contract_id":financial_agreement.contract_application,
        "customer" :financial_agreement.customer,
        "id_no":financial_agreement.id_no,
        "agreement": agree,
        "agreement_essay": financial_agreement.agreement_essay
    }


    frappe.local.response['status'] = {"message": _("Financial Clearance"), "success": True, "code": 200}
    frappe.local.response['data'] = result


@frappe.whitelist(allow_guest=True)
def get_contract_financial(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang
    data = kwards
    id = None
    if "id" in data:
        id = data['id']
    else:
        frappe.local.response['status'] = {"message": _("ID Required"), "success": False, "code": 403}
        frappe.local.response['data'] = None

    check = check_token()
    user1 = None
    if check and "user" in check:
        user1 = check['user']
    financial_agreements = frappe.get_all("Financial Clearance",fields=["*"],filters={"contract_application":id})
    result ={}
    if len(financial_agreements) > 0:
        financial_agreement = financial_agreements[0]
        agree = False
        if financial_agreement.agreement == 1:
            agree = True
        else:
            agree = False
        result = {
            "id" : financial_agreement.name,
            "contract_id":financial_agreement.contract_application,
            "customer" :financial_agreement.customer,
            "id_no":financial_agreement.id_no,
            "agreement": agree,
            "agreement_essay": financial_agreement.agreement_essay
        }


    frappe.local.response['status'] = {"message": _("Contracts List"), "success": True, "code": 200}
    frappe.local.response['data'] = result


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
        frappe.db.commit()
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

# @frappe.whitelist(allow_guest=True)
# def uploadfile(param):
#     user = frappe.get_doc("User", frappe.session.user)
#
#     file = frappe.request.files[param]
#     is_private = 0
#     fieldname = ""
#     folder = 'Home'
#     filename = ""
#     content = None
#
#     if file:
#         content = file.stream.read()
#         filename = file.filename
#         content_type = guess_type(filename)[0]
#     frappe.local.uploaded_file = content
#     frappe.local.uploaded_filename = filename
#
#     ret = frappe.get_doc({
#         "doctype": "File",
#         "attached_to_doctype": "",
#         "attached_to_name": "",
#         "attached_to_field": "",
#         "folder": folder,
#         "file_name": filename,
#         "file_url": "",
#         "is_private": cint(is_private),
#         "content": content
#     })
#     ret.save(ignore_permissions=True)
#     return ret

@frappe.whitelist(allow_guest=True)
def updatefile(data):
    gallery = []
    user = frappe.get_doc("User", frappe.session.user)
    i = 0
    for i in range(len(frappe.request.files)):
        file = frappe.request.files['image['+str(i)+']']
        is_private = 0
        folder = 'Home'
        content = file.stream.read()
        filename = file.filename
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
            "images": ret.file_url
        })
        print(gallery)
    return gallery


@frappe.whitelist(allow_guest=True)
def upload_file(param):
	user = None
	if frappe.session.user == 'Guest':
		if frappe.get_system_settings('allow_guests_to_upload_files'):
			ignore_permissions = True
		else:
			return
	else:
		user = frappe.get_doc("User", frappe.session.user)
		ignore_permissions = True

	files = frappe.request.files
	is_private = frappe.form_dict.is_private
	doctype = frappe.form_dict.doctype
	docname = frappe.form_dict.docname
	fieldname = frappe.form_dict.fieldname
	file_url = frappe.form_dict.file_url
	folder = frappe.form_dict.folder or 'Home'
	filename = frappe.form_dict.file_name
	content = None

	if param in files:
		file = files[param]
		content = file.stream.read()
		filename = file.filename

	frappe.local.uploaded_file = content
	frappe.local.uploaded_filename = filename

	if not file_url and (frappe.session.user == "Guest" or (user and not user.has_desk_access())):
		import mimetypes
		filetype = mimetypes.guess_type(filename)[0]
		if filetype not in ALLOWED_MIMETYPES:
			frappe.throw(_("You can only upload JPG, PNG, PDF, or Microsoft documents."))

	else:
		ret = frappe.get_doc({
			"doctype": "File",
			"attached_to_doctype": doctype,
			"attached_to_name": docname,
			"attached_to_field": fieldname,
			"folder": folder,
			"file_name": filename,
			"file_url": file_url,
			"is_private": cint(is_private),
			"content": content
		})
		ret.save(ignore_permissions=ignore_permissions)
		return ret