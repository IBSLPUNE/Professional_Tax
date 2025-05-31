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
![image](https://github.com/user-attachments/assets/6c6bb534-24e5-48af-818b-e5aafb3ebf7f)
![image](https://github.com/user-attachments/assets/8de0dc90-d296-460a-a324-0529ba99f06e)
![image](https://github.com/user-attachments/assets/c035b62e-1820-4a7d-9111-10b812329583)


## ⚙️ Setup Instructions

1. Define State & Formula
Go to State and create a new record (e.g., “Maharashtra”).

In the Formula child table, add a row for each PT slab:

Component: “Professional Tax”

Formula: Python expression using gross_pay and start_date (e.g.,0 if gross_pay <= 7500 else 175 if gross_pay <= 10000 else (200 if getdate(start_date).month != 2 else 300))

Submit the State record (only submitted states appear for employees).

2. Assign State to Employee
Open an Employee record.

In the State (PT) link field, select a submitted State (e.g., “Maharashtra”).

Save (and submit if needed).

3. Automatic PT Calculation on Salary-Slip via Payroll or Manually.