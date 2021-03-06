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
# from fpdf import FPDF
# import arabic_reshaper
# from bidi.algorithm import get_display


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

    customer = user1.name

    id_image = None
    if 'id_image' in frappe.request.files:
        try:
            res = upload_file("id_image")
            id_image = res.file_url
        except:
            id_image = None
    instrument_image = None
    if 'instrument_image' in frappe.request.files:
        try:
            res = upload_file("instrument_image")
            instrument_image = res.file_url
        except:
            instrument_image = None

    license_image = None
    if 'license_image' in frappe.request.files:
        try:
            res = upload_file("license_image")
            license_image = res.file_url
        except:
            license_image = None

    if "id_no" in data:
        id_no = data['id_no']
    else:
        frappe.local.response['status'] = {"message": _("ID NO. Required"), "success": False, "code": 403}
        frappe.local.response['data'] = None
        return
    contract_type = data['contract_type']
    sub_menu_id = data['sub_menu_id']

    diagrams = None
    try:
        diagrams=updatefile(data)
    except:
        diagrams = None
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

        id_image=id_image,
        license_image=license_image,
        instrument_image=instrument_image,
        diagrams=diagrams,
        engineer_contact=engineer_contact,
        instrument_no=instrument_no,
        docstatus=0,
    )).insert(ignore_permissions=True)
    contract.save(ignore_permissions=True)
    frappe.db.commit()
    contract_doc = frappe.get_doc("Contract Application",frappe.get_all("Contract Application",filters={'customer':user1.name},order_by="creation desc")[0])
    doc ={
        "id":contract_doc.name,
        "id_no":contract_doc.id_no,
        "id_release_date":contract_doc.id_release_date,
        "id_issuer":contract_doc.id_issuer,
        "instrument_date":contract_doc.instrument_date,
        "license_no":contract_doc.license_no,
        "license_date":contract_doc.license_date,
        "office_name":contract_doc.office_name,
        "engineer_name":contract_doc.engineer_name,
        "id_image":contract_doc.id_image,
        "engineer_contact":contract_doc.engineer_contact,
        "instrument_no":contract_doc.instrument_no,
        "contract_copy": contract_doc.contract_copy
    }
    frappe.local.response['status'] = {"message": _("Contract Created Successfully"), "success": True, "code": 200}
    frappe.local.response['data'] = doc

@frappe.whitelist(allow_guest=True)
def add_conditions(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang
    data = kwards
    contract_id = data['id']
    conditions = json.loads(data['conditions'])
    contract_doc = frappe.get_doc("Contract Application",contract_id)
    contract_doc.set("conditions",conditions)
    contract_doc.save(ignore_permissions=True)
    frappe.db.commit()

    doc = {
        "id": contract_doc.name,
        "id_no": contract_doc.id_no,
        "id_release_date": contract_doc.id_release_date,
        "id_issuer": contract_doc.id_issuer,
        "instrument_date": contract_doc.instrument_date,
        "license_no": contract_doc.license_no,
        "license_date": contract_doc.license_date,
        "office_name": contract_doc.office_name,
        "engineer_name": contract_doc.engineer_name,
        "id_image": contract_doc.id_image,
        "engineer_contact": contract_doc.engineer_contact,
        "instrument_no": contract_doc.instrument_no,
        "contract_copy":contract_doc.contract_copy
    }
    frappe.local.response['status'] = {"message": _("Contract Created Successfully"), "success": True, "code": 200}
    frappe.local.response['data'] = doc

@frappe.whitelist(allow_guest=True)
def get_contracts(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")
    frappe.local.lang = lang
    data = kwards
    contract = None
    if "contract" in data:
        contract = data['contract']

    check = check_token()
    user1 = None
    if check and "user" in check:
        user1 = check['user']
    contracts = None
    if contract is not None and contract != "":

        contracts = frappe.db.sql(f"SELECT name  FROM `tabContract Application` where customer = '{user1.name}' AND (name LIKE '%{contract}%' OR id_no LIKE '%{contract}%')", as_dict=True)
    else:
        contracts = frappe.get_all("Contract Application",filters={"customer":user1.name},order_by= "creation desc")

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
    agree = 0
    disagree = 0
    review = 0
    if contract.contract_status == "pending":
        pending_status = 1
    elif contract.contract_status == "approved by management":
        management_status = 1
    elif contract.contract_status == "approved by the customer":
        customer_status = 1
        if contract.customer_response == "agree":
            agree = 1
        elif contract.customer_response == "disagree":
            disagree = 1
        else:
            review = 1
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
            "status": customer_status,
            "agree" :agree,
            "disagree" : disagree,
            "review" : review,
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
        "contract_copy": contract.contract_copy,
        "conditions":conditions
    }


# @frappe.whitelist(allow_guest=True)
# def get_contract_copy(**kwards):
#     lang = "ar"
#     if frappe.get_request_header("Language"):
#         lang = frappe.get_request_header("Language")
#     frappe.local.lang = lang
#     data = kwards
#     id = None
#     if "id" in data:
#         id = data['id']
#     else:
#         frappe.local.response['status'] = {"message": _("ID Required"), "success": False, "code": 403}
#         frappe.local.response['data'] = None
#
#     check = check_token()
#     user1 = None
#     if check and "user" in check:
#         user1 = check['user']
#
#     contract = frappe.get_doc("Contract Application",id)
#     conditions = []
#
#     for condition in contract.conditions:
#         conditions.append({
#             "condition":condition.condition_details,
#             "check":_(condition.base_select)
#         })
#
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_margins(10,25,30)
#     pdf.add_font("Arial", "", "arial.ttf", uni=True)
#     pdf.set_font("Arial", size=15)
#     txt = arabic_reshaper.reshape("?????????? ????????")
#     txt = txt[::-1]
#     # create a cell
#     pdf.cell(200, 10, txt,
#              ln=1, align='C')
#
#     # add another cell
#     txt = arabic_reshaper.reshape("?????? "
#                                   "???????????? ??????????"
#                                   ")"
#                                   "???????? ????????"
#                                   "(")
#     txt = txt[::-1]
#     pdf.cell(200, 20, txt,
#              ln=2, align='C')
#
#     txt = arabic_reshaper.reshape("?????????? / ?????????? ?????????? ????????????????")
#     txt = txt[::-1]
#     pdf.cell(200, 10, txt,
#              ln=2, align='R')
#
#     txt = arabic_reshaper.reshape("?????????? ?????? ???? ???????????????? ?????????????? ?????????????? ?????? ???????? ???????? ?????? ???????? ???????? ????????")
#     txt = txt[::-1]
#     pdf.cell(200, 10, txt,
#              ln=2, align='R')
#
#     txt = arabic_reshaper.reshape("?????? ???? ??????"
#                                   " ???????????????? ?????????????? 27-12-2022"
#                                   " ???? ?????????????? ???? ?????????? "
#                                   "?????? "
#                                   "?????? ???? ???? :")
#     txt = txt[::-1]
#     pdf.cell(200, 10, txt,
#              ln=2, align='R')
#
#     txt = arabic_reshaper.reshape("1 . ?????????? / "
#                                   "???????? ???????????? "
#                                   "?????????? ?????? "
#                                   "059994554 "
#                                   " ???????????? "
#                                   "?????????????? ???????????????????? "
#                                   "?????????????? "
#                                   "22-12-1888 "
#                                   )
#     txt = txt[::-1]
#     pdf.cell(200, 10, txt,
#              ln=2, align='R')
#
#     txt = arabic_reshaper.reshape("?????? ???????????? ?????????? "
#                                   "?????? ???????? ?????? "
#                                   "112233 "
#                                   ""
#                                   )
#     txt = txt[::-1]
#     pdf.cell(200, 10, txt,
#              ln=2, align='R')
#     # save the pdf with name .pdf
#     pdf.output("GFG.pdf")
#
#     # frappe.local.response['status'] = {"message": _("Contract Details"), "success": True, "code": 200}
#     #
#     # frappe.local.response['data'] = {
#     #         "id" :contract.name,
#     #         "ID_no" :contract.id_no,
#     #         "id_release_date":contract.id_release_date,
#     #         "id_issuer":contract.id_issuer,
#     #         "id_image":contract.id_image,
#     #     "instrument_no":contract.instrument_no,
#     #     "instrument_date":contract.instrument_date,
#     #     "instrument_image":contract.instrument_image,
#     #     "license_no":contract.license_no,
#     #     "license_date":contract.license_date,
#     #     "license_image":contract.license_image,
#     #     "office_name":contract.office_name,
#     #     "engineer_name":contract.engineer_name,
#     #     "engineer_contact":contract.engineer_contact,
#     #     "diagrams":contract.diagrams,
#     #     "details":contract.details,
#     #     "customer_response":_(contract.customer_response),
#     #     "customer_note":contract.customer_note,
#     #     "price" : contract.price,
#     #     "contract_copy": contract.contract_copy,
#     #     "conditions":conditions
#     # }


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

    frappe.local.response['data'] = {
        "response" : response}


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


# @frappe.whitelist(allow_guest=True)
# def get_management_works(**kwards):
#     lang = "ar"
#     if frappe.get_request_header("Language"):
#         lang = frappe.get_request_header("Language")
#
#     frappe.local.lang = lang
#     data = kwards
#
#     check = check_token()
#     user1 = None
#     contract = None
#     if check and "user" in check:
#         user1 = check['user']
#
#     if "contract" in data:
#         contract = data['contract']
#
#     if not user1:
#         frappe.local.response['http_status_code'] = 403
#         frappe.local.response['status'] = {"message": _("Not Authorized"), "success": False, "code": 403}
#         frappe.local.response['data'] = None
#         return
#
#
#     result = []
#     works = []
#     if contract is not None and contract != "":
#         works = frappe.get_all("Work Management Application", fields=["*"], filters={"customer": user1.name,"contract": ['like', "%" + contract + "%"]})
#     else:
#         works = frappe.get_all("Work Management Application", fields=["*"], filters={"customer": user1.name})
#
#
#     for work in works:
#         work_doc = frappe.get_doc("Work Management Application",work.name)
#         result.append({
#             "id":work.name,
#             "contract":work.contract,
#             "date":work.date,
#             "supervisor" :work.supervisor,
#             "work": work.work,
#             "email": work.email,
#         })
#
#
#     frappe.local.response['status'] = {"message": _("Works list "), "success": True, "code": 200}
#     frappe.local.response['data'] = result

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
            "work_name":work.work_name,
            "contract":work.contract,
            "date":work.date,
            "status" :_(work.status),
            "images" : images
        })


    frappe.local.response['status'] = {"message": _("Works list "), "success": True, "code": 200}
    frappe.local.response['data'] = result



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


    if not frappe.db.exists("Contract Application",contract):
        frappe.local.response['status'] = {"message": _("Contract Not Found"), "success": False, "code": 403}
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

@frappe.whitelist(allow_guest=True)
def upload_file(param):
    user = frappe.get_doc("User", frappe.session.user)

    file = frappe.request.files[param]
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
        ret = frappe.new_doc("File")
        ret.folder = folder
        ret.file_name = filename
        ret.content = content
        ret.is_private = cint(is_private)
        ret.save(ignore_permissions=True)
        frappe.db.commit()

        gallery.append({
            "images": ret.file_url
        })

    return gallery


# @frappe.whitelist(allow_guest=True)
# def upload_file(param):
#     user = None
#     if frappe.session.user == 'Guest':
#         if frappe.get_system_settings('allow_guests_to_upload_files'):
#             ignore_permissions = True
#     else:
#         user = frappe.get_doc("User", frappe.session.user)
#         ignore_permissions = True
#     frappe.session.user
#     ignore_permissions = True
#     files = frappe.request.files
#     is_private = frappe.form_dict.is_private
#     doctype = frappe.form_dict.doctype
#     docname = frappe.form_dict.docname
#     fieldname = frappe.form_dict.fieldname
#     file_url = frappe.form_dict.file_url
#     folder = frappe.form_dict.folder or 'Home'
#     filename = frappe.form_dict.file_name
#     content = None
#
#     if param in files:
#
#         file = files[param]
#
#         content = file.stream.read()
#         filename = file.filename
#
#         frappe.local.uploaded_file = content
#         frappe.local.uploaded_filename = filename
#
#     # if not file_url and (frappe.session.user == "Guest" or (user and not user.has_desk_access())):
#         import mimetypes
#         filetype = mimetypes.guess_type(filename)[0]
#         # if filetype not in ALLOWED_MIMETYPES:
#         #     frappe.throw(_("You can only upload JPG, PNG, PDF, or Microsoft documents."))
#
#
#         ret = frappe.get_doc({
#             "doctype": "File",
#             "attached_to_doctype": doctype,
#             "attached_to_name": docname,
#             "attached_to_field": fieldname,
#             "folder": folder,
#             "file_name": filename,
#             "file_url": file_url,
#             "is_private": cint(is_private),
#             "content": content
#         })
#         ret.save(ignore_permissions=ignore_permissions)
#         return ret
