# Copyright (c) 2022, test and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document
from frappe import _
class ContractApplication(Document):

	def before_save(self):

		if self.workflow_state == "Approved by management":
			if self.price is None or self.price == 0:
				frappe.throw(_("Please Enter Price"))
				return
			pre_notifications = frappe.get_all("Notification Me",filters={"doc_reference":self.name,"rank":1})
			if len(pre_notifications) == 0 :
				notification = frappe.new_doc("Notification Me")
				notification.type="need response"
				notification.text = "لقد تم إدراج سعر للعقد المرسل وتبلغ قيمته " \
									+ " " + str(self.price) + " ريال سعودي"
				notification.reference_type =  "Customer"
				notification.reference = self.customer
				notification.doc_type = "Contract Application"
				notification.doc_reference = self.name
				notification.rank = 1
				notification.save(ignore_permissions = True)
				frappe.db.commit()


		if self.workflow_state == "Final approved":
			if len(frappe.get_all("Financial Clearance",filters={"contract_application":self.name})) == 0:
				new_financial_clearance = frappe.new_doc("Financial Clearance")

				new_financial_clearance.contract_application = self.name
				new_financial_clearance.customer = self.customer
				new_financial_clearance.id_no = self.id_no
				new_financial_clearance.save(ignore_permissions=True)
				frappe.db.commit()

				pre_notifications = frappe.get_all("Notification Me", filters={"doc_reference": self.name, "rank": 2})
				if len(pre_notifications) == 0:
					notification = frappe.new_doc("Notification Me")
					notification.type = "display"
					notification.text = "لقد تم إصدار مخالصة مالية للعقد " \
										" " + self.name + " يرجى الرد على المخالصة لإتمام العقد "
					notification.reference_type = "Customer"
					notification.reference = self.customer
					notification.doc_type = "Financial Clearance"
					docs =frappe.get_all("Financial Clearance",filters={"contract_application":self.name})
					notification.doc_reference = docs[0].name
					notification.rank = 2
					notification.save(ignore_permissions=True)
					frappe.db.commit()


		if self.sub_menu_id:
			try:
				self.sub_menu_id = frappe.get_doc("Sub Menu Child",self.sub_menu_id).sub_name
			except:
				self.sub_menu_id = ""

