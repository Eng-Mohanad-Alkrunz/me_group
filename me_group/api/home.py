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
def get_home():
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")

    frappe.local.lang = lang

    constructions_list =[]
    main_menu = frappe.get_all("Main Menu",fields=["*"])
    finishing_list = []
    for main in main_menu:
        enabled = False
        if main.enabled == 1:
            enabled = True
        else:
            enabled = False
        if main.meny_type == "Construction":
             constructions_list.append({
                 "id" : main.name,
                 "name" :_(main.menu_name),
                 "image":main.image,
                 "enabled":enabled
             })
        else:
            finishing_list.append({
                "id": main.name,
                "name": _(main.finishing),
                "image": main.image,
                "enabled": enabled
            })

    result = {
        "constructions":constructions_list,
        "finishing": finishing_list
    }

    frappe.local.response['status'] = {"message": _("Home Page"), "success": True,
                                       "code": 200}
    frappe.local.response['data'] = result


@frappe.whitelist(allow_guest=True)
def get_sub_menu(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")

    frappe.local.lang = lang
    data = kwards

    if "id" in data:
        con_id = data['id']
    else:
        frappe.local.response['status'] = {"message": _("Id Required"), "success": False,
                                           "code": 403}
        frappe.local.response['data'] = None

    result = {}
    sub_menu = frappe.get_all("Sub Menu Child",fields=["*"],filters={"parent":con_id})
    sub_menu_list = []
    for sub in sub_menu:
        enabled = False
        if sub.enabled == 1:
            enabled = True
        else:
            enabled = False
        sub_menu_list.append({
            "id" : sub.name,
            "name" :_(sub.sub_name),
            "enabled":enabled
        })


    result = {
        "main_menu_id": con_id,
        "sub_menu":sub_menu_list,

    }

    frappe.local.response['status'] = {"message": _("Home Page"), "success": True,
                                       "code": 200}
    frappe.local.response['data'] = result



