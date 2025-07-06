# Wilco ERP - Odoo 16.0 Development Environment

A comprehensive Enterprise Resource Planning (ERP) system built on Odoo 16.0, designed for project-based businesses with advanced financial tracking, reporting, and document management capabilities.

## 🚀 Overview

Wilco ERP is a custom Odoo-based solution that provides integrated project management, financial tracking, and reporting capabilities. The system is designed to handle complex business workflows including sales processing, purchase management, accounting, and comprehensive project profitability analysis.

## 🎯 Core Features

### Project Management
- **Project Creation**: Unique project numbering and auto-creation of analytic accounts
- **Financial KPI Tracking**: Real-time monitoring of project financials
- **Document Management**: Revision tracking and approval workflows
- **Timeline Visualization**: Project progress and milestone tracking

### Financial Management
- **Advanced Accounting**: Integration with multiple accounting modules
- **Budget Tracking**: Budget vs actual analysis at project and line levels
- **Payment Processing**: Comprehensive payment tracking with analytic distributions
- **Financial Reporting**: Enhanced reports with profit tracking and settlement monitoring

### Sales & Purchase Management
- **Sales Workflow**: Quotation to invoice with project linking
- **Purchase Orders**: Project-based purchasing with analytic distribution
- **Invoice Management**: Flexible invoicing methods (by line or order total)
- **Vendor Bill Processing**: Automated bill processing and approval workflows

### Reporting & Analytics
- **Project Profitability**: Revenue vs expense tracking with budget comparisons
- **Customer & Vendor Summaries**: Period-based aggregation and drill-down capabilities
- **Analytic Reports**: Multi-dimensional reporting across projects, vendors, and accounts
- **Dashboard Views**: Comprehensive project and financial dashboards

## 📦 Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.8+
- PostgreSQL 12+

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd wilco-odoo
   ```

2. **Build and run with Docker**
   ```bash
   docker-compose -f conf/docker/stack.yaml up -d
   ```

3. **Access the application**
   - Web interface: http://localhost:8069
   - Default credentials: admin/admin

### Manual Installation

1. **Install Odoo 16.0**
   ```bash
   # Follow Odoo 16.0 installation guide for your OS
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r custom_addons/requirements.txt
   ```

3. **Configure Odoo**
   - Copy appropriate config file from `conf/` directory
   - macOS: `odoo16-macos.conf`
   - Ubuntu: `odoo16-ubuntu.conf`
   - Docker: `odoo16-docker.conf`

4. **Start Odoo**
   ```bash
   ./odoo-bin -c conf/odoo16-[platform].conf
   ```

## ⚙️ Configuration

### Environment-Specific Configurations

| Environment | Config File | Description |
|-------------|-------------|-------------|
| macOS | `conf/odoo16-macos.conf` | Local development on macOS |
| Ubuntu | `conf/odoo16-ubuntu.conf` | Linux server deployment |
| Docker | `conf/odoo16-docker.conf` | Containerized deployment |
| Nginx | `conf/odoo_nginx.conf` | Nginx proxy configuration |

### Database Configuration
- Configure PostgreSQL connection in your chosen config file
- Default database: `wilco_erp`
- Ensure proper user permissions and encoding (UTF-8)

## 🔧 Development

### Project Structure
```
wilco-odoo/
├── custom_addons/           # Custom Wilco modules
│   └── wilco_project/       # Main project management module
├── third_party_addons/      # Third-party Odoo addons
├── conf/                    # Configuration files
├── docs/                    # Project documentation
├── memory-bank/             # Development documentation
├── odoo/                    # Odoo core (submodule)
└── logs/                    # Application logs
```

### Custom Modules

#### Wilco Project (`custom_addons/wilco_project/`)
The main custom module providing:
- Project management enhancements
- Financial tracking and reporting
- Custom views and wizards
- Document management
- Enhanced reporting templates

### Third-Party Addons

| Module | Purpose |
|--------|---------|
| `accounting_pdf_reports` | Enhanced PDF financial reports |
| `auto_database_backup` | Automated database backups |
| `muk_web_theme` | Modern UI theme |
| `om_account_*` | Accounting and financial modules |
| `om_hr_payroll*` | HR and payroll management |
| `purchase_discount` | Purchase discount management |
| `signature` | Digital signature support |

## 🚀 Usage

### Getting Started
1. **Login**: Access the web interface with admin credentials
2. **Setup Company**: Configure your company information
3. **Create Projects**: Set up your first project with analytic accounts
4. **Configure Users**: Add team members and assign permissions

### Key Workflows

#### Project Creation
1. Navigate to Projects → Create New
2. Enter project name (unique number will be auto-generated)
3. System auto-creates linked analytic account
4. Configure budget and tracking parameters

#### Sales Process
1. Create Quotation linked to project
2. Configure analytic distribution
3. Convert to Sale Order
4. Generate invoices (by line or total)
5. Process payments with project tracking

#### Financial Reporting
1. Navigate to Reports → Project Profitability
2. Select date range and projects
3. Review budget vs actual analysis
4. Export reports as needed

## 🔍 Monitoring & Logs

### Log Files
- Application logs: `logs/`
- Error tracking: Check Odoo interface under Settings → Technical → Logging

### Health Checks
- Database connectivity
- File system permissions
- Third-party addon compatibility

## 🛡️ Security

### Access Control
- Role-based permissions
- Project-specific access controls
- Document approval workflows
- Audit trail for financial transactions

### Data Protection
- Automated database backups
- File storage security
- User session management

## 📚 Documentation

### Additional Resources
- Project documentation: `docs/TVP/`
- Development notes: `memory-bank/`
- Technical specifications: Available in module docstrings

## 🤝 Contributing

### Development Guidelines
1. Follow Odoo development best practices
2. Use consistent naming conventions
3. Document all custom models and methods
4. Test thoroughly before deployment

### Code Style
- Python: PEP 8 compliance
- XML: Proper indentation and structure
- JavaScript: ES6+ standards

## 📄 License

This project is licensed under LGPL-3 - see the LICENSE file for details.

## 🆘 Support

For technical support or feature requests:
1. Check existing documentation
2. Review log files for error details
3. Contact development team

## 🔄 Version History

- **v1.0.0**: Initial release with core project management and financial tracking
- Enhanced vendor bill processing
- Comprehensive reporting suite
- Docker deployment support

---

**Note**: This is a development environment. For production deployment, ensure proper security configurations, regular backups, and performance optimization.
