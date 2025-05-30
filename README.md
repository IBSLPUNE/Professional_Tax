# Professional Tax for ERPNext

This app enables automated Professional Tax calculation in ERPNext based on custom formulas defined at the state level.

## 🔧 Features

- Define tax slabs per state using Python-style formulas
- Works with both manual and Payroll Entry-generated Salary Slips
- Automatically injects a `State` field in the Employee Doctype
- No dependency on India Compliance — lightweight & standalone

## 📊 Formula Example

```python
0 if gross_pay <= 7500 else 175 if gross_pay <= 10000 else 200
