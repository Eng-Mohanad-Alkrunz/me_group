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
                "name": _(main.menu_name),
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


@frappe.whitelist(allow_guest=True)
def get_terms():
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")

    frappe.local.lang = lang


    terms = frappe.get_single("Terms").terms



    result = {
        "terms":terms,
    }

    frappe.local.response['status'] = {"message": _("Terms And Conditions"), "success": True,
                                       "code": 200}
    frappe.local.response['data'] = result


@frappe.whitelist(allow_guest=True)
def get_about_us():
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")

    frappe.local.lang = lang


    about_us = frappe.get_single("About us").about
    us = frappe.get_single("About us").us
    logo = frappe.get_single("About us").logo
    slider =frappe.get_single("About us").slider

    my_slider =[]
    if slider is not None:
        for image in slider:
            my_slider.append({
                "image":image.images
            })

    result = {
        "about_us":about_us,
        "us": us,
        "logo": logo,
        "slider":my_slider
    }

    frappe.local.response['status'] = {"message": _("About Us"), "success": True,
                                       "code": 200}
    frappe.local.response['data'] = result




@frappe.whitelist(allow_guest=True)
def contact_us(**kwards):
    lang = "ar"
    if frappe.get_request_header("Language"):
        lang = frappe.get_request_header("Language")

    frappe.local.lang = lang


    data = kwards

    mobile = data['mobile']
    email = data['email']
    message = data['message']


    new_log = frappe.new_doc("Contact Us Log")
    new_log.mobile = mobile
    new_log.email = email
    new_log.message = message
    new_log.save(ignore_permissions=True)
    frappe.db.commit()


    frappe.local.response['status'] = {"message": _("Message Sent Successfully"), "success": True,
                                       "code": 200}
    frappe.local.response['data'] = None

