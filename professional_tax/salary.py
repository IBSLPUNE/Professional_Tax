import frappe
import json
from frappe.utils.safe_exec import safe_eval
from frappe.utils import getdate


def calculate_professional_tax_from_salary_slip(doc,method):
    # Fetch Salary Slip 
    # frappe.throw(str(doc.name))
    salary_slip = frappe.get_doc("Salary Slip", doc.name)
    
    employee = salary_slip.employee
    start_date = salary_slip.start_date
    earnings = salary_slip.earnings

    # Fetch Employee document
    employee_doc = frappe.get_doc("Employee", employee)
    state_name = employee_doc.custom_state
    # frappe.throw(f"State Name: {state_name}")

    # If no state is assigned, no professional tax calculation
    if not state_name:
        return 0.0

    # Parse earnings if it's a JSON string
    # if isinstance(doc.earnings, str):
    #     try:
    #         earnings = json.loads(earnings)
    #     except Exception as e:
    #         frappe.throw(f"Failed to parse earnings: {e}")

    # Calculate gross pay by summing 'amount' from earnings list
    gross_pay = 0.0
    if isinstance(doc.earnings, list):
        for earning in doc.earnings:
            # Each earning is expected to be dict with 'amount'
            try:
                gross_pay += float(earning.get("amount", 0))
            except Exception:
                # fallback in case amount is not convertible to float
                pass

    # Fetch State document linked to Employee
    state_doc = frappe.get_doc("State", state_name)

    # Find the formula for 'Professional Tax' in state's formula child table
    pt_formula = None
    for row in state_doc.formula:
        if row.component == "Professional Tax":
            pt_formula = row.formula
            break

    # If no formula found, return 0
    if not pt_formula:
        return 0.0

    # Convert start_date string to date object for evaluation
    start_date_obj = getdate(start_date)

    try:
        # Safely evaluate the formula with given variables
        pt_amount = safe_eval(
            pt_formula,
            {
                "gross_pay": gross_pay,
                "start_date": start_date_obj,
                "getdate": getdate
            }
        )
        # frappe.throw(f"Professional Tax Amount: {pt_amount}")
        found = False
        # pt_amount = <your_calculated_pt_amount>  # replace with your PT amount variable

        for row in doc.deductions:
            if row.salary_component == "Professional Tax":
                row.amount = pt_amount
                found = True
                break  # optional: break once found

        if not found and pt_amount > 0:
            doc.append("deductions", {
                "salary_component": "Professional Tax",
                "amount": pt_amount
            })

    except Exception as e:
        frappe.throw(f"Error evaluating Professional Tax formula: {e}")

    # Return the calculated professional tax amount as float
    return float(pt_amount or 0.0)
