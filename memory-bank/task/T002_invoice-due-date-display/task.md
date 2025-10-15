# Task T002: Invoice & Bill Due Date Display

## Task Information
- **Task ID**: T002
- **Title**: Add Due Date and Due Days to Invoice/Bill Views
- **Status**: In Progress
- **Priority**: Medium
- **Complexity**: L1-Simple
- **Created**: 2025-10-16
- **Last Updated**: 2025-10-16

## Description
Add visibility of Due Date and Days Remaining (Due Days as of today) in Customer Invoice and Vendor Bill tree views to help users quickly identify upcoming payment deadlines.

## Requirements
1. Display `invoice_date_due` (Due Date) in tree views
2. Add computed field `wilco_days_due` showing days until/overdue from today
3. Apply to both Customer Invoice and Vendor Bill views
4. Show positive numbers for future due dates, negative for overdue

## Implementation Plan

### Phase 1: Model Extension
- [x] Add `wilco_days_due` computed field to `account.move` model
- [x] Implement computation logic to calculate days from today to due date
- [x] Handle cases where `invoice_date_due` is not set

### Phase 2: View Updates
- [x] Update invoice tree view to show due date and due days
- [x] Add visual decorations (red for overdue, orange for due within 7 days)
- [x] Make fields optional/visible by default
- [x] Update Project Status Report - Customer Invoices section
- [x] Update Project Status Report - Vendor Bills section

### Phase 3: Testing
- [ ] Verify calculation with future due dates
- [ ] Verify calculation with overdue invoices
- [ ] Verify display in tree views
- [ ] Test visual decorations

## Technical Details

### Files Modified
- `custom_addons/wilco_project/models/account_move.py`
- `custom_addons/wilco_project/views/account_move_views_inherit.xml`
- `custom_addons/wilco_project/report/project_status_report_template.xml`

### Field Specifications
- **Field Name**: `wilco_days_due`
- **Type**: Integer (computed)
- **Dependencies**: `invoice_date_due`, `amount_residual`
- **Computation Logic**: 
  - Returns 0 if invoice/bill is fully paid (`amount_residual = 0`)
  - Returns `(invoice_date_due - today).days` if unpaid/partially paid and due date exists
  - Returns 0 if no due date is set
- **Display**: "Days Due"
- **Decorations**: 
  - Red (`decoration-danger`) for negative values (overdue)
  - Orange (`decoration-warning`) for 0-7 days (due soon)
  - Normal for fully paid (shows 0)

## Progress Log

### 2025-10-16
- Task created
- Implementation completed
- Added `wilco_days_due` computed field to `account_move` model
- Added `_wilco_compute_days_due` method with proper @api.depends decorator
- **Business Logic**: Field shows 0 when invoice/bill is fully paid (amount_residual = 0)
- Dependencies: `invoice_date_due` and `amount_residual` for proper recomputation
- Updated invoice tree view to display both `invoice_date_due` and `wilco_days_due`
- Added visual decorations for better UX (red for overdue, orange for due within 7 days)
- Updated Project Status Report template:
  - Added "Due Date" and "Days Due" columns to Customer Invoices section
  - Added "Due Date" and "Days Due" columns to Vendor Bills section
  - Added "Payment Terms" column to Customer Invoices section
  - Added "Payment Terms" column to Vendor Bills section
  - **Filter**: Only show Posted invoices/bills (state = 'posted')
  - Applied same visual styling (red for overdue, orange for due within 7 days)
  - Updated colspan values for empty/footer rows to match new column count (14 columns total)
- Ready for testing
