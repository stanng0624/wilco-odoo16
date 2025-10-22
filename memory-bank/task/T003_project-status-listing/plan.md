# Implementation Plan: Project Status Listing Report (T003)

**Date Created**: October 22, 2025  
**Complexity Level**: L3-High  
**Plan Type**: Comprehensive Implementation Plan

## 📋 Plan Overview

This document outlines the detailed implementation strategy for the Project Status Listing Report. The report will display all projects in a table format with columns from both the Project Information Section and Project Financial Summary, enabling portfolio-level analysis of project finances and performance.

**Menu Location**: Project > Reporting > Project Status Listing Report (below Project Status Report)

**File Organization**: Following Odoo standards, all report files (actions and templates) are placed in the `report/` folder.

---

## 🎯 Phase 1: Report Template Creation

### Step 1.1: Create QWeb Template File

**File**: `custom_addons/wilco_project/report/project_status_listing_report_template.xml`

**Template Structure**:
1. Root `<template>` with ID `report_project_status_listing_document`
2. HTML container wrapper with company branding
3. Page header section
4. Main table with project records
5. CSS styling for print and screen

**Key Sections**:

#### Header Section
- Report title: "Project Status Listing Report"
- Report date: Current date/time
- Company information
- Report filters applied (if any, for future use)

#### Table Structure
```
Column Groups:
├── Project Identification (Project Number, Name, Manager, Stage)
├── Project Timeline (Award Date, Start Date, End Date)
├── Contract & Revenue (Contract Sum, Invoice Amount, Invoice %)
├── Budget & Costs (Budget Cost, Vendor Bill Amount, Bill %, Cost & Expense %)
├── Financial Performance (Estimated GP%, Project P&L, Actual NP%)
└── Cash Flow (Actual Cash Flow, Cash Flow %)
```

#### Per-Project Row Logic
For each project in `docs` (from report data):
1. Query sales orders with `wilco_project_id = project.id`
2. Query analytic lines with `account_id = project.analytic_account_id.id`
3. Query customer invoices with `wilco_project_id = project.id`
4. Query vendor bills (with complex analytic distribution logic)
5. Calculate financial totals using same logic as T001
6. Render row with all columns

### Step 1.2: Template Implementation Details

**Financial Calculation Variables** (per project):

```xml
<!-- Sales Orders & Analytic Data -->
<t t-set="sales_orders" t-value="o.env['sale.order'].search([('wilco_project_id', '=', o.id), ('state', 'in', ['sale', 'done'])])"/>
<t t-set="analytic_lines" t-value="o.env['account.analytic.line'].search([('account_id', '=', o.analytic_account_id.id)])"/>

<!-- Contract Sum & Costs -->
<t t-set="total_contract_sum" t-value="sum(sales_orders.mapped('amount_total'))"/>
<t t-set="total_budget_cost" t-value="sum(sales_orders.mapped('wilco_amount_budget_cost_total'))"/>

<!-- Invoicing -->
<t t-set="invoices" t-value="o.env['account.move'].search([('wilco_project_id', '=', o.id), ('move_type', '=', 'out_invoice'), ('state', 'not in', ['draft', 'cancel'])])"/>
<t t-set="total_invoice_amount" t-value="sum(invoices.mapped('amount_total'))"/>
<t t-set="invoice_percent" t-value="(total_invoice_amount / total_contract_sum * 100) if total_contract_sum != 0 else 0"/>

<!-- Vendor Bills (complex logic) -->
<!-- Get bills with direct project link -->
<t t-set="vendor_bills_with_project" t-value="o.env['account.move'].search([('wilco_project_id', '=', o.id), ('move_type', 'in', ['in_invoice', 'in_refund']), ('state', 'not in', ['draft', 'cancel']), ('expense_sheet_id', '=', False)])"/>

<!-- Get bills without project link but with matching analytic distribution -->
<t t-set="analytic_account_str" t-value="str(o.analytic_account_id.id) if o.analytic_account_id else ''"/>
<t t-set="vendor_bills_no_project" t-value="o.env['account.move'].search([('wilco_project_id', '=', False), ('move_type', 'in', ['in_invoice', 'in_refund']), ('state', 'not in', ['draft', 'cancel']), ('expense_sheet_id', '=', False)])"/>

<!-- Filter bills with matching analytic distribution -->
<t t-set="vendor_bills_with_analytic" t-value="o.env['account.move']"/>
<t t-foreach="vendor_bills_no_project" t-as="bill">
  <t t-if="any(line.analytic_distribution and analytic_account_str in line.analytic_distribution for line in bill.invoice_line_ids)">
    <t t-set="vendor_bills_with_analytic" t-value="vendor_bills_with_analytic | bill"/>
  </t>
</t>

<!-- Combine both recordsets -->
<t t-set="vendor_bills" t-value="vendor_bills_with_project | vendor_bills_with_analytic"/>

<!-- Calculate total vendor bill amount -->
<t t-set="total_vendor_bill_amount" t-value="0.0"/>
<t t-foreach="vendor_bills" t-as="bill">
  <t t-if="bill.wilco_project_id">
    <t t-set="total_vendor_bill_amount" t-value="total_vendor_bill_amount + bill.amount_total"/>
  </t>
  <t t-else="">
    <t t-set="bill_amount_for_project" t-value="sum([line.price_total for line in bill.invoice_line_ids if line.analytic_distribution and analytic_account_str in line.analytic_distribution])"/>
    <t t-set="total_vendor_bill_amount" t-value="total_vendor_bill_amount + bill_amount_for_project"/>
  </t>
</t>

<!-- Cost & Expense -->
<t t-set="total_cost_expense" t-value="sum([line.wilco_amount_cost + line.wilco_amount_expense for line in analytic_lines])"/>
<t t-set="cost_expense_percent" t-value="(total_cost_expense / total_budget_cost * 100) if total_budget_cost != 0 else 0"/>
<t t-set="vendor_bill_percent" t-value="(total_vendor_bill_amount / total_budget_cost * 100) if total_budget_cost != 0 else 0"/>

<!-- Profit & Performance -->
<t t-set="total_net_profit" t-value="sum(analytic_lines.mapped('wilco_amount_net_profit'))"/>
<t t-set="total_revenue" t-value="sum(analytic_lines.mapped('wilco_amount_revenue'))"/>
<t t-set="estimated_gp_percent" t-value="((total_contract_sum - total_budget_cost) / total_contract_sum * 100) if total_contract_sum != 0 else 0"/>
<t t-set="actual_np_percent" t-value="(total_net_profit / total_revenue * 100) if total_revenue != 0 else 0"/>

<!-- Cash Flow -->
<t t-set="total_net_payment" t-value="sum(analytic_lines.mapped('wilco_amount_payment_display'))"/>
<t t-set="cash_flow_percent" t-value="(total_net_payment / total_invoice_amount * 100) if total_invoice_amount != 0 else 0"/>
```

**Table Columns** (in order):

| Column | Field/Calculation | Data Type | Format |
|--------|------------------|-----------|--------|
| Project Number | o.name | Text | -12 (left align) |
| Project Name | o.wilco_project_name | Text | -30 (left align) |
| Project Manager | o.user_id.name | Text | -20 (left align) |
| Stage | o.stage_id.name | Text | -15 (left align) |
| Award Date | o.wilco_date_award | Date | YYYY-MM-DD |
| Start Date | o.date_start | Date | YYYY-MM-DD |
| End Date | o.date | Date | YYYY-MM-DD |
| Contract Sum | total_contract_sum | Monetary | Currency formatted |
| Invoice Amount | total_invoice_amount | Monetary | Currency formatted |
| Invoice % | invoice_percent | Percent | ##.##% |
| Budget Cost | total_budget_cost | Monetary | Currency formatted |
| Vendor Bill | total_vendor_bill_amount | Monetary | Currency formatted |
| Bill % | vendor_bill_percent | Percent | ##.##% |
| Cost & Expense | total_cost_expense | Monetary | Currency formatted |
| CE % | cost_expense_percent | Percent | ##.##% |
| Est. GP% | estimated_gp_percent | Percent | ##.##% |
| Project P&L | total_net_profit | Monetary | Currency formatted |
| NP% | actual_np_percent | Percent | ##.##% |
| Cash Flow | total_net_payment | Monetary | Currency formatted |
| CF % | cash_flow_percent | Percent | ##.##% |

### Step 1.3: Styling Considerations

**CSS Classes & Styling**:
- Use Bootstrap 5 classes for responsive design
- Table classes: `table table-sm table-bordered o_main_table`
- Header row: `table-light` background
- Data alignment: Monetary/percent columns right-aligned
- Color coding (optional):
  - Negative GP%: Red background warning
  - High NP%: Green background success
  - Pending/incomplete: Yellow/orange warning

**Print Optimization**:
- Page orientation: Landscape (many columns)
- Font size: 10-11pt for readability
- Margin: 0.5 inch
- Header repeat on page breaks
- Hide filters/controls in print

---

## 🎯 Phase 2: Report Action and Menu Registration

### Step 2.1: Report Action Definition

**File**: `custom_addons/wilco_project/report/project_status_listing_report_views.xml`

Following Odoo standard conventions, report actions should be placed in the `report/` folder alongside the template.

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Report Definition -->
    <record id="action_report_project_status_listing" model="ir.actions.report">
        <field name="name">Project Status Listing Report</field>
        <field name="model">project.project</field>
        <field name="report_type">qweb-html</field>
        <field name="report_name">wilco_project.report_project_status_listing_document</field>
        <field name="report_file">wilco_project.report_project_status_listing_document</field>
        <field name="binding_model_id" ref="project.model_project_project"/>
        <field name="binding_type">report</field>
    </record>

    <!-- Menu Item under Project > Reporting (below Project Status Report) -->
    <menuitem id="wilco_menu_project_report_status_listing"
              name="Project Status Listing Report"
              action="wilco_project.action_report_project_status_listing"
              parent="project.menu_project_report"
              sequence="110"/>
</odoo>
```

**Note**: 
- Menu item is placed directly in the action file (standard Odoo practice)
- `parent="project.menu_project_report"` places it under Project > Reporting menu
- `sequence="110"` positions it below Project Status Report (which has sequence="100")
- Action reference uses module prefix: `wilco_project.action_report_project_status_listing`

### Step 2.2: Manifest Configuration

**File**: `custom_addons/wilco_project/__manifest__.py`

Add the new report files to the `data` list in the proper section:

```python
'data': [
    # ... existing entries ...
    
    # Reports (in report/ folder)
    'report/project_status_report_views.xml',          # Existing (T001)
    'report/project_status_report_template.xml',       # Existing (T001)
    'report/project_status_listing_report_views.xml',  # New (T003) - Action & Menu
    'report/project_status_listing_report_template.xml', # New (T003) - Template
    
    # ... other entries ...
],
```

---

## 🎯 Phase 3: Integration & Testing Setup

### Step 3.1: Module Update Requirements

After adding the new files, the module must be updated in Odoo:

**Via Odoo UI**:
1. Navigate to Apps menu
2. Remove "Apps" filter
3. Search for "Wilco Project"
4. Click "Upgrade" button

**Via Command Line**:
```bash
conda activate wilco-odoo16
./odoo/odoo-bin -c conf/odoo16-macos.conf -d wilco-odoo-dev -u wilco_project --stop-after-init
```

### Step 3.2: Security Access Verification

**File**: `custom_addons/wilco_project/security/ir.model.access.csv`

Verify that users have read access to `project.project` model. The report inherits permissions from the model.

```csv
"id","name","model_id:id","group_id:id","perm_read","perm_write","perm_create","perm_unlink"
"access_project_project_user","project.project user","project.model_project_project","base.group_user",1,0,0,0
```

**Note**: This entry typically already exists in the base `project` module, so no modification is usually needed.

---

## 🎯 Phase 4: Testing Strategy

### Test Case 1: Menu Navigation & Access
- **Objective**: Verify menu item appears in correct location
- **Steps**:
  1. Navigate to Project module
  2. Go to Reporting menu
  3. Verify "Project Status Listing Report" appears below "Project Status Report"
  4. Check sequence order (should be 110, after 100)
- **Success Criteria**: Menu item visible in correct position

### Test Case 2: Basic Report Rendering
- **Objective**: Report generates without errors
- **Steps**:
  1. Click "Project Status Listing Report" from menu
  2. Verify report opens in browser
  3. Check for template errors in log
  4. Generate PDF version
- **Success Criteria**: Report renders successfully with all projects displayed

### Test Case 3: Data Accuracy
- **Objective**: Financial calculations match T001 project status report
- **Steps**:
  1. Select a project with known data
  2. Run T001 (Project Status Report) for that project
  3. Run T003 (Project Status Listing Report)
  4. Compare financial totals for the same project
- **Success Criteria**: All calculations match exactly between reports

### Test Case 4: Multi-Project Display
- **Objective**: Multiple projects display correctly in table
- **Steps**:
  1. Ensure database has 5-10 active projects with varying data
  2. Run listing report
  3. Verify all projects appear in table
  4. Check row formatting and alignment
  5. Verify no overlapping or truncated data
- **Success Criteria**: All projects visible with proper formatting

### Test Case 5: PDF Export & Layout
- **Objective**: PDF layout and formatting work correctly
- **Steps**:
  1. Generate PDF from on-screen report
  2. Verify landscape orientation
  3. Check column alignment and readability
  4. Verify page breaks and header repeat on multi-page PDFs
  5. Check font sizes and spacing
- **Success Criteria**: PDF readable with proper formatting, landscape orientation

### Test Case 6: Performance
- **Objective**: Report generates in acceptable time
- **Steps**:
  1. Load report with 50+ projects
  2. Measure load time from menu click to render
  3. Check database query log for optimization opportunities
  4. Verify no timeout errors
- **Success Criteria**: Report loads in < 5 seconds for typical portfolio (50 projects)

### Test Case 7: Permissions & Security
- **Objective**: Report respects user permissions
- **Steps**:
  1. Login as different user roles (Project Manager, User, Admin)
  2. Verify menu visibility for each role
  3. Check project visibility (should respect project access rules)
  4. Verify access denied for unauthorized users
- **Success Criteria**: Access control working correctly per role

### Test Case 8: Edge Cases
- **Objective**: Handle edge cases gracefully
- **Steps**:
  1. Test with projects having no sales orders
  2. Test with projects having no vendor bills
  3. Test with projects having zero contract sum
  4. Test with archived/cancelled projects
- **Success Criteria**: No errors, proper handling of missing/zero data

---

## 🔄 Implementation Details by File

### Files to Create

1. **report/project_status_listing_report_template.xml**
   - QWeb template for listing report
   - Financial calculation logic
   - Table structure and styling
   - ~300-400 lines of code

2. **report/project_status_listing_report_views.xml**
   - Report action configuration (`ir.actions.report`)
   - Menu item definition under `project.menu_project_report`
   - Positioned below Project Status Report (sequence 110)
   - ~30 lines of code

### Files to Modify

1. **__manifest__.py**
   - Add both new report files to 'data' list
   - Place in the reports section after existing project status report entries
   - ~2 lines added

### File Structure Verification

After implementation, the report folder should contain:
```
custom_addons/wilco_project/report/
├── project_status_report_views.xml         (T001 - Existing)
├── project_status_report_template.xml      (T001 - Existing)
├── project_status_listing_report_views.xml    (T003 - NEW)
└── project_status_listing_report_template.xml (T003 - NEW)
```

**Note**: All report-related files (both actions and templates) are kept in the `report/` folder following standard Odoo conventions.

---

## 📊 Column Mapping Reference

### Project Information (from project.project)
- Project Number: `project.name`
- Project Name: `project.wilco_project_name`
- Project Manager: `project.user_id.name`
- Stage: `project.stage_id.name`
- Award Date: `project.wilco_date_award`
- Start Date: `project.date_start`
- End Date: `project.date`
- Company: `project.company_id.name` (implicit from currency)

### Financial Summary (calculated per project)

**Revenue & Invoicing**:
- Total Contract Sum: sum(sales_orders.amount_total) where state in ['sale', 'done']
- Total Invoice Amount: sum(invoices.amount_total) where move_type='out_invoice'
- Invoice %: (Total Invoice / Total Contract Sum) * 100

**Budget & Costs**:
- Total Budget Cost: sum(sales_orders.wilco_amount_budget_cost_total)
- Total Vendor Bill: Complex calculation handling both direct project link and analytic distribution
- Bill %: (Total Vendor Bill / Total Budget Cost) * 100
- Cost & Expense: sum([line.wilco_amount_cost + line.wilco_amount_expense for analytic_lines])
- CE %: (Cost & Expense / Total Budget Cost) * 100

**Performance Metrics**:
- Estimated GP%: ((Total Contract Sum - Total Budget Cost) / Total Contract Sum) * 100
- Project P&L: sum(analytic_lines.wilco_amount_net_profit)
- Actual NP%: (Project P&L / Total Revenue) * 100

**Cash Flow**:
- Actual Cash Flow: sum(analytic_lines.wilco_amount_payment_display)
- CF %: (Actual Cash Flow / Total Invoice Amount) * 100

---

## ⚡ Optimization Notes

### Query Optimization
1. Minimize database queries per project row
2. Use `mapped()` for field aggregations
3. Consider query batching for large project lists

### Template Optimization
1. Pre-calculate all values before rendering
2. Use t-set variables to avoid recalculation
3. Minimize nested loops

### Future Enhancements
1. Add filtering parameters (date range, project stage, manager)
2. Implement pagination for large portfolios
3. Add export to Excel functionality
4. Add sorting capabilities
5. Add drill-down to individual project reports

---

## 📋 Implementation Checklist

- [ ] Create `report/project_status_listing_report_template.xml`
- [ ] Define all financial calculation variables in template
- [ ] Create table with all required columns
- [ ] Apply styling and formatting
- [ ] Create `report/project_status_listing_report_views.xml` with:
  - [ ] Report action (`ir.actions.report`)
  - [ ] Menu item under `project.menu_project_report` with sequence 110
- [ ] Update `__manifest__.py`:
  - [ ] Add `report/project_status_listing_report_views.xml` to data list
  - [ ] Add `report/project_status_listing_report_template.xml` to data list
- [ ] Upgrade `wilco_project` module in Odoo
- [ ] Verify menu appears under Project > Reporting (below Project Status Report)
- [ ] Test report generation (on-screen)
- [ ] Test PDF export and formatting
- [ ] Test financial calculation accuracy vs T001
- [ ] Test with multiple projects (5-10 projects)
- [ ] Test performance with large dataset (50+ projects)
- [ ] Verify permissions and access control
- [ ] Document report usage (if needed)

---

## 🔗 Related Resources

- **T001 Project Status Report**: Reference implementation with same financial logic
- **Odoo QWeb Reporting**: Odoo framework documentation
- **Wilco Project Architecture**: System patterns and naming conventions
- **Financial Calculation Patterns**: T001 implementation details

---

**Plan Version**: 1.0  
**Last Updated**: October 22, 2025  
**Status**: Ready for Implementation
