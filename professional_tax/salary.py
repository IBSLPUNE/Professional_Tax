import frappe
from frappe import _
from frappe.utils import flt, getdate
from frappe.utils.safe_exec import safe_eval


def calculate_professional_tax_from_salary_slip(doc, method):
    """
    Calculate Professional Tax (or any component) for a Salary Slip based on the employee's state.
    The formula and component name are taken dynamically from the State Doctype's child table
    (linked via Employee.custom_state).
    """

    if not doc.employee:
        frappe.throw(_("Employee is not specified in the Salary Slip."))

    # Fetch Employee
    if not frappe.db.exists("Employee", doc.employee):
        frappe.throw(_("Employee {0} does not exist.").format(doc.employee))
    employee = frappe.get_doc("Employee", doc.employee)

    # Attempt to read the employee's state; if none, skip calculation
    state_name = employee.get("custom_state")
    if not state_name:
        return 0.0

    # If the State record does not exist, skip calculation
    if not frappe.db.exists("State", state_name):
        return 0.0
    # Fetch the State document    
    if frappe.db.exists("State", {"name": state_name, "docstatus": ["!=", 1]}):
        return 0.0
    state = frappe.get_doc("State", state_name)
    

    # Collect all formula rows (child table “formula”)
    formula_rows = state.get("formula") or []
    if not formula_rows:
        return 0.0

    # Calculate gross pay from earnings table
    gross_pay = sum(flt(row.get("amount")) for row in doc.get("earnings") or [])

    # Fallback to gross_pay field if earnings table is empty or zero
    if gross_pay <= 0 and hasattr(doc, "gross_pay"):
        gross_pay = flt(doc.gross_pay)

    # If gross_pay is still <= 0, skip calculation
    if gross_pay <= 0:
        return 0.0

    # Find the first formula row whose component has a non-empty formula
    pt_component = None
    pt_formula = None
    for row in formula_rows:
        comp = row.get("component")
        formula = row.get("formula")
        if comp and formula:
            pt_component = comp
            pt_formula = formula
            break

    # If no valid formula found, skip calculation
    if not pt_component or not pt_formula:
        return 0.0

    # Safely evaluate the formula
    try:
        pt_amount = safe_eval(
            pt_formula,
            {
                "gross_pay": gross_pay,
                "start_date": getdate(doc.start_date),
                "getdate": getdate
            }
        )
        pt_amount = flt(pt_amount)
    except Exception as e:
        # On error, log a warning and skip calculation
        frappe.msgprint(
            _("Error while evaluating formula '{0}' for component '{1}': {2}")
            .format(pt_formula, pt_component, e)
        )
        return 0.0

    # Update or append the deduction dynamically based on pt_component
    existing_row = next(
        (d for d in doc.get("deductions") or [] if d.salary_component == pt_component),
        None
    )

    if existing_row:
        existing_row.amount = pt_amount
    elif pt_amount > 0:
        doc.append("deductions", {
            "salary_component": pt_component,
            "amount": pt_amount
        })
    
    doc.run_method("calculate_net_pay")
    doc.run_method("compute_year_to_date")
    doc.run_method("compute_month_to_date")
    doc.run_method("compute_component_wise_year_to_date")

    return pt_amount
