# Copyright (c) 2022, test and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class WorkManagementApplication(Document):

	def before_save(self):
		pre_notifications = frappe.get_all("Notification Me", filters={"doc_reference": self.name, "rank": 1})
		if len(pre_notifications) == 0:
			notification = frappe.new_doc("Notification Me")
			notification.type = "display"
			notification.text = "لقد تم إدراج عمل جديد للعقد " \
								" " + self.contract
			notification.reference_type = "Customer"
			notification.reference = self.customer
			notification.doc_type = "Work Management Application"
			notification.doc_reference = self.name
			notification.rank = 1
			notification.save(ignore_permissions=True)
			frappe.db.commit()

