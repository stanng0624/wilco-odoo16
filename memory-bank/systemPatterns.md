# SYSTEM PATTERNS

## Odoo Development Patterns

### Module Structure Pattern
```
wilco_project/
├── __init__.py              # Module initialization
├── __manifest__.py          # Module manifest and dependencies
├── models/                  # Data models
├── views/                   # UI definitions (XML)
├── wizard/                  # User interaction wizards
├── report/                  # Reporting templates
├── security/                # Access control definitions
├── data/                    # Default data and configurations
└── static/                  # Static assets (CSS, JS, images)
```

### Model Definition Pattern
- Inherit from `models.Model` or extend existing models
- Define fields with appropriate types and constraints
- Implement business logic in model methods
- Follow Odoo naming conventions

### View Definition Pattern
- XML-based view definitions
- Inherit and extend existing views
- Maintain consistent UI patterns
- Use appropriate view types (form, tree, kanban, etc.)

### Security Pattern
- Access control via `ir.model.access.csv`
- Record rules for fine-grained permissions
- User groups and categories
- Field-level security where needed

### Data Management Pattern
- Use XML data files for default configurations
- Implement data fixes in separate modules/scripts
- External identifier management for referencing

## Current Implementation Patterns
- **Vendor Bill Summary**: Following standard Odoo model/view/wizard pattern
- **Security Integration**: Proper access control definitions
- **Reporting**: Integration with existing PDF reporting infrastructure 
## Wilco Project Management Architecture

### Core Model Extensions

#### Project Model (project.project)
- **Field Customizations:**
  - Renamed "name" field to "Project Number"
  - Added "wilco_project_name" for descriptive project names
  - Enhanced project status tracking with customized status options

#### Analytic Accounts (account.analytic.account)
- **Project Integration:**
  - Direct link to projects via wilco_project_id
  - Extended to track financial KPIs (receivables, payables, revenue, expenses)
  - Profit tracking (gross/net profit calculations)

#### Sales & Purchasing Extensions
- **Custom Invoice Methods:**
  - invoice_by_line method for line-by-line invoicing
  - invoice_by_order method for total order invoicing
  - Budget cost tracking at line item level
  - Revision tracking with document numbering

#### Financial Integration
- **Analytic Distribution:**
  - Automatic analytic distribution from projects
  - Enhanced payment tracking with project allocation
  - Specialized financial reporting (aged analytics)

### Naming Conventions & Guidelines

#### Field Naming Standards
- **Standard Fields**: Keep Odoo naming conventions
- **Extended Fields**: Use `wilco_` prefix (e.g., `wilco_project_name`)
- **Computation Methods**: Use `_wilco_compute_` prefix
- **Action Methods**: Use `wilco_action_` prefix

#### Model Extension Patterns
- Extend existing models where possible
- Document model relationships in method comments
- Maintain analytic distribution consistency

#### Development Guidelines
- **Code Organization**: Separate business logic into clear methods
- **Computed Fields**: Use computed fields with dependencies for derived values
- **Security**: Respect Odoo's record rules and access controls
- **Project-based Security**: Implement project-based security for financial data

### Utility Modules

#### External Identifier Utility
- **Purpose**: Manages consistent external identifiers across models
- **Features**: 
  - Prevents duplicates
  - Enforces naming conventions
  - Maintains referential integrity

#### Data Fixers
- **Sale Order Invoice Link Fixer**: Resolves missing links between invoices and sales orders
- **Maintenance Utilities**: Data consistency verification and repair tools

### Financial Data Structure Conventions

#### Clear Financial Separation
- **Revenue vs Income**: Distinct tracking and reporting
- **Cost vs Expense**: Proper categorization
- **Gross Profit vs Net Profit**: Accurate calculation methods

#### Project Financial Structure
- **Project Number**: Primary identifier (no spaces allowed)
- **Project Name**: Descriptive title for display
- **Analytic Account**: Auto-created if missing during project creation
- **Project Stage & Status**: Enhanced tracking with custom status options
