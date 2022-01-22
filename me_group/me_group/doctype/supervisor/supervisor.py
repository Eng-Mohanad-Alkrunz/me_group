# Copyright (c) 2022, test and contributors
# For license information, please see license.txt

# import frappe
import base64

from frappe.model.document import Document

class Supervisor(Document):


	def before_save(self):
		if self.password is None:
			password = "220122"
			password = password.encode("utf-8")
			encoded = base64.b64encode(password)
			self.password = encoded

