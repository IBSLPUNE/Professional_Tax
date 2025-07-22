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

    # Ensure State is not cancelled/submitted incorrectly
    if frappe.db.exists("State", {"name": state_name, "docstatus": ["!=", 1]}):
        # If state is not in Submitted state (docstatus 1), skip calculation
        return 0.0
    state = frappe.get_doc("State", state_name)

    # Get formula rows from State (Professional Tax slab/formula)
    formula_rows = state.get("formula") or []
    if not formula_rows:
        return 0.0

    # Calculate gross pay from earnings in the Salary Slip
    gross_pay = sum(flt(row.get("amount")) for row in (doc.get("earnings") or []))
    if gross_pay <= 0 and hasattr(doc, "gross_pay"):
        gross_pay = flt(doc.gross_pay)
    if gross_pay <= 0:
        # No earnings or zero gross pay, no PT applicable
        return 0.0

    # Extract the first valid component & formula for Professional Tax
    pt_component, pt_formula, default_amount = None, None, None
    for row in formula_rows:
        comp = row.get("component")
        formula = row.get("formula")
        default_amount = row.get("default_amount")
        if comp and formula:
            pt_component = comp
            pt_formula = formula
            # default_amount is taken from the first valid row
            break

    if not pt_component or not pt_formula:
        # No valid PT component or formula found
        return 0.0

    # Prepare context for formula evaluation (include all doc fields and utilities)
    eval_context = frappe._dict({
        key: flt(val) if isinstance(val, (int, float)) else val
        for key, val in doc.__dict__.items()
    })
    eval_context.update({
        "gross_pay": gross_pay,
        "getdate": getdate,
        "flt": flt
    })

    # Include salary structure components in context (if applicable)
    structure_name = None
    if hasattr(doc, "salary_structure") and doc.salary_structure:
        structure_name = doc.salary_structure
    elif doc.get("payroll_entry"):
        # If generated via Payroll Entry, find the relevant Salary Structure Assignment
        structure_name = frappe.db.get_value(
            "Salary Structure Assignment",
            {"employee": doc.employee, "from_date": ["<=", doc.start_date]},
            "salary_structure",
            order_by="from_date desc"
        )
    if structure_name:
        try:
            structure = frappe.get_doc("Salary Structure", structure_name)
            # Add all components (earnings and deductions) from the structure to eval_context
            for row in (structure.get("earnings", []) + structure.get("deductions", [])):
                if row.salary_component:
                    var_name = row.salary_component.replace(" ", "_").lower()
                    eval_context[var_name] = flt(row.amount)
        except Exception as e:
            frappe.msgprint(_("Error fetching Salary Structure: {0}").format(e))

    # Evaluate the Professional Tax formula to get the amount
    try:
        pt_amount = flt(safe_eval(pt_formula, eval_context))
        default_amount = flt(default_amount)
    except Exception as e:
        frappe.msgprint(
            _("Error while evaluating formula '{0}' for component '{1}': {2}")
            .format(pt_formula, pt_component, e)
        )
        return 0.0

    # Fetch Salary Component master to get flags like depends_on_payment_days, exempted_from_income_tax
    try:
        component_doc = frappe.get_doc("Salary Component", pt_component)
        pt_depends_on_payment_days = int(component_doc.get("depends_on_payment_days") or 0)
        pt_exempt_from_income_tax = int(component_doc.get("exempted_from_income_tax") or 0)
        pt_variable_based_on_taxable_salary = int(component_doc.get("variable_based_on_taxable_salary") or 0)
        pt_do_not_include_in_total = int(component_doc.get("do_not_include_in_total") or 0)
        pt_statistical_component = int(component_doc.get("statistical_component") or 0)
        pt_is_income_tax_component = int(component_doc.get("is_income_tax_component") or 0)
    except Exception as e:
        frappe.msgprint(_("Error fetching Salary Component details: {0}").format(e))
        pt_depends_on_payment_days = 0
        pt_exempt_from_income_tax = 0

    # Update or add the Professional Tax deduction entry in the Salary Slip
    existing_row = next((d for d in (doc.get("deductions") or []) if d.salary_component == pt_component), None)
    if existing_row:
        # Update existing PT deduction row
        existing_row.amount = pt_amount
        existing_row.default_amount = default_amount
        existing_row.depends_on_payment_days = pt_depends_on_payment_days
        existing_row.exempted_from_income_tax = pt_exempt_from_income_tax
    else:
        # Only add a new row if the calculated PT amount is > 0 (no deduction if formula results in 0)
        if pt_amount > 0:
            doc.append("deductions", {
                "salary_component": pt_component,
                "amount": pt_amount,
                "additional_amount": 0.0,
                "default_amount": default_amount,
                "depends_on_payment_days": pt_depends_on_payment_days,
                "exempted_from_income_tax": pt_exempt_from_income_tax
            })

    # Recompute the totals and other derived fields on the Salary Slip
    doc.run_method("calculate_net_pay")
    doc.run_method("compute_year_to_date")
    doc.run_method("compute_month_to_date")
    doc.run_method("compute_component_wise_year_to_date")
    doc.validate()

    return pt_amount
