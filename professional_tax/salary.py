import frappe
import json
from frappe.utils.safe_exec import safe_eval
from frappe.utils import getdate

def calculate_professional_tax_from_salary_slip(doc, method):
    # Use doc directly, no need to fetch again
    employee = doc.employee
    start_date = doc.start_date
    earnings = doc.earnings

    # Fetch Employee document
    employee_doc = frappe.get_doc("Employee", employee)
    state_name = employee_doc.custom_state

    # If no state is assigned, no professional tax calculation
    if not state_name:
        return 0.0

    # Calculate gross pay by summing 'amount' from earnings list
    gross_pay = 0.0
    if isinstance(earnings, list):
        for earning in earnings:
            try:
                gross_pay += float(earning.get("amount", 0))
            except Exception:
                pass

    # Fetch State document linked to Employee
    state_doc = frappe.get_doc("State", state_name)

    # Find the formula for 'Professional Tax' in state's formula child table
    pt_formula = None
    for row in state_doc.formula:
        if row.component == "Professional Tax":
            pt_formula = row.formula
            break

    if not pt_formula:
        return 0.0

    # Convert start_date to date object for evaluation
    start_date_obj = getdate(start_date)

    try:
        pt_amount = safe_eval(
            pt_formula,
            {
                "gross_pay": gross_pay,
                "start_date": start_date_obj,
                "getdate": getdate
            }
        )

        found = False
        for row in doc.deductions:
            if row.salary_component == "Professional Tax":
                row.amount = pt_amount
                found = True
                break

        if not found and pt_amount > 0:
            doc.append("deductions", {
                "salary_component": "Professional Tax",
                "amount": pt_amount
            })

    except Exception as e:
        frappe.throw(f"Error evaluating Professional Tax formula: {e}")

    return float(pt_amount or 0.0)
