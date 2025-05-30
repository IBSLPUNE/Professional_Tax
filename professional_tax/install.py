def after_install():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    create_custom_fields({
        "Employee": [
            {
                "fieldname": "custom_state",
                "label": "State (PT)",
                "fieldtype": "Link",
                "options": "State",  
                "insert_after": "date_of_birth",
                "reqd": 0
            }
        ]
    })
