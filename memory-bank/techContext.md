# TECHNICAL CONTEXT

## Technology Stack
- **Framework**: Odoo 16.0
- **Language**: Python 3.11.11
- **Database**: PostgreSQL (implied)
- **Web Server**: Nginx (configured)
- **Platform**: macOS Darwin (arm64 architecture)
- **Shell**: /bin/zsh

## Development Environment
- **Shell**: /bin/zsh
- **Workspace**: `/Users/Workspace/Development/workspace/odoo/wilco-odoo/16.0`
- **Git**: Repository with active changes

## Project Structure
```
16.0/
├── custom_addons/wilco_project/    # Main custom module
├── third_party_addons/             # External Odoo modules
├── conf/                           # Configuration files
├── odoo/                          # Core Odoo framework
└── memory-bank/                   # Project memory system
```

## Active Modules
- **wilco_project**: Main custom ERP module
- **accounting_pdf_reports**: Financial reporting
- **auto_backup**: Database backup automation
- **om_account_***: Various accounting modules
- **signature**: Digital signature support

## Current Development Focus
- Vendor bill summary functionality
- Recent model/view/wizard additions
- Security access configurations 
## Wilco Data Structures & Integration

### Core Data Relationships

#### Project Data Structure
```
project.project
├── project_number (primary identifier, no spaces)
├── wilco_project_name (descriptive title)
├── analytic_account_ids (one-to-many relationship)
└── stage_id (enhanced project status tracking)
```

#### Analytic Account Integration
```
account.analytic.account
├── wilco_project_id (many-to-one to project.project)
├── receivable_amount (computed KPI)
├── payable_amount (computed KPI)  
├── revenue_amount (computed KPI)
├── expense_amount (computed KPI)
├── gross_profit (computed)
└── net_profit (computed)
```

#### Financial Integration Patterns
- **Automatic Analytic Distribution**: Sales/purchase orders auto-populate project analytics
- **Payment Tracking**: Enhanced payment registration with project allocation
- **Multi-dimensional Reporting**: Vendor/customer bill summaries with project breakdown

### Security Considerations
- **Project-based Security**: Financial data isolated by project access
- **Record Rules**: Odoo's built-in access control respected
- **User Permissions**: Role-based access to financial reporting

### Extension Points
- **Payment Registration Customization**: Enhanced payment workflows
- **Document Workflow Enhancement**: Approval and revision tracking  
- **Report Customization**: Flexible financial reporting framework

### Integration Mechanisms
- **Analytic Distribution**: Automatic project assignment from sales/purchase
- **Financial KPI Computation**: Real-time calculation of project metrics
- **Data Consistency**: Utility modules ensure referential integrity
