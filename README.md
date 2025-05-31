# Professional Tax for ERPNext

A lightweight app to automate Professional Tax (PT) calculations in ERPNext using state-specific, formula-driven rules.

---

## Problem Statement

- ERPNext lacks built-in, state-specific Professional Tax (PT) calculation based on dynamic slabs.  
- Manually entering PT amounts for each employee is error-prone and time-consuming.  
- State PT rates change frequently; manual updates risk non-compliance.  

## Our Solution

- Introduce a custom “State” doctype with a child table to define per-state, slab-based PT formulas.  
- Add a “State (PT)” link field on Employee so each employee is tied to their state’s formula table.  
- On Salary Slip validation, automatically evaluate the appropriate PT formula (using `safe_eval`) and insert the “Professional Tax” deduction.  
- Maintain all PT rules in the ERPNext UI—no code changes needed when state rates change.  


## 🔧 Features

- **State-wise PT Configuration**  
  Define dynamic tax slabs per state using Python-style formulas in a custom “State” doctype.  

- **Employee-State Linking**  
  Automatically associate each employee with their state’s PT rules via a custom `State` field on the Employee doctype.  

- **Auto Tax Deduction**  
  On Salary Slip creation (manual or via Payroll Entry), the app calculates and injects the correct “Professional Tax” deduction line.  

- **Safe Formula Evaluation**  
  Uses Frappe’s `safe_eval` to securely evaluate any valid slab or conditional expression.  

- **Fully Configurable from UI**  
  Update or add new PT formulas through the ERPNext interface—no code changes required.  

- **Standalone & Lightweight**  
  No dependency on India Compliance or other external apps—simply install and configure.

---

## 📊 Formula Example

Below is a sample Python expression for a state’s PT slab (e.g., Maharashtra):

```python
0 if gross_pay <= 7500
else 175 if gross_pay <= 10000
else 200
