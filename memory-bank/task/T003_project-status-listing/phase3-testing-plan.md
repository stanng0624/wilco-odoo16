# Phase 3 Testing Plan: Project Status Listing Report (T003)

**Date**: October 22, 2025  
**Phase**: Phase 3 - Testing & Refinement  
**Status**: Ready for Execution

## Test Environment Setup

### Prerequisites
- Odoo server running on `http://localhost:8069`
- Database: `wilco-odoo-dev`
- Module: `wilco_project` (upgraded)
- Test data: Multiple projects with various financial data

### Credentials
- Access role: Project User or higher
- Database: wilco-odoo-dev

---

## Test Scenarios

### Test Case 1: Menu Navigation & Access
**Objective**: Verify menu item appears in correct location and is accessible

**Steps**:
1. Navigate to Project module (`http://localhost:8069/web#action=...`)
2. Open the Reporting submenu under Projects
3. Verify "Project Status Listing Report" appears below "Project Status Report"
4. Click on the menu item
5. Verify report opens without errors

**Expected Results**:
- ✅ Menu item visible under Project > Reporting
- ✅ Menu positioned after Project Status Report
- ✅ Report opens in new page/tab without errors
- ✅ Report displays project data in table format

**Status**: [ ] Not Started  [ ] In Progress  [ ] Passed  [ ] Failed

**Notes**: 

---

### Test Case 2: Basic Report Rendering
**Objective**: Report renders successfully with all projects and columns

**Steps**:
1. Open Project Status Listing Report from menu
2. Observe report in browser (HTML view)
3. Check that:
   - Report title displays correctly
   - Report date shows current date
   - Company name appears
   - Project table displays
   - All column headers visible
4. Check browser console for JavaScript errors

**Expected Results**:
- ✅ Report loads without timeout errors
- ✅ Report title: "Project Status Listing Report"
- ✅ All 20 columns appear with proper headers
- ✅ No JavaScript errors in console
- ✅ Table responsive and readable in browser

**Status**: [ ] Not Started  [ ] In Progress  [ ] Passed  [ ] Failed

**Notes**: 

---

### Test Case 3: Project Data Display
**Objective**: All projects display in table with correct data

**Steps**:
1. Open Project Status Listing Report
2. Count number of rows in table
3. For 3-5 projects, verify:
   - Project Number displays correctly
   - Project Name displays correctly
   - Manager name displays correctly
   - Stage name displays correctly
   - Award date shows correctly (or "-" if not set)
   - Start/End dates display correctly (or "-" if not set)
4. Verify no duplicate rows
5. Verify no missing projects (compare with Project list view)

**Expected Results**:
- ✅ All active projects appear in table
- ✅ Project information accurate (number, name, manager, stage)
- ✅ Dates display in YYYY-MM-DD format
- ✅ Missing dates shown as "-"
- ✅ No duplicate or missing projects
- ✅ Row count matches active project count in database

**Status**: [ ] Not Started  [ ] In Progress  [ ] Passed  [ ] Failed

**Notes**: 

---

### Test Case 4: Financial Calculations Accuracy
**Objective**: Financial data calculations are accurate and match T001

**Steps**:
1. Select a project with complete financial data
2. Open Project Status Report (T001) for that project
3. Note the financial totals from T001:
   - Total Contract Sum
   - Total Invoice Amount
   - Total Budget Cost
   - Total Vendor Bill Amount
   - Total Cost & Expense
   - Estimated GP%
   - Project P&L
   - Actual Cash Flow
4. Open Project Status Listing Report
5. Find the same project in the listing table
6. Compare each financial value:
   - Contract Sum (column: "Contract Sum")
   - Invoice Amount (column: "Invoice Amt")
   - Budget Cost (column: "Budget Cost")
   - Vendor Bill Amount (column: "Vendor Bill")
   - Cost & Expense (column: "Cost & Exp")
   - GP% (column: "Est. GP%")
   - Project P&L (column: "Project P&L")
   - Cash Flow (column: "Cash Flow")

**Expected Results**:
- ✅ All financial values match T001 exactly
- ✅ Percentages calculated correctly
- ✅ Monetary amounts formatted consistently
- ✅ No rounding errors or discrepancies
- ✅ Currency symbols display correctly

**Status**: [ ] Not Started  [ ] In Progress  [ ] Passed  [ ] Failed

**Notes**: 

---

### Test Case 5: Percentage Calculations
**Objective**: All percentage columns calculate correctly

**Steps**:
1. For 3-5 projects in report, verify percentage calculations:
   - Invoice %: (Invoice Amount / Contract Sum) * 100
   - Bill %: (Vendor Bill / Budget Cost) * 100
   - CE %: (Cost & Expense / Budget Cost) * 100
   - Est. GP%: ((Contract Sum - Budget Cost) / Contract Sum) * 100
   - NP%: (Project P&L / Total Revenue) * 100
   - CF %: (Cash Flow / Invoice Amount) * 100
2. Calculate expected percentages manually
3. Compare with values in report

**Expected Results**:
- ✅ All percentages calculated correctly
- ✅ Percentages formatted with 2 decimal places
- ✅ Percentages display % symbol
- ✅ Division by zero handled gracefully (displays 0.00%)
- ✅ Negative percentages display correctly when applicable

**Status**: [ ] Not Started  [ ] In Progress  [ ] Passed  [ ] Failed

**Notes**: 

---

### Test Case 6: Edge Cases - Missing Data
**Objective**: Report handles missing/incomplete data gracefully

**Steps**:
1. Verify projects with no data in various scenarios:
   - Project with no sales orders
   - Project with no invoices
   - Project with no vendor bills
   - Project with no dates set
   - Project with no manager assigned
2. Check each row displays correctly with:
   - All monetary fields showing 0.00
   - All percentage fields showing 0.00%
   - Date fields showing "-"
   - Text fields showing empty or "-"

**Expected Results**:
- ✅ No errors or broken layout
- ✅ Missing data displays as "0.00" or "-"
- ✅ Rows with no data are readable and organized
- ✅ Table remains properly formatted

**Status**: [ ] Not Started  [ ] In Progress  [ ] Passed  [ ] Failed

**Notes**: 

---

### Test Case 7: PDF Export & Formatting
**Objective**: PDF export works and formats correctly

**Steps**:
1. Open Project Status Listing Report
2. Click "Print" button (or PDF export if available)
3. Select PDF format if prompted
4. Save or open PDF
5. Verify in PDF viewer:
   - Document orientation is landscape
   - All 20 columns visible on page
   - Table formatting intact
   - Font sizes readable (should be 9-10pt)
   - Column widths appropriate
   - No truncated data
   - Company branding/header visible
   - Report date visible
6. If multi-page:
   - Verify header repeats on each page
   - Verify page breaks logical
   - Verify page numbers correct

**Expected Results**:
- ✅ PDF generates without errors
- ✅ Landscape orientation applied
- ✅ All columns visible and readable
- ✅ Font sizes appropriate (9pt minimum)
- ✅ No data truncation or overlap
- ✅ Professional formatting maintained
- ✅ Multi-page documents have proper headers/footers

**Status**: [ ] Not Started  [ ] In Progress  [ ] Passed  [ ] Failed

**Notes**: 

---

### Test Case 8: Multi-Project Performance
**Objective**: Report performs acceptably with multiple projects

**Steps**:
1. Count projects in database (should have multiple)
2. Open Project Status Listing Report
3. Measure load time from menu click to full rendering
4. Measure time to generate PDF
5. Check server logs for errors or slow queries
6. Verify memory usage doesn't spike excessively

**Expected Results**:
- ✅ Report loads in < 5 seconds (normal portfolios: 10-50 projects)
- ✅ PDF generates in < 10 seconds
- ✅ No timeout errors
- ✅ Server logs show no errors
- ✅ Consistent performance across multiple runs
- ✅ Browser remains responsive

**Status**: [ ] Not Started  [ ] In Progress  [ ] Passed  [ ] Failed

**Notes**: 

---

### Test Case 9: Security & Permissions
**Objective**: Report respects user permissions and access controls

**Steps**:
1. Login as different user roles:
   - Admin user
   - Project Manager
   - Regular user
   - Sales user
2. For each role:
   - Verify menu item is accessible (or not if restricted)
   - Verify report opens or is denied based on permissions
   - Verify only accessible projects appear in report
3. Check project access rules are applied

**Expected Results**:
- ✅ Access control respected per user role
- ✅ Unauthorized users cannot access report
- ✅ Authorized users see appropriate project data
- ✅ Project-level access rules applied
- ✅ No security vulnerabilities or data leaks

**Status**: [ ] Not Started  [ ] In Progress  [ ] Passed  [ ] Failed

**Notes**: 

---

### Test Case 10: Data Consistency After Updates
**Objective**: Report reflects changes made to projects/invoices/bills

**Steps**:
1. Open Project Status Listing Report, note data for one project
2. Make changes to that project:
   - Add a new invoice
   - Add a vendor bill
   - Update project dates
   - Change project manager
3. Refresh report (or navigate away and back)
4. Verify updated data appears in report
5. Repeat with different change scenarios

**Expected Results**:
- ✅ Report reflects recent changes immediately
- ✅ New invoices/bills appear in financial totals
- ✅ Project information updates reflected
- ✅ Percentages recalculated correctly
- ✅ No stale data caching issues

**Status**: [ ] Not Started  [ ] In Progress  [ ] Passed  [ ] Failed

**Notes**: 

---

## Summary of Test Results

| Test Case | Description | Status | Notes |
|-----------|-------------|--------|-------|
| 1 | Menu Navigation & Access | [ ] | |
| 2 | Basic Report Rendering | [ ] | |
| 3 | Project Data Display | [ ] | |
| 4 | Financial Calculations | [ ] | |
| 5 | Percentage Calculations | [ ] | |
| 6 | Edge Cases - Missing Data | [ ] | |
| 7 | PDF Export & Formatting | [ ] | |
| 8 | Multi-Project Performance | [ ] | |
| 9 | Security & Permissions | [ ] | |
| 10 | Data Consistency | [ ] | |

**Overall Status**: [ ] All Pass  [ ] Some Pass  [ ] Multiple Failures  [ ] Not Started

**Overall Notes**: 

---

## Known Issues & Solutions

| Issue | Severity | Solution | Status |
|-------|----------|----------|--------|
| | | | |

---

## Recommendations for Future Enhancement

1. Add filtering parameters (date range, project stage, manager)
2. Implement pagination for very large project portfolios (100+ projects)
3. Add column sorting/filtering in template
4. Add export to Excel functionality
5. Add drill-down capability to individual project status reports
6. Add project portfolio totals row at bottom of table
7. Add color coding for financial metrics (red/green for performance)
8. Add comparison to previous period capabilities

---

**Test Plan Created**: October 22, 2025  
**Estimated Testing Time**: 1-2 hours  
**Next Step After Testing**: Document results and mark Phase 3 complete
