# Task T003: Project Status Listing Report

**Created**: October 22, 2025  
**Status**: 🎯 Planning - Ready for Implementation
**Complexity**: L3-High  
**Priority**: High

## 📋 Overview

Create a comprehensive Project Status Listing Report that displays all projects in a table/list format with key project information and financial summary columns. This listing report will provide a dashboard view of all active/relevant projects with their financial status, enabling quick comparison and analysis across the project portfolio.

The report will combine information from:
- **Project Information Section**: Project Number, Project Name, Project Manager, Stage, Award Date, Planned Dates
- **Project Financial Summary**: Contract Sum, Invoice Amount, Budget Cost, Vendor Bill Amount, Cost & Expense, GP%, P&L, Cash Flow

## 🎯 Requirements

### Functional Requirements

1. **List View with All Projects**
   - Display all projects (filtered by company if needed)
   - One row per project with all key financial metrics
   - Enable sorting and filtering capabilities
   - Sortable columns for easy analysis

2. **Project Information Columns**
   - Project Number (wilco_project_id or name field)
   - Project Name (wilco_project_name)
   - Project Manager (user_id)
   - Stage (stage_id)
   - Award Date (wilco_date_award)
   - Planned Start Date (date_start)
   - Planned End Date (date)

3. **Project Financial Summary Columns**
   - Total Contract Sum (A) - Sum of confirmed sales orders
   - Total Invoice Amount (B) - Sum of customer invoices
   - Invoice % (B/A) - Invoicing progress percentage
   - Total Budget Cost (C) - Sum of budgeted costs from sales orders
   - Total Vendor Bill Amount (D) - Sum of vendor bills for project
   - Vendor Bill % (D/C) - Budget consumption percentage
   - Total Cost & Expense (E) - From analytic lines
   - Cost & Expense % (E/C) - Cost consumption percentage
   - Estimated GP% (F) - (A-C)/A * 100
   - Project P&L (G) - Net profit from analytic distribution
   - Actual NP% - Net profit percentage
   - Actual Cash Flow (H) - Net payment from analytic distribution
   - Cash Flow % (H/B) - Cash collection percentage

4. **Report Access & Actions**
   - Accessible from Projects menu
   - Printable PDF export option
   - On-screen list view with export capabilities
   - Optional: Drill-down to individual project status report (T001)

5. **Data Filtering & Selection**
   - Filter by project stage (if applicable)
   - Filter by date range (award date or project dates)
   - Filter by project manager
   - Export to spreadsheet/PDF
   - Company-based filtering (multi-company support)

### Technical Requirements

- Follow Wilco naming conventions (`wilco_` prefix for custom fields/methods)
- Use existing project.project model (no new model needed for listing)
- Leverage account.analytic.line for financial calculations (reuse T001 logic)
- Implement as report accessible through menu or action button
- Support both on-screen and PDF output
- Maintain consistent security and access controls
- Efficient query optimization for large project portfolios

## 🏗️ Architecture Decisions

### Report Implementation Pattern
**Decision**: Implement as a Report Action (ir.actions.report) + QWeb Template  
**Rationale**:
- Simpler than wizard for list view without filtering parameters
- Can add wizard layer later for filtering if needed
- Follows standard Odoo report patterns
- Provides both on-screen and PDF output
- Avoids transient model complexity for non-parameterized report

### Data Retrieval Strategy
**Decision**: Use project.project model search with pre-computed field aggregations in QWeb template  
**Rationale**:
- Reuse financial calculation logic from T001 project status report
- Query project records once, calculate summaries per-project in template
- Efficient for moderate project counts (typical SME portfolios: 10-100 projects)
- Template-level calculations match existing T001 pattern for consistency

### Report Template Type
**Decision**: Single QWeb template with project row iteration  
**Rationale**:
- Single table with sortable columns
- No page breaks for full portfolio view (user can page in browser/PDF)
- Responsive design for screen and print
- Cleaner than wizard-based approach

## 🧩 Components Affected

### Existing Components
1. **project.project Model** (extended)
   - No new fields needed, leverage existing extensions from T001
   - Use existing computed fields and methods

2. **account.analytic.line Model** (referenced)
   - Reuse existing `wilco_amount_*` fields for financial calculations
   - Leverage existing analytic distribution logic

3. **sale.order Model** (referenced)
   - Use `wilco_project_id` and `wilco_amount_budget_cost_total` fields
   - Query confirmed sales orders (state in ['sale', 'done'])

4. **account.move Model** (referenced)
   - Query customer invoices and vendor bills by project
   - Handle analytic distribution for bills without direct project_id

### New Components to Create

1. **Report Template File**
   - `report/project_status_listing_template.xml`
   - QWeb template for rendering project listing with financial columns

2. **Report Action**
   - Register in `__manifest__.py` or via XML data file
   - Link report to menu action
   - Define report action in module

3. **Menu Item (Optional)**
   - Add menu entry under Reports for quick access
   - Or integrate into existing project reports menu

4. **Security/Access** (if needed)
   - Verify `ir.model.access.csv` includes report access
   - Use existing project model access controls

## 📊 Implementation Strategy

### Phase 1: Report Template Creation
- Create QWeb template with project iteration
- Implement project information columns
- Implement financial summary columns with calculations
- Apply styling consistent with existing reports

### Phase 2: Report Action Registration
- Register report action in manifest or XML
- Configure PDF export settings
- Link to menu or project view action

### Phase 3: Testing & Refinement
- Test with multiple projects
- Verify financial calculations accuracy
- Test PDF export formatting
- Test permission/security access

### Phase 4: Optimization (if needed)
- Profile query performance
- Add filtering/parameters if required
- Consider caching strategies for large portfolios

## 🔄 Dependencies

### Internal Dependencies
- **T001 Project Status Report**: Pattern reference and financial calculation logic reuse
- **wilco_project module**: Existing model extensions and utilities

### External Dependencies
- Odoo reporting infrastructure (QWeb, PDF generation)
- Existing accounting modules (account.analytic.line, account.move)

## ⚠️ Challenges & Mitigations

| Challenge | Mitigation |
|-----------|-----------|
| Complex financial calculations | Reuse proven logic from T001 project status report |
| Large dataset performance | Optimize QWeb template, consider pagination or filtering |
| Column alignment in PDF | Use fixed-width table design, test multiple formats |
| Multi-currency handling | Leverage company currency from project.company_id |
| Decimal precision | Use Odoo's monetary widget and currency formatting |
| Analytic line filtering complexity | Document logic clearly, test edge cases |

## ✅ Acceptance Criteria

- [ ] Report displays all active projects in list format
- [ ] All project information columns display correctly
- [ ] All financial summary columns calculate correctly and match T001 logic
- [ ] Financial totals sum to project portfolio totals
- [ ] PDF export works with proper formatting
- [ ] Report is accessible from Projects menu
- [ ] Data updates reflect changes in projects, orders, and invoices
- [ ] No permission/security issues
- [ ] Performance acceptable for typical project portfolios (< 5 seconds load time)

## 📝 Implementation Notes

### Calculation Logic to Reuse from T001

The following calculation patterns from T001 should be reused:

1. **Sales Orders Query**: 
   ```
   search([('wilco_project_id', '=', project_id), ('state', 'in', ['sale', 'done'])])
   ```

2. **Analytic Lines Query**:
   ```
   search([('account_id', '=', project.analytic_account_id.id)])
   ```

3. **Customer Invoices Query**:
   ```
   search([('wilco_project_id', '=', project_id), ('move_type', '=', 'out_invoice'), ('state', 'not in', ['draft', 'cancel'])])
   ```

4. **Vendor Bills Query** (handles both direct project link and analytic distribution)

5. **Financial Totals Calculations**:
   - header_total_contract_sum = sum(sales_orders.mapped('amount_total'))
   - header_total_budget_cost = sum(sales_orders.mapped('wilco_amount_budget_cost_total'))
   - header_total_invoice_amount = sum(invoices.mapped('amount_total'))
   - header_total_vendor_bill_amount = (complex logic handling both direct project link and analytic distribution)
   - header_total_net_profit = sum(analytic_lines.mapped('wilco_amount_net_profit'))
   - Percentages and other derived calculations

### QWeb Template Structure

```
project_status_listing_template.xml
├── Root template call wrapper
├── HTML container structure
├── Page header (title, date, company info)
├── Table header with column definitions
├── Loop through project.project records
│   ├── For each project: 
│   │   ├── Set variables for financial calculations
│   │   ├── Query related records
│   │   ├── Calculate aggregated financial values
│   │   ├── Render project row with all columns
├── Table footer (optional: portfolio totals)
└── Style definitions (CSS for print/screen)
```

## � Implementation Notes

### Calculation Logic to Reuse from T001

The following calculation patterns from T001 should be reused:

## 🔗 Related Documentation

- **T001 Project Status Report**: [Task Details](../T001_project-status-report/task.md) - Reference implementation
- **Plan Document**: [Implementation Plan](./plan.md) - Detailed implementation strategy
- **Plan Adjustments**: [Plan Adjustments Summary](./PLAN_ADJUSTMENTS.md) - October 22 refinements
- **System Patterns**: [Naming Conventions & Guidelines](../../systemPatterns.md)
- **Product Context**: [Project Management Architecture](../../productContext.md)
- **Technical Context**: [Data Structures & Integration](../../techContext.md)

## 📌 Progress Log

### 2025-10-22
- ✅ Task created in PLAN mode
- ✅ Analyzed T001 project status report pattern
- ✅ Defined requirements and architecture
- ✅ Documented implementation strategy
- ✅ Plan adjustments for menu location and report folder organization
- ⏳ Next: Proceed to CREATIVE/IMPLEMENT mode

---

**Task Owner**: Development Team  
**Last Updated**: October 22, 2025  
**Mode**: PLAN MODE - Ready for CREATIVE/IMPLEMENT transition
