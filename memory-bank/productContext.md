# PRODUCT CONTEXT

## Business Domain
- **Industry**: Enterprise Resource Planning (ERP)
- **Company**: Wilco
- **System**: Custom Odoo-based ERP solution
- **Version**: 16.0

## Core Business Functions
- **Accounting & Financial Management**
- **Vendor Bill Processing**
- **Purchase Management**
- **Reporting & Analytics**
- **Document Management**

## Recent Feature Development
- **Vendor Bill Summary**: New functionality for aggregating and reporting on vendor bills
  - Model: Vendor bill summary data structure
  - Views: User interface for bill summary management
  - Wizard: Guided processes for bill summary operations

## User Base
- Internal business users
- Accounting teams
- Financial analysts
- Management reporting staff

## Key Business Processes
1. Vendor bill processing and approval
2. Financial reporting and analysis
3. Purchase order management
4. Account distribution and tracking
5. Digital document signatures

## Integration Points
- PDF report generation
- Database backup automation
- Third-party accounting modules
- Digital signature workflows 
## Business Workflows

### Sales Process Workflow
1. **Project Creation**
   - Generate unique project number (no spaces)
   - Create descriptive project name
   - Auto-create analytic account if missing

2. **Sales Quotation/Order**
   - Link sales order to project
   - Configure budget cost tracking at line level
   - Set analytic distribution for all lines

3. **Invoice Generation**
   - Choose invoice method: by line or by order total
   - Maintain project links in invoice lines
   - Apply proper analytic distributions

4. **Payment Processing**
   - Track payments with analytic distributions
   - Update project financial KPIs
   - Monitor settlement status

### Purchase Process Workflow
1. **Purchase Order Creation**
   - Link purchase to project
   - Auto-distribute analytics to project accounts
   - Enable revision tracking with document numbers

2. **Invoice Verification**
   - Verify project assignments
   - Validate analytic distributions
   - Track budget vs actual costs

3. **Payment Processing**
   - Apply project-based payment tracking
   - Update expense tracking in project analytics

### Financial Reporting Workflows
1. **Enhanced Analytic Reports**
   - Project-based financial reporting
   - Profit tracking (gross and net)
   - Payment tracking with settlement dates

2. **Project Profitability Analysis**
   - Revenue vs expense tracking
   - Budget vs actual comparisons
   - Settlement status monitoring

3. **Customer & Vendor Bill Summaries**
   - Period-based aggregation
   - Multi-dimensional reporting (vendor, project, account)
   - Opening period consolidation
   - Bill breakdown drill-down capabilities

### Project Management Workflows
1. **Project Financial Tracking**
   - Real-time financial KPI monitoring
   - Receivables and payables tracking
   - Revenue and expense categorization

2. **Document Management**
   - Document approval workflows
   - Revision tracking and numbering
   - Project timeline visualization

3. **Reporting & Analytics**
   - Comprehensive project dashboards
   - Budget variance analysis
   - Profitability reporting
