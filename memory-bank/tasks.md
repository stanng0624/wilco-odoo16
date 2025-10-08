## 📁 Task Organization

> **📖 Complete Task Organization Rules**: See [Task Organization Guidelines](../rules/task-organization.md) for comprehensive documentation.

### Quick Reference

All tasks are organized in the `task/` folder with a self-contained structure:

```
task/
└── TXXX_short-name/
    ├── task.md              # Required: Task tracking and status
    ├── plan.md              # Optional: Main implementation plan
    └── plan-XXX_*.md        # Optional: Detailed plan breakdowns
```

### Key Principles

**📂 Folder Structure**:
- **Format**: `TXXX_short-name` (e.g., `T001_customer-invoice-summary`)
- **Location**: `memory-bank/task/`
- **Self-Contained**: All task-related docs (including plans) live in task folder

**📝 Required Files**:
- `task.md` - Always required for tracking status and progress
- `plan.md` - Optional, create for tasks with complexity ≥ L2-Medium
- `plan-XXX_*.md` - Optional, for detailed breakdowns of complex tasks

**🔢 ID System**:
- **Next Task ID**: T001
- **Format**: Zero-padded 3 digits (T001, T002, ..., T999)
- **Plan Breakdowns**: Sequential per task (plan-001, plan-002, etc.)

**🔗 Linking Pattern**:
- Within task folder: `./plan.md`, `./plan-001_data-model.md`
- Between tasks: `../T008_core-integration/task.md`
- From index: `./task/T041_profitability/task.md`

> **⚠️ IMPORTANT**: 
> - See [Complete Rules](../rules/task-organization.md) for templates, workflows, and detailed guidelines
> - Always create `task.md` first - it's the anchor for all task documentation
> - Plans now live WITH tasks, not in separate plan/ folder
> - Use relative links within task folders for stability


# MEMORY BANK - TASKS

## Current Task Status
- **Status**: ACTIVE - Implementation Phase
- **Last Updated**: October 6, 2025
- **Mode**: BUILD MODE (Testing Pending)
- **Next Task ID**: T002

## Current Active Tasks

### 🎯 T001: Project Status Report
- **Status**: Implementation Complete - Testing Pending
- **Complexity**: L3-High
- **Priority**: Medium
- **Created**: 2025-10-06
- **Last Updated**: 2025-10-08
- **Description**: Create a comprehensive Project Status Report showing project information and all related sales orders, customer invoices, and vendor bills
- **Files**: [Task Details](./task/T001_project-status-report/task.md) | [Implementation Plan](./task/T001_project-status-report/plan.md)
- **Progress**:
  - ✅ Phase 1: Wizard Model - Complete
  - ✅ Phase 2: QWeb Report Template - Complete
  - ✅ Phase 3: Report Actions & Views - Complete
  - ✅ Module Upgrade - Successful
  - ✅ Phase 5: Invoice Form Integration - Complete (Oct 8)
  - ⏳ Phase 4: Manual Testing - Pending
- **Key Achievements**: 
  - Wizard model with data collection logic implemented
  - Comprehensive QWeb report template with all sections
  - Button integration in project form view
  - Button integration in customer invoice form view with auto-highlight feature
  - Security access configured
  - Module successfully upgraded

## Historical Tasks & Project Context

### ✅ Recently Completed Tasks

#### Vendor Bill Summary System (October 2025)
- **Impact**: Comprehensive vendor bill reporting system implemented
- **Status**: COMPLETED
- **Features**:
  - Complete model implementation (402 lines)
  - Multi-view system (search, tree, form)
  - Wizard interface for report generation
  - Security integration with access controls
  - Integration with Odoo accounting modules

#### Customer Invoice Summary System (June 2025)
- **Impact**: Comprehensive financial reporting system implemented
- **Features**:
  - Period-based reporting (monthly/yearly)
  - Opening period support for historical data consolidation
  - Multiple grouping options: by period, customer, project, or sales account
  - Invoice breakdown view showing individual invoice details
  - Running balance calculations (period_balance and total_sales_amount)
  - Down payment tracking and deduction reporting
  - Settlement tracking with payment dates
  - Quick access to related invoices, journal entries, and line items
  - Filtering by customer, project, and sales account
  - Customizable as-of-date for point-in-time reporting

#### Core Enhancements (April-May 2025)
- **Sale Order Invoice by Order Total**: Added ability to invoice entire order with single line
- **Project Reference Tracking**: Improved traceability of partner involvement in projects
- **Analytic Account Line Calculation**: Enhanced financial analysis with categorized amounts

### 🔄 Known Issues & Future Enhancements

#### Bug Fixes (Priority: Medium - Not Currently Active)
- [ ] **Sale Order Line Analytic Distribution Consistency**
  - Expected Impact: Ensure all sale order lines properly distribute analytics
  - Status: Identified, needs implementation

- [ ] **Invoice Deletion with Linked Sales Orders**  
  - Expected Impact: Prevent data integrity issues when invoices with sales order links are deleted
  - Status: Identified, needs implementation

#### Enhancements (Priority: Low - For Future Consideration)
- [x] **Vendor Bill Summary Settled Logic Alignment** (COMPLETED - December 2024)
  - Impact Achieved: Vendor bill summary now follows customer invoice summary pattern for settled fields
  - Status: Implementation complete - All field references updated consistently + settled calculation logic fixed
  - Complexity: Level 2 (Simple Enhancement)
  - Files Modified: wilco_vendor_bill_summary.py, wilco_vendor_bill_summary_views.xml, wilco_vendor_bill_summary_wizard.py
  - Changes Made:
    - Renamed `paid_amount` field to `settled_amount` in model and all references
    - Renamed `paid_dates` field to `settled_dates` in model and all references
    - Updated help text and labels from "Paid" to "Settled" throughout
    - Updated balance calculation help text to reflect new terminology
    - Renamed `_compute_paid_amount` method to `_compute_settled_amount` in wizard
    - Updated all view references in tree, form, and search views
    - **FIXED: Settled amount calculation logic** - Now checks both matched_credit_ids and matched_debit_ids, uses max_date instead of create_date, includes currency conversion
    - Verified syntax validity and XML structure
  - Result: Consistent settled logic pattern across both customer invoice and vendor bill summary systems with accurate settlement calculations

- [ ] **Project Analytic Reporting Performance**
  - Expected Impact: Speed up analytic reports for projects with many transactions
  - Related Discovery: Performance issue in _wilco_compute_amounts method
  - Status: Performance analysis needed

- [ ] **Bulk Project Assignment to Invoices**
  - Expected Impact: Allow users to update multiple invoices with project information
  - Status: Enhancement requested

- [ ] **Customer Invoice Summary Enhancement**
  - Expected Impact: Improve financial reporting with opening periods and date filtering
  - Status: Building on existing success

## Ready for New Tasks
The system is ready to accept new tasks. When creating a new task:
1. Use next sequential ID: **T001**
2. Create task folder: `memory-bank/task/T001_short-name/`
3. Create required `task.md` file
4. Follow templates in `memory-bank/rules/task-organization.md`
