from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class WilcoCustomerInvoiceSummary(models.Model):
    _name = 'wilco.customer.invoice.summary'
    _description = 'Customer Invoice Summary Report'
    _order = 'is_opening desc, year asc, month asc'

    year = fields.Integer(string='Year', readonly=True)
    month = fields.Integer(string='Month', readonly=True)
    month_name = fields.Char(string='Month Name', compute='_wilco_compute_month_name', store=True)
    period = fields.Char(string='Period', compute='_compute_period', store=True, 
                       help="Period in YYYY-MM format for easy grouping")
    invoice_count = fields.Integer(string='No of Invoice', readonly=True)
    sales_amount = fields.Monetary(string='Sales', currency_field='company_currency_id', readonly=True)
    total_sales_amount = fields.Monetary(string='Total Sales', currency_field='company_currency_id', readonly=True, 
                                       help="Accumulated sales from previous periods including current period")
    settled_amount = fields.Monetary(string='Settled', currency_field='company_currency_id', readonly=True)
    balance = fields.Monetary(string='Balance', currency_field='company_currency_id', readonly=True)
    is_opening = fields.Boolean(string='Is Opening Period', default=False, 
                              help="Indicates this is an opening period record with consolidated previous activity")
    description = fields.Char(string='Description', readonly=True,
                            help="Additional description for opening period records")
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    
    # For filtering
    as_of_date = fields.Date(string='As Of Date')
    partner_id = fields.Many2one('res.partner', string='Customer')
    
    @api.depends('year', 'month', 'is_opening', 'description')
    def _compute_period(self):
        """
        Compute the period in YYYY-MM format for easy grouping.
        For opening periods:
          - Historical opening: YYYY-MM (1: Historical)
          - Regular opening: YYYY-MM (2: Opening)
        For first regular period (January):
          - YYYY-MM (3: First period)
        For other regular periods:
          - YYYY-MM
        """
        for record in self:
            # Format as YYYY-MM for all records
            period_string = f"{record.year}-{record.month:02d}"
            
            if record.is_opening:
                # Check if this is a historical opening or regular opening record
                if record.description and 'Historical' in record.description:
                    record.period = f"{period_string} (1: Historical)"  # Historical opening
                else:
                    record.period = f"{period_string} (2: Opening)"  # Regular opening
            else:
                # First regular month (January) gets special naming
                if record.month == 1 and not record.is_opening:
                    record.period = f"{period_string} (3: First period)"
                else:
                    record.period = period_string
    
    def name_get(self):
        """
        Return a better display name for the customer invoice summary records.
        
        Format:
        - If customer exists: "[Month Year] Customer Name"
        - If no customer: "[Month Year] All Customers"
        """
        result = []
        for record in self:
            # Get customer name if exists
            customer_name = record.partner_id.name if record.partner_id else 'All Customers'
            
            # Create display name
            if record.is_opening:
                display_name = f"Opening Period {record.year} - {customer_name}"
            else:
                month_name = record.month_name or ''
                display_name = f"{month_name} {record.year} - {customer_name}"
                
            result.append((record.id, display_name))
        return result
    
    @api.depends('month')
    def _wilco_compute_month_name(self):
        """
        Compute the month name based on the month number.
            Following naming conventions from PLANNING.md.
        """
        months = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        for record in self:
            if record.is_opening:
                record.month_name = f"Opening ({months.get(record.month, '')} {record.year})"
            else:
                record.month_name = months.get(record.month, '')
                
    def _wilco_prepare_invoice_domain(self):
        """
        Helper method to prepare the invoice domain based on period type.
        Following naming conventions from PLANNING.md.
        
        :return: Domain for filtering invoices for this period
        """
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ]
        
        # Add date range filter
        if self.is_opening:
            # For opening periods, get all invoices BEFORE this year-month (strictly before)
            # Convert to string for date comparison
            opening_date = f"{self.year}-{self.month:02d}-01"
            domain.append(('invoice_date', '<', opening_date))
        else:
            # For regular periods, get invoices for the specific year-month
            start_date = f"{self.year}-{self.month:02d}-01"
            
            # Calculate end date (first day of next month)
            if self.month < 12:
                end_date = f"{self.year}-{self.month + 1:02d}-01"
            else:
                end_date = f"{self.year + 1}-01-01"
                
            domain.extend([
                ('invoice_date', '>=', start_date),
                ('invoice_date', '<', end_date)
            ])
        
        # Add partner filter if specified
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
            
        return domain
    
    def wilco_action_view_invoices(self):
        """
        Show related customer invoices for this period.
        Following naming conventions from PLANNING.md for action methods.
        
        :return: Action to open the list of related invoices
        """
        self.ensure_one()
        
        # Create domain for invoice search
        domain = self._wilco_prepare_invoice_domain()
        
        # Get the action definition to open invoices
        action = {
            'name': f'Invoices for {self.month_name} {self.year}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': domain,
            'context': {'search_default_posted': 1},
        }
        
        return action
        
    def wilco_action_view_invoice_items(self):
        """
        Show invoice line items for this period's invoices.
        Following naming conventions from PLANNING.md for action methods.
        
        :return: Action to open the list of invoice line items
        """
        self.ensure_one()
        
        # Get invoice domain
        invoice_domain = self._wilco_prepare_invoice_domain()
        
        # Find all invoices matching the domain
        invoices = self.env['account.move'].search(invoice_domain)
        
        # Get the action definition to open invoice items
        action = {
            'name': f'Invoice Items for {self.month_name} {self.year}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [
                ('move_id', 'in', invoices.ids),
                ('account_id.account_type', 'not in', ['asset_receivable', 'liability_payable']),
                ('display_type', 'in', ['product', 'line_section', 'line_note', False]),
            ],
            'context': {'search_default_group_by_product': 1},
        }
        
        return action
        
    def wilco_action_view_journal_entries(self):
        """
        Show journal entries for this period.
        Following naming conventions from PLANNING.md for action methods.
        
        :return: Action to open the list of journal entries
        """
        self.ensure_one()
        
        # Create date range for journal entries
        if self.is_opening:
            # For opening period, show entries up to the period
            date_domain = [('date', '<', f"{self.year}-{self.month:02d}-01")]
        else:
            # For regular periods, get entries for the specific month
            start_date = f"{self.year}-{self.month:02d}-01"
            
            # Calculate end date
            if self.month < 12:
                end_date = f"{self.year}-{self.month + 1:02d}-01"
            else:
                end_date = f"{self.year + 1}-01-01"
                
            date_domain = [
                ('date', '>=', start_date),
                ('date', '<', end_date)
            ]
        
        domain = [('state', '=', 'posted')] + date_domain
        
        # Add partner filter if specified
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        
        # Get the action definition to open journal entries
        action = {
            'name': f'Journal Entries for {self.month_name} {self.year}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': domain,
            'context': {'search_default_posted': 1},
        }
        
        return action
        
    def wilco_action_view_journal_items(self):
        """
        Show journal items for this period.
        Following naming conventions from PLANNING.md for action methods.
        
        :return: Action to open the list of journal items
        """
        self.ensure_one()
        
        # Create date range for journal items
        if self.is_opening:
            # For opening period, show items up to the period
            date_domain = [('date', '<', f"{self.year}-{self.month:02d}-01")]
        else:
            # For regular periods, get items for the specific month
            start_date = f"{self.year}-{self.month:02d}-01"
            
            # Calculate end date
            if self.month < 12:
                end_date = f"{self.year}-{self.month + 1:02d}-01"
            else:
                end_date = f"{self.year + 1}-01-01"
                
            date_domain = [
                ('date', '>=', start_date),
                ('date', '<', end_date)
            ]
        
        domain = [('parent_state', '=', 'posted')] + date_domain
        
        # Add partner filter if specified
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        
        # Get the action definition to open journal items
        action = {
            'name': f'Journal Items for {self.month_name} {self.year}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': domain,
            'context': {'search_default_group_by_account': 1},
        }
        
        return action