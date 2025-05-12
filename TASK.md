# Wilco Project Management - Task Tracking

## 🔄 Current Tasks

### Bug Fixes
- [ ] Fix sale order line analytic distribution consistency
  - **Date**: May 10, 2025
  - **Dependencies**: None
  - **Expected Impact**: Ensure all sale order lines properly distribute analytics

- [ ] Address invoice deletion with linked sales orders
  - **Date**: May 10, 2025
  - **Dependencies**: None
  - **Expected Impact**: Prevent data integrity issues when invoices with sales order links are deleted

### Enhancements
- [ ] Improve project analytic reporting performance
  - **Date**: May 10, 2025
  - **Dependencies**: None
  - **Expected Impact**: Speed up analytic reports for projects with many transactions

- [ ] Add bulk project assignment capability to invoices
  - **Date**: May 10, 2025
  - **Dependencies**: None
  - **Expected Impact**: Allow users to update multiple invoices with project information

- [ ] Enhance Customer Invoice Summary report with opening period and date filtering
  - **Date**: May 12, 2025
  - **Dependencies**: Customer Invoice Summary report
  - **Expected Impact**: Improve financial reporting by allowing users to define opening periods and prevent generating periods after as-of-date

### New Features
- [ ] Create project profitability dashboard
  - **Date**: May 10, 2025
  - **Dependencies**: Enhanced analytic computation
  - **Expected Impact**: Visual representation of project financial performance

- [ ] Implement project budget vs actual comparison report
  - **Date**: May 10, 2025
  - **Dependencies**: Budget cost tracking
  - **Expected Impact**: Provide variance analysis for project managers

- [ ] Implement Customer Invoice Summary report
  - **Date**: May 10, 2025
  - **Dependencies**: Account module
  - **Expected Impact**: Provide financial overview of customer invoices with settled amounts and balances as of a specified date

## ✅ Completed Tasks

- [x] Implement sale order invoice by order total capability
  - **Date**: April 15, 2025
  - **Impact**: Added ability to invoice entire order with single line

- [x] Add project reference tracking in partner records
  - **Date**: April 10, 2025
  - **Impact**: Improved traceability of partner involvement in projects

- [x] Create analytic account line amount calculation
  - **Date**: April 5, 2025
  - **Impact**: Enhanced financial analysis with categorized amounts

## 🔍 Discovered During Work

- [ ] Need consistent behavior for wilco_project_id propagation
  - **Date**: May 8, 2025
  - **Related To**: "Address invoice deletion with linked sales orders"
  - **Notes**: Project IDs sometimes aren't properly maintained across related documents

- [ ] Performance issue in _wilco_compute_amounts method
  - **Date**: May 7, 2025
  - **Related To**: "Improve project analytic reporting performance"
  - **Notes**: Computation becomes slow with large number of analytic lines

## 📆 Planned Tasks

- [ ] Implement document approval workflow
  - **Date**: May 20, 2025
  - **Dependencies**: None
  - **Expected Impact**: Add formal approval steps to project documents

- [ ] Create project timeline visualization
  - **Date**: June 1, 2025
  - **Dependencies**: None
  - **Expected Impact**: Visual representation of project milestones and progress