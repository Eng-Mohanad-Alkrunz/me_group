// Copyright (c) 2022, test and contributors
// For license information, please see license.txt

frappe.ui.form.on('Contract Application', {
	// refresh: function(frm) {

	// }
	contract_status:function(frm){
	    var current_status = frm.doc.contract_status;
	    if (current_status == "pending"){
	    console.log(current_status);
	    frm.set_df_property("sb02", "hidden", 1);
	    }else{
	    frm.set_df_property("sb02", "hidden", 0);
	    }
	    if (current_status == "final approved"){
	    frm.set_df_property("conditions", "read_only", 1);
	    frm.set_df_property("customer", "read_only", 1);
	    frm.set_df_property("customer_response", "read_only", 1);
	    frm.set_df_property("customer_note", "read_only", 1);
	    frm.set_df_property("price", "read_only", 1);
	    frm.set_df_property("financial_agreement", "read_only", 1);
	    }

	}
});
