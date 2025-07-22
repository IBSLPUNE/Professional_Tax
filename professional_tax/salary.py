import frappe
from frappe import _
from frappe.utils import flt, getdate
from frappe.utils.safe_exec import safe_eval


def calculate_professional_tax_from_salary_slip(doc, method):
    if not doc.employee:
        frappe.throw(_("Employee is not specified in the Salary Slip."))

    # Fetch Employee
    if not frappe.db.exists("Employee", doc.employee):
        frappe.throw(_("Employee {0} does not exist.").format(doc.employee))
    employee = frappe.get_doc("Employee", doc.employee)

    # Get State from employee
    state_name = employee.get("custom_state")
    if not state_name or not frappe.db.exists("State", state_name):
        return 0.0

    # Ensure State is not cancelled
    if frappe.db.exists("State", {"name": state_name, "docstatus": ["!=", 1]}):
        return 0.0
    state = frappe.get_doc("State", state_name)

    # Get formula rows
    formula_rows = state.get("formula") or []
    if not formula_rows:
        return 0.0

    # Calculate gross pay
    gross_pay = sum(flt(row.get("amount")) for row in doc.get("earnings") or [])
    if gross_pay <= 0 and hasattr(doc, "gross_pay"):
        gross_pay = flt(doc.gross_pay)
    if gross_pay <= 0:
        return 0.0

    # Extract first valid component & formula
    pt_component, pt_formula , default_amount= None, None , None
    for row in formula_rows:
        comp = row.get("component")
        formula = row.get("formula")
        default_amount = row.get("default_amount")
        if comp and formula:
            pt_component = comp
            pt_formula = formula
            default_amount = default_amount
            break

    if not pt_component or not pt_formula:
        return 0.0

    # Prepare formula evaluation context
    eval_context = frappe._dict({
        key: flt(val) if isinstance(val, (int, float)) else val
        for key, val in doc.__dict__.items()
    })
    eval_context.update({
        "gross_pay": gross_pay,
        "getdate": getdate,
        "flt": flt
    })

    # Include salary structure components if any
    structure_name = None
    if hasattr(doc, "salary_structure") and doc.salary_structure:
        structure_name = doc.salary_structure
    elif doc.get("payroll_entry"):
        structure_name = frappe.db.get_value(
            "Salary Structure Assignment",
            {
                "employee": doc.employee,
                "from_date": ["<=", doc.start_date],
            },
            order_by="from_date desc",
            fieldname="salary_structure"
        )

    if structure_name:
        try:
            structure = frappe.get_doc("Salary Structure", structure_name)
            for row in structure.get("earnings", []) + structure.get("deductions", []):
                if row.salary_component:
                    variable_name = row.salary_component.replace(" ", "_").lower()
                    eval_context[variable_name] = flt(row.amount)
        except Exception as e:
            frappe.msgprint(_("Error fetching Salary Structure: {0}").format(e))

    # Evaluate formula
    try:
        pt_amount = safe_eval(pt_formula, eval_context)
        pt_amount = flt(pt_amount)
        default_amount = flt(default_amount)
    except Exception as e:
        frappe.msgprint(
            _("Error while evaluating formula '{0}' for component '{1}': {2}")
            .format(pt_formula, pt_component, e)
        )
        return 0.0

    # Update or append deduction row
    existing_row = next(
        (d for d in doc.get("deductions") or [] if d.salary_component == pt_component),
        None
    )

    if existing_row:
        existing_row.amount = pt_amount
    elif pt_amount > 0:
        doc.append("deductions", {
            "salary_component": pt_component,
            "amount": pt_amount,
            "default_amount": default_amount
        })

    # Recalculate totals
    doc.run_method("calculate_net_pay")
    doc.run_method("compute_year_to_date")
    doc.run_method("compute_month_to_date")
    doc.run_method("compute_component_wise_year_to_date")
    doc.validate()
    

    return pt_amount
