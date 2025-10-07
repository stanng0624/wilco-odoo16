# Implementation Plan: Project Status Report

**Task**: T001 - Project Status Report  
**Created**: October 6, 2025  
**Complexity**: L3-High

## 🎯 Implementation Strategy

This plan follows a phased approach to build the Project Status Report feature, leveraging existing patterns from the customer invoice summary and vendor bill summary implementations.

---

## 📐 Technical Architecture

### Data Flow
```
Project Form View
    ↓
[Status Report Button]
    ↓
Wizard Model (Optional Parameters)
    ↓
Data Collection Method
    ↓
QWeb Report Template
    ↓
PDF Output / Screen View
```

### Data Sources
1. **Project Information**: `project.project` model
2. **Sales Orders**: `sale.order` filtered by `wilco_project_id`
3. **Customer Invoices**: `account.move` filtered by `wilco_project_id` + `move_type='out_invoice'`
4. **Vendor Bills**: `account.move` filtered by `wilco_project_id` + `move_type='in_invoice'`

### Security Considerations
- Use existing project security rules
- Respect record-level permissions
- Apply appropriate access groups for financial data

---

## 🔨 Phase 1: Wizard Model Implementation

**File**: `custom_addons/wilco_project/wizard/wilco_project_status_report_wizard.py`

### Model Definition
```python
class WilcoProjectStatusReportWizard(models.TransientModel):
    _name = 'wilco.project.status.report.wizard'
    _description = 'Project Status Report Wizard'
    
    # Fields
    project_id = fields.Many2one('project.project', string='Project', required=True)
    # Future enhancement fields can be added here (date filters, etc.)
```

### Data Collection Method
```python
def wilco_action_print_report(self):
    """Generate and display the project status report"""
    self.ensure_one()
    
    # Collect project data
    project = self.project_id
    
    # Collect sales orders
    sales_orders = self.env['sale.order'].search([
        ('wilco_project_id', '=', project.id)
    ], order='date_order desc')
    
    # Collect customer invoices
    customer_invoices = self.env['account.move'].search([
        ('wilco_project_id', '=', project.id),
        ('move_type', '=', 'out_invoice')
    ], order='invoice_date desc, name desc')
    
    # Collect vendor bills
    vendor_bills = self.env['account.move'].search([
        ('wilco_project_id', '=', project.id),
        ('move_type', '=', 'in_invoice')
    ], order='invoice_date desc, name desc')
    
    # Return report action
    return self.env.ref('wilco_project.action_report_project_status').report_action(
        self, data={
            'project_id': project.id,
            'sales_order_ids': sales_orders.ids,
            'customer_invoice_ids': customer_invoices.ids,
            'vendor_bill_ids': vendor_bills.ids,
        }
    )
```

### Calculations & Aggregations
- Sales orders: Total amount, settled amount, balance
- Customer invoices: Total amount, settled amount, balance  
- Vendor bills: Total amount, settled amount, balance
- Net position: (Customer invoices settled - Vendor bills settled)

---

## 🎨 Phase 2: QWeb Report Template

**File**: `custom_addons/wilco_project/report/project_status_report_template.xml`

### Report Structure

#### Section 1: Project Header
```xml
<!-- Project Information -->
<div class="page">
    <h2>Project Status Report</h2>
    
    <div class="row mt-4">
        <div class="col-6">
            <strong>Project Number:</strong> <span t-field="docs.project_id.name"/>
            <br/>
            <strong>Project Name:</strong> <span t-field="docs.project_id.wilco_project_name"/>
            <br/>
            <strong>Stage:</strong> <span t-field="docs.project_id.stage_id.name"/>
        </div>
        <div class="col-6">
            <strong>Award Date:</strong> <span t-field="docs.project_id.wilco_date_award"/>
            <br/>
            <strong>Status:</strong> <span t-field="docs.project_id.last_update_status"/>
            <br/>
            <strong>Report Date:</strong> <span t-esc="context_timestamp(datetime.datetime.now()).strftime('%Y-%m-%d')"/>
        </div>
    </div>
</div>
```

#### Section 2: Sales Orders Table
```xml
<h3 class="mt-4">Sales Orders</h3>
<table class="table table-sm">
    <thead>
        <tr>
            <th>Order #</th>
            <th>Date</th>
            <th>Customer</th>
            <th class="text-right">Amount</th>
            <th class="text-right">Invoiced</th>
            <th class="text-right">Balance</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
        <t t-foreach="sales_orders" t-as="order">
            <tr>
                <td><span t-field="order.name"/></td>
                <td><span t-field="order.date_order"/></td>
                <td><span t-field="order.partner_id.name"/></td>
                <td class="text-right"><span t-field="order.amount_total"/></td>
                <td class="text-right"><span t-field="order.wilco_amount_invoiced_total"/></td>
                <td class="text-right"><span t-field="order.wilco_amount_invoice_remainder"/></td>
                <td><span t-field="order.state"/></td>
            </tr>
        </t>
    </tbody>
    <tfoot>
        <tr>
            <td colspan="3"><strong>Total</strong></td>
            <td class="text-right"><strong t-esc="sum(sales_orders.mapped('amount_total'))"/></td>
            <td class="text-right"><strong t-esc="sum(sales_orders.mapped('wilco_amount_invoiced_total'))"/></td>
            <td class="text-right"><strong t-esc="sum(sales_orders.mapped('wilco_amount_invoice_remainder'))"/></td>
            <td></td>
        </tr>
    </tfoot>
</table>
```

#### Section 3: Customer Invoices Table
```xml
<h3 class="mt-4">Customer Invoices</h3>
<table class="table table-sm">
    <thead>
        <tr>
            <th>Invoice #</th>
            <th>Date</th>
            <th>Customer</th>
            <th class="text-right">Amount</th>
            <th class="text-right">Settled</th>
            <th class="text-right">Due</th>
            <th>Payment Date</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
        <t t-foreach="customer_invoices" t-as="invoice">
            <tr>
                <td><span t-field="invoice.name"/></td>
                <td><span t-field="invoice.invoice_date"/></td>
                <td><span t-field="invoice.partner_id.name"/></td>
                <td class="text-right"><span t-field="invoice.amount_total"/></td>
                <td class="text-right"><span t-field="invoice.wilco_amount_settled_total"/></td>
                <td class="text-right"><span t-field="invoice.amount_residual"/></td>
                <td><span t-field="invoice.wilco_payment_dates"/></td>
                <td><span t-field="invoice.payment_state"/></td>
            </tr>
        </t>
    </tbody>
    <tfoot>
        <tr>
            <td colspan="3"><strong>Total</strong></td>
            <td class="text-right"><strong t-esc="sum(customer_invoices.mapped('amount_total'))"/></td>
            <td class="text-right"><strong t-esc="sum(customer_invoices.mapped('wilco_amount_settled_total'))"/></td>
            <td class="text-right"><strong t-esc="sum(customer_invoices.mapped('amount_residual'))"/></td>
            <td colspan="2"></td>
        </tr>
    </tfoot>
</table>
```

#### Section 4: Vendor Bills Table
```xml
<h3 class="mt-4">Vendor Bills</h3>
<table class="table table-sm">
    <thead>
        <tr>
            <th>Bill #</th>
            <th>Date</th>
            <th>Vendor</th>
            <th class="text-right">Amount</th>
            <th class="text-right">Settled</th>
            <th class="text-right">Due</th>
            <th>Payment Date</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
        <t t-foreach="vendor_bills" t-as="bill">
            <tr>
                <td><span t-field="bill.name"/></td>
                <td><span t-field="bill.invoice_date"/></td>
                <td><span t-field="bill.partner_id.name"/></td>
                <td class="text-right"><span t-field="bill.amount_total"/></td>
                <td class="text-right"><span t-field="bill.wilco_amount_settled_total"/></td>
                <td class="text-right"><span t-field="bill.amount_residual"/></td>
                <td><span t-field="bill.wilco_payment_dates"/></td>
                <td><span t-field="bill.payment_state"/></td>
            </tr>
        </t>
    </tbody>
    <tfoot>
        <tr>
            <td colspan="3"><strong>Total</strong></td>
            <td class="text-right"><strong t-esc="sum(vendor_bills.mapped('amount_total'))"/></td>
            <td class="text-right"><strong t-esc="sum(vendor_bills.mapped('wilco_amount_settled_total'))"/></td>
            <td class="text-right"><strong t-esc="sum(vendor_bills.mapped('amount_residual'))"/></td>
            <td colspan="2"></td>
        </tr>
    </tfoot>
</table>
```

### Styling Considerations
- Use Bootstrap classes for responsive layout
- Follow existing Odoo report styling
- Ensure proper page breaks for PDF
- Add company header/footer using standard templates

---

## 📋 Phase 3: Report Actions & Views

### Report Action Definition

**File**: `custom_addons/wilco_project/report/project_status_report_views.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Report Definition -->
    <record id="action_report_project_status" model="ir.actions.report">
        <field name="name">Project Status Report</field>
        <field name="model">wilco.project.status.report.wizard</field>
        <field name="report_type">qweb-pdf</field>
        <field name="report_name">wilco_project.report_project_status_document</field>
        <field name="report_file">wilco_project.report_project_status_document</field>
        <field name="binding_model_id" ref="model_wilco_project_status_report_wizard"/>
        <field name="binding_type">report</field>
    </record>
</odoo>
```

### Wizard View Definition

**File**: `custom_addons/wilco_project/wizard/wilco_project_status_report_wizard_views.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Wizard Form View -->
    <record id="view_wilco_project_status_report_wizard_form" model="ir.ui.view">
        <field name="name">wilco.project.status.report.wizard.form</field>
        <field name="model">wilco.project.status.report.wizard</field>
        <field name="arch" type="xml">
            <form string="Project Status Report">
                <group>
                    <field name="project_id" invisible="1"/>
                </group>
                <footer>
                    <button name="wilco_action_print_report" string="Print Report" 
                            type="object" class="btn-primary"/>
                    <button string="Cancel" class="btn-secondary" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>

    <!-- Wizard Action -->
    <record id="action_wilco_project_status_report_wizard" model="ir.actions.act_window">
        <field name="name">Project Status Report</field>
        <field name="res_model">wilco.project.status.report.wizard</field>
        <field name="view_mode">form</field>
        <field name="target">new</field>
        <field name="binding_model_id" ref="project.model_project_project"/>
        <field name="binding_view_types">form</field>
    </record>
</odoo>
```

### Project Form View Button

**File**: `custom_addons/wilco_project/views/project_views_inherit.xml` (modify)

```xml
<!-- Add after existing stat buttons -->
<button class="oe_stat_button" 
        type="action"
        name="%(action_wilco_project_status_report_wizard)d"
        icon="fa-file-text-o">
    <div class="o_form_field o_stat_info">
        <span class="o_stat_text">Status</span>
        <span class="o_stat_text">Report</span>
    </div>
</button>
```

---

## 🔧 Phase 4: Module Integration

### Update __init__.py Files

**File**: `custom_addons/wilco_project/wizard/__init__.py`
```python
from . import wilco_project_status_report_wizard
```

**File**: `custom_addons/wilco_project/report/__init__.py` (if needed)
```python
# Import any Python report models if created
```

### Update __manifest__.py

**File**: `custom_addons/wilco_project/__manifest__.py`

Add to 'data' section:
```python
'data': [
    # ... existing entries ...
    'wizard/wilco_project_status_report_wizard_views.xml',
    'report/project_status_report_views.xml',
    'report/project_status_report_template.xml',
    # ... rest of entries ...
],
```

---

## ✅ Testing Strategy

### Test Cases

#### TC1: Basic Report Generation
- **Setup**: Create project with sales orders, invoices, and bills
- **Action**: Click Status Report button, print report
- **Expected**: PDF generates with all sections populated correctly

#### TC2: Empty Project
- **Setup**: Create project with no transactions
- **Action**: Generate report
- **Expected**: Report shows project info, empty tables with headers

#### TC3: Partial Data
- **Setup**: Project with only sales orders (no invoices/bills)
- **Action**: Generate report
- **Expected**: Sales orders section populated, others empty

#### TC4: Multi-currency
- **Setup**: Project with transactions in different currencies
- **Action**: Generate report
- **Expected**: Amounts display in their respective currencies

#### TC5: Large Data Set
- **Setup**: Project with 50+ transactions
- **Action**: Generate report
- **Expected**: Report generates successfully with pagination

#### TC6: Permission Testing
- **Setup**: User with limited project access
- **Action**: Attempt to generate report
- **Expected**: Only accessible projects shown, security respected

### Data Validation Checks
- ✅ All sales orders with matching `wilco_project_id` appear
- ✅ All customer invoices with matching `wilco_project_id` appear
- ✅ All vendor bills with matching `wilco_project_id` appear
- ✅ Totals calculated correctly
- ✅ Dates formatted properly
- ✅ Currency symbols display correctly

---

## ⚠️ Error Handling

### Potential Issues & Solutions

1. **Missing Project Data**
   - Check: Ensure project_id is always set in wizard
   - Handle: Raise user-friendly error if project missing

2. **Report Generation Timeout**
   - Monitor: Large data sets may cause slow rendering
   - Solution: Consider adding progress indicator or chunking

3. **Permission Errors**
   - Handle: Check user access before querying data
   - Display: Appropriate error message for access denied

4. **Data Inconsistencies**
   - Validate: Check for archived/deleted records
   - Filter: Exclude inactive records if appropriate

---

## 📊 Success Metrics

1. **Functionality**
   - ✅ Report accessible from project form
   - ✅ All required data sections present
   - ✅ PDF generation works correctly

2. **Performance**
   - ✅ Report generates in < 5 seconds for typical project
   - ✅ Handles projects with 100+ transactions

3. **User Experience**
   - ✅ Intuitive access via button
   - ✅ Clear, readable report layout
   - ✅ Professional PDF output

4. **Code Quality**
   - ✅ Follows Wilco naming conventions
   - ✅ Proper error handling
   - ✅ Well-commented code
   - ✅ No security vulnerabilities

---

## 🔄 Post-Implementation Tasks

1. **Documentation**
   - Update Memory Bank with implementation details
   - Document any deviations from plan
   - Add user guide if needed

2. **Code Review**
   - Self-review against coding standards
   - Check for optimization opportunities
   - Verify security best practices

3. **Update Task Status**
   - Mark task as completed in `task.md`
   - Update `tasks.md` index
   - Update `progress.md` with milestone

4. **Future Enhancement Notes**
   - Document potential improvements
   - Note any limitations discovered
   - Capture user feedback for v2

---

## 📚 Reference Implementation

### Similar Code Patterns

**Customer Invoice Summary Wizard** (`wilco_invoice_summary_wizard.py`):
- Data collection pattern
- Report action return format
- Error handling approach

**Vendor Bill Summary** (`wilco_vendor_bill_summary_wizard.py`):
- Wizard structure
- View integration
- Security model

**Existing QWeb Reports**:
- `sale_report_template.xml` - Styling reference
- `purchase_report_template.xml` - Table layout
- `invoice_report_inherit.xml` - Financial data display

---

## 🎓 Learning Notes

### Key Odoo Patterns Used
1. **Transient Models (Wizards)**: For report parameter gathering
2. **QWeb Templates**: For PDF report rendering
3. **Report Actions**: For PDF generation
4. **View Inheritance**: For button integration

### Wilco-Specific Patterns
1. **`wilco_` Prefix**: For all custom fields and methods
2. **Project-Based Architecture**: Central project model as hub
3. **Financial Integration**: Using existing settlement tracking
4. **Report Infrastructure**: Leveraging existing PDF framework
