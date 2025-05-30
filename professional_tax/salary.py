import frappe
from frappe import _
from frappe.utils import flt, getdate
from frappe.utils.safe_exec import safe_eval


def calculate_professional_tax_from_salary_slip(doc, method):
    """
    Calculate Professional Tax for a Salary Slip based on the employee's state.
    The formula is defined in the State Doctype's child table (linked via Employee.custom_state).
    """

    if not doc.employee:
        frappe.throw(_("Employee is not specified in the Salary Slip."))

    # Fetch Employee
    if not frappe.db.exists("Employee", doc.employee):
        frappe.throw(_("Employee {0} does not exist.").format(doc.employee))
    employee = frappe.get_doc("Employee", doc.employee)

    # Validate state
    state_name = employee.get("custom_state")
    if not state_name:
        frappe.throw(_("State not specified for employee {0}.").format(employee.name))

    if not frappe.db.exists("State", state_name):
        frappe.throw(_("State '{0}' does not exist.").format(state_name))

    state = frappe.get_doc("State", state_name)

    # Validate formula table
    formula_rows = state.get("formula") or []
    if not formula_rows:
        frappe.throw(_("No Professional Tax formula defined in state '{0}'.").format(state_name))

    # Sum gross pay from earnings
    gross_pay = sum(flt(row.get("amount")) for row in doc.get("earnings") or [])

    # Fallback to gross_pay field if table is empty
    if gross_pay <= 0 and hasattr(doc, "gross_pay"):
        gross_pay = flt(doc.gross_pay)

    if gross_pay <= 0:
        frappe.throw(_("Gross Pay must be a positive number to compute Professional Tax."))

    # Extract the applicable formula
    pt_formula = None
    for row in formula_rows:
        if row.get("component") == "Professional Tax" and row.get("formula"):
            pt_formula = row.get("formula")
            break

    if not pt_formula:
        frappe.throw(_("No valid Professional Tax formula found for state '{0}'.").format(state_name))

    # Evaluate the formula safely
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
        frappe.throw(_("Error while evaluating Professional Tax formula: {0}").format(e))

    # Apply the deduction
    existing_row = next((row for row in doc.get("deductions") or [] if row.salary_component == "Professional Tax"), None)
    if existing_row:
        existing_row.amount = pt_amount
    elif pt_amount > 0:
        doc.append("deductions", {
            "salary_component": "Professional Tax",
            "amount": pt_amount
        })

    return pt_amount
