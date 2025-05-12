---
description: 
globs: 
alwaysApply: false
---
# Odoo Naming Conventions
 
This rule enforces naming conventions for Odoo models and files in the project.
 
## Model Name Convention
- **Description**: Model names must follow Odoo 16 guidelines and start with 'wilco'
- **Pattern**: `_name\s*=\s*['"]([^'"]+)['"]`
- **Message**: Model name '${1}' must start with 'wilco' and follow Odoo naming convention (module.model format)
- **Severity**: error
- **File Pattern**: `custom_addons/**/*.py`
- **Not Match**: `^wilco\.`
 
## File Name Convention
- **Description**: File names for models must start with 'wilco_'
- **Pattern**: `class\s+([A-Za-z][A-Za-z0-9_]*)\s*\(\s*models\.Model`
- **Message**: File containing model '${1}' must be named with prefix 'wilco_'
- **Severity**: error
- **File Pattern**: `custom_addons/**/*.py`
- **Not Match**: `wilco_`
 
## Examples
 
### Correct Model Names:
```python
class wilcoSAPProductMaster(models.Model):
    _name = 'wilco.sap.product.master'
    _description = 'wilco SAP Product Master'
```
 
### Correct File Names:
- `wilco_product.py`
- `wilco_sale_order.py`
- `wilco_purchase_order.py`
 
### Incorrect Examples:
❌ `product.py` (missing wilco_ prefix)
❌ `_name = 'product.model'` (missing wilco prefix)