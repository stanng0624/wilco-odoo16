# Wilco Project Management - Architecture & Planning

## 📋 Overview
The Wilco Project Management add-on extends Odoo 16's project management capabilities with specialized financial tracking, enhanced analytics, and document management features tailored for project-based businesses.

## 🏗️ Architecture

### Core Models & Extensions
- **Project (project.project)**
  - Renamed "name" field to "Project Number"
  - Added "wilco_project_name" for descriptive project names
  - Enhanced project status tracking with customized status options

- **Analytic Accounts (account.analytic.account)**
  - Direct link to projects via wilco_project_id
  - Extended to track financial KPIs (receivables, payables, revenue, expenses)
  - Profit tracking (gross/net profit calculations)

- **Sales & Purchasing**
  - Custom invoice methods (invoice_by_line, invoice_by_order)
  - Budget cost tracking at line item level
  - Revision tracking with document numbering

- **Financial Integration**
  - Automatic analytic distribution from projects
  - Enhanced payment tracking with project allocation
  - Specialized financial reporting (aged analytics)

### Utility Modules
- **External Identifier Utility**
  - Manages consistent external identifiers across models
  - Prevents duplicates and enforces naming conventions

### Data Fixers
- **Sale Order Invoice Link Fixer**
  - Resolves missing links between invoices and sales orders
  - Maintenance utility for data consistency

## 🔄 Workflows

### Sales Process
1. Project creation with unique project number
2. Sales quotation/order linked to project
3. Budget cost tracking at line level
4. Invoice generation (by line or by order total)
5. Payment tracking with analytic distributions

### Purchase Process
1. Purchase linked to project
2. Auto-distribution of analytics
3. Revision tracking with document numbers
4. Invoice verification with project assignments

### Financial Reporting
1. Enhanced analytic reports by project
2. Profit tracking (gross/net)
3. Payment tracking with dates
4. Settlement status monitoring

## 📊 Data Structures

### Project Structure
- Project Number (primary identifier, no spaces allowed)
- Project Name (descriptive title)
- Analytic Account (auto-created if missing)
- Project Stage & Status (enhanced tracking)

### Financial Structure
- Clear separation between:
  - Revenue vs Income
  - Cost vs Expense
  - Gross Profit vs Net Profit

## 🧩 Naming Conventions

### Fields
- **Standard Fields**: Keep Odoo naming
- **Extended Fields**: Use `wilco_` prefix (e.g., `wilco_project_name`)
- **Computation Methods**: Use `_wilco_compute_` prefix
- **Action Methods**: Use `wilco_action_` prefix

### Models
- Extend existing models where possible
- Document model relationships in method comments

## 🔧 Development Guidelines

### Code Organization
- Separate business logic into clear methods
- Use computed fields with dependencies for derived values
- Maintain analytic distribution consistency

### Security Considerations
- Respect Odoo's record rules and access controls
- Project-based security for financial data

### Extension Points
- Payment registration customization
- Document workflow enhancement
- Report customization