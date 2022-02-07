# Copyright (c) 2022, test and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document

class ContractApplication(Document):

	def before_save(self):
		if self.workflow_state == "Final approved":
			if len(frappe.get_all("Financial Clearance",filters={"contract_application":self.name})) == 0:
				new_financial_clearance = frappe.new_doc("Financial Clearance")

				new_financial_clearance.contract_application = self.name
				new_financial_clearance.customer = self.customer
				new_financial_clearance.id_no = self.id_no
				new_financial_clearance.save(ignore_permissions=True)

