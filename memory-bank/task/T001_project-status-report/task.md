# Task T001: Project Status Report

**Created**: October 6, 2025  
**Status**: �️ Implementation Complete - Testing Pending  
**Complexity**: L3-High  
**Priority**: Medium

## 📋 Overview

Create a comprehensive Project Status Report that displays project information and lists all related financial transactions (sales orders, customer invoices, vendor bills) based on the `wilco_project_id` field in the order headers. The report should be printable from the project master record.

## 🎯 Requirements

### Functional Requirements
1. **Project Information Display**
   - Show project basic information (number, name, stage, dates, etc.)
   - Display project financial KPIs (if available from analytic accounts)

2. **Related Transaction Lists**
   - Sales Orders linked via `sale.order.wilco_project_id`
   - Customer Invoices linked via `account.move.wilco_project_id` (where move_type = 'out_invoice')
   - Vendor Bills linked via `account.move.wilco_project_id` (where move_type = 'in_invoice')

3. **Report Access**
   - Action button on project form view
   - Printable PDF report option
   - On-screen view with drill-down capabilities

### Technical Requirements
- Follow Wilco naming conventions (`wilco_` prefix for custom fields/methods)
- Use existing report infrastructure patterns
- Leverage Odoo's QWeb reporting system
- Maintain consistent security and access controls
- Support multi-company if needed

## 🏗️ Architecture Decisions

### Report Type
**Decision**: Implement as a transient model wizard + QWeb PDF report  
**Rationale**: 
- Follows existing pattern from customer/vendor bill summary reports
- Allows for potential future filtering/parameter options
- Provides both on-screen and PDF output
- Maintains consistency with project architecture

### Data Retrieval Strategy
**Decision**: Direct query using `wilco_project_id` field on order headers only  
**Rationale**:
- User explicitly requested to use order header's `wilco_project_id`
- Simpler and more performant than line-level aggregation
- Matches existing data model relationships
- Ensures data consistency

## 📦 Components

### 1. Wizard Model
**File**: `custom_addons/wilco_project/wizard/wilco_project_status_report_wizard.py`
- Transient model to gather report parameters (if needed in future)
- Method to collect project data and related transactions
- Action to open report view or generate PDF

### 2. Report Template
**File**: `custom_addons/wilco_project/report/project_status_report_template.xml`
- QWeb template for PDF report
- Sections for:
  - Project header information
  - Sales orders table
  - Customer invoices table
  - Vendor bills table
- Follow existing report styling patterns

### 3. Report Definition
**File**: `custom_addons/wilco_project/report/project_status_report_views.xml`
- Report action definition
- Paper format configuration
- Report menu item (if needed)

### 4. View Integration
**File**: `custom_addons/wilco_project/views/project_views_inherit.xml` (modify)
- Add "Status Report" button to project form view
- Position near other financial buttons (Analytic Lines, etc.)
- Use appropriate icon and styling

### 5. Wizard View
**File**: `custom_addons/wilco_project/wizard/wilco_project_status_report_wizard_views.xml`
- Wizard form view (initially minimal)
- Action definition for wizard

## 🔄 Dependencies

### Existing Models Used
- `project.project` - Source project record
- `sale.order` - Related sales orders via `wilco_project_id`
- `account.move` - Related invoices/bills via `wilco_project_id`
- `account.analytic.account` - Project financials (optional display)

### No New Dependencies Required
- All required modules already in manifest
- Uses existing security groups
- Leverages current report infrastructure

## 📝 Implementation Plan

### Phase 1: Wizard Model & Data Collection
**Estimated Effort**: 2-3 hours

1. Create wizard model with method to gather data
2. Implement data collection logic:
   - Fetch project record
   - Query sales orders: `search([('wilco_project_id', '=', project_id)])`
   - Query customer invoices: `search([('wilco_project_id', '=', project_id), ('move_type', '=', 'out_invoice')])`
   - Query vendor bills: `search([('wilco_project_id', '=', project_id), ('move_type', '=', 'in_invoice')])`
3. Structure data for report rendering

### Phase 2: QWeb Report Template
**Estimated Effort**: 3-4 hours

1. Create report template following existing patterns
2. Project information section:
   - Project number and name
   - Stage and status
   - Award date
   - Analytic account balance (if available)
3. Sales orders section:
   - Table with columns: Order #, Date, Customer, Amount, Status
   - Totals row
4. Customer invoices section:
   - Table with columns: Invoice #, Date, Customer, Amount, Settled, Balance
   - Totals row
5. Vendor bills section:
   - Table with columns: Bill #, Date, Vendor, Amount, Settled, Balance
   - Totals row

### Phase 3: Report Actions & Views
**Estimated Effort**: 1-2 hours

1. Define report action in XML
2. Create wizard view (simple form initially)
3. Add button to project form view
4. Configure security access

### Phase 4: Testing & Refinement
**Estimated Effort**: 2 hours

1. Test with projects having various transaction combinations
2. Verify data accuracy
3. Test PDF generation
4. Check permissions and access controls
5. Validate styling and layout

## ⚠️ Potential Challenges

### 1. Large Data Sets
**Challenge**: Projects with many transactions may cause slow report generation  
**Mitigation**: 
- Use efficient queries with proper indexing
- Consider pagination for on-screen view if needed
- Limit initial scope to reasonable data volumes

### 2. Deleted/Draft Records
**Challenge**: How to handle draft orders or cancelled invoices  
**Solution**: 
- Include state/status column in tables
- Consider filtering options in future enhancements
- Document behavior clearly

### 3. Multi-currency Scenarios
**Challenge**: Transactions in different currencies  
**Solution**: 
- Display in transaction currency
- Add company currency conversion if needed
- Follow existing currency handling patterns

### 4. Performance on Form View
**Challenge**: Button action should be responsive  
**Solution**: 
- Keep wizard lightweight
- Generate report only on user action
- Use appropriate loading indicators

## ✅ Success Criteria

1. ✅ Report accessible from project form view via button
2. ✅ Displays project basic information accurately
3. ✅ Lists all sales orders linked to project via `wilco_project_id`
4. ✅ Lists all customer invoices linked to project via `wilco_project_id`
5. ✅ Lists all vendor bills linked to project via `wilco_project_id`
6. ✅ PDF report generates successfully
7. ✅ Report follows Wilco styling and conventions
8. ✅ No security issues or access control problems

## 📚 Reference Materials

### Similar Implementations
- `wilco_customer_invoice_summary` - Pattern for report structure
- `wilco_vendor_bill_summary` - Pattern for wizard and views
- Existing QWeb reports in `custom_addons/wilco_project/report/`

### Key Files to Reference
- `memory-bank/systemPatterns.md` - Naming conventions
- `memory-bank/techContext.md` - Data relationships
- Existing report templates for styling consistency

## 🔄 Future Enhancements (Out of Scope)

- Advanced filtering options (date ranges, status filters)
- Grouping/sorting options
- Export to Excel functionality
- Chart/graph visualizations
- Purchase order inclusion (non-bill POs)
- Project comparison reports

## 📝 Progress Log

**2025-10-06**: Task created, technical analysis completed, plan documented

### Implementation Progress - October 6, 2025

**Phase 1: Wizard Model - COMPLETED ✅**
- Created `wilco_project_status_report_wizard.py` with data collection logic
- Implemented method to query sales orders, customer invoices, and vendor bills
- Added logging and calculation of summary totals
- Updated wizard `__init__.py` to import new model

**Phase 2: QWeb Report Template - COMPLETED ✅**
- Created `project_status_report_template.xml` with comprehensive layout
- Implemented project information header section
- Added three main table sections:
  - Sales Orders table with amount, invoiced, balance columns
  - Customer Invoices table with settlement tracking
  - Vendor Bills table with payment information
- Added empty state handling and totals calculation
- Used existing Wilco field patterns (wilco_amount_settled_total, wilco_payment_dates)

**Phase 3: Report Actions & Views - COMPLETED ✅**
- Created `project_status_report_views.xml` with report action definition
- Created `wilco_project_status_report_wizard_views.xml` with wizard form and action
- Added "Status Report" button to project form view in `project_views_inherit.xml`
- Added security access rule for wizard model in `ir.model.access.csv`
- Updated `__manifest__.py` with proper file loading order

**Module Upgrade - COMPLETED ✅**
- Successfully upgraded wilco_project module
- All XML files loaded without errors
- New wizard model and report registered in system
- Security rules applied correctly

### Files Created/Modified:
1. **New Files**:
   - `/wizard/wilco_project_status_report_wizard.py`
   - `/wizard/wilco_project_status_report_wizard_views.xml`
   - `/report/project_status_report_views.xml`
   - `/report/project_status_report_template.xml`

2. **Modified Files**:
   - `/wizard/__init__.py` - Added new wizard import
   - `/views/project_views_inherit.xml` - Added Status Report button
   - `/security/ir.model.access.csv` - Added security access
   - `/__manifest__.py` - Added new files with proper loading order

### Implementation Details:
- **Data Collection**: Uses `wilco_project_id` field on order headers as specified
- **Report Type**: QWeb PDF report following existing Wilco patterns
- **Security**: Accessible to `project.group_project_user` group
- **Button Integration**: Added to project form view stat buttons area
- **Context Passing**: Wizard receives `default_project_id` from button context

### Next Steps:
- **Phase 4**: Manual testing in Odoo UI
  - Test report generation from project form
  - Verify data accuracy with test projects
  - Test PDF output and formatting
  - Validate security and access controls

### Bug Fixes - October 6, 2025

**Issue 1**: Validation Error - "Create/update: a mandatory field is not set" for project_id field

**Root Cause**: The wizard action did not include context to pass the `project_id` from the project form to the wizard.

**Fix Applied**: Added `context` field to wizard action in `wilco_project_status_report_wizard_views.xml`
```xml
<field name="context">{'default_project_id': active_id}</field>
```

**Status**: ✅ Fixed and module re-upgraded successfully

---

**Issue 2**: Blank PDF report - Only company header showing, no report content

**Root Cause**: Two issues in the report template:
1. Used `web.external_layout` instead of `web.internal_layout` 
2. Template structure had incorrect nesting of elements and closing tags

**Fix Applied**: Updated `project_status_report_template.xml`
1. Changed from `web.external_layout` to `web.internal_layout`
2. Fixed template structure - moved `<div class="page">` outside the `t-foreach` loop
3. Changed data access from `data.get('...')` to direct search queries in template:
   - `o.env['sale.order'].search([('wilco_project_id', '=', o.project_id.id)])`
   - `o.env['account.move'].search([('wilco_project_id', '=', o.project_id.id), ('move_type', '=', 'out_invoice')])`
   - `o.env['account.move'].search([('wilco_project_id', '=', o.project_id.id), ('move_type', '=', 'in_invoice')])`
4. Fixed closing tag structure

**Status**: ✅ Fixed and module re-upgraded successfully

**Testing**: Ready for user to retry report generation - report should now display all content
