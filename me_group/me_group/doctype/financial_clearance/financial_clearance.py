# Copyright (c) 2022, test and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document

class FinancialClearance(Document):

	def before_save(self):
		agreement = frappe.get_single("Khalta Settings").agreement_essay
		if agreement != None:

			agreement = str.replace(agreement, '{Customer}', self.customer, 1)
			agreement = str.replace(agreement, '{id_no}', self.id_no, 1)
			agreement = str.replace(agreement, '{contract_id}', self.contract_application, 1)
			self.agreement_essay = agreement

