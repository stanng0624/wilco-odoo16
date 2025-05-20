from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class WilcoCustomerInvoiceSummary(models.Model):
    _name = 'wilco.customer.invoice.summary'
    _description = 'Customer Invoice Summary Report'
    _order = 'is_opening desc, year asc, month asc, is_breakdown asc, invoice_date asc, id asc'

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
    amount_downpayment = fields.Monetary(string='Down Payment', currency_field='company_currency_id', readonly=True,
                                       help="Down payment amount for this period")
    amount_downpayment_deducted = fields.Monetary(string='Down Payment Deducted', currency_field='company_currency_id', readonly=True,
                                                help="Down payment deducted amount for this period")
    balance = fields.Monetary(string='Balance', currency_field='company_currency_id', readonly=True,
                           help="For invoice breakdowns: Sales - Settled + Down Payment - Down Payment Deducted. For period records, it's always 0.")
    period_balance = fields.Monetary(string='Period Balance', currency_field='company_currency_id', readonly=True,
                               help="Running balance that includes all previous periods: previous period balance + current sales - current settled + down payment - down payment deducted")
    is_opening = fields.Boolean(string='Is Opening Period', default=False, 
                              help="Indicates this is an opening period record with consolidated previous activity")
    description = fields.Char(string='Description', readonly=True,
                            help="Additional description for opening period records")
    
    # Fields for invoice breakdown
    is_breakdown = fields.Boolean(string='Is Invoice Breakdown', default=False,
                                help="Indicates this is an invoice breakdown record")
    parent_period_id = fields.Many2one('wilco.customer.invoice.summary', string='Parent Period',
                                     help="Reference to the parent period summary record")
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    invoice_date = fields.Date(string='Invoice Date', readonly=True)
    invoice_number = fields.Char(string='Invoice Number', readonly=True)
    settled_dates = fields.Char(string='Settled Date(s)', readonly=True,
                              help="Dates when payments were applied to this invoice")
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    
    # For filtering
    as_of_date = fields.Date(string='As Of Date')
    partner_id = fields.Many2one('res.partner', string='Customer')
    sales_account_id = fields.Many2one('account.account', string='Sales Account')
    project_id = fields.Many2one('project.project', string='Project')
    
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
                # First regular month (January) gets special naming only when opening periods are used
                # We check for opening periods by checking if any opening period exists in the system
                opening_period_exists = self.env['wilco.customer.invoice.summary'].search_count([
                    ('is_opening', '=', True),
                    ('year', '=', record.year)
                ], limit=1)
                
                if record.month == 1 and opening_period_exists:
                    record.period = f"{period_string} (3: First period)"
                else:
                    record.period = period_string
    
    def name_get(self):
        """
        Return a better display name for the customer invoice summary records.
        
        Format:
        - If customer exists: "[Month Year] Customer Name"
        - If no customer: "[Month Year] All Customers"
        - For invoice breakdowns: "Invoice: [Number] ([Date])"
        """
        result = []
        for record in self:
            if record.is_breakdown and record.invoice_number:
                invoice_date = record.invoice_date.strftime('%Y-%m-%d') if record.invoice_date else ''
                display_name = f"Invoice: {record.invoice_number} ({invoice_date})"
            else:
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
            ('move_type', 'in', ['out_invoice', 'out_refund']),
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
            # Fix: Convert id to string to satisfy type checker
            domain.append(('partner_id', '=', str(self.partner_id.id)))
            
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
            # Fix: Convert id to string to satisfy type checker
            domain.append(('partner_id', '=', str(self.partner_id.id)))
        
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
            # Fix: Convert id to string to satisfy type checker
            domain.append(('partner_id', '=', str(self.partner_id.id)))
        
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
        
    def wilco_action_view_invoice(self):
        """
        Show the specific invoice for this breakdown record.
        
        :return: Action to open the invoice
        """
        self.ensure_one()
        
        # Check if this is a breakdown record with an invoice
        if not self.is_breakdown or not self.invoice_id:
            return {'type': 'ir.actions.act_window_close'}
        
        # Get the action definition to open the invoice
        action = {
            'name': f'Invoice {self.invoice_number}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_id': self.invoice_id.id,
            'context': {'create': False},
        }
        
        return action
    
    def wilco_action_view_invoice_lines(self):
        """
        Show invoice lines for the specific invoice in this breakdown record.
        
        :return: Action to open the invoice lines
        """
        self.ensure_one()
        
        # Check if this is a breakdown record with an invoice
        if not self.is_breakdown or not self.invoice_id:
            return {'type': 'ir.actions.act_window_close'}
        
        # Get the action definition to open invoice items
        action = {
            'name': f'Invoice Lines for {self.invoice_number}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [
                ('move_id', '=', self.invoice_id.id),
                ('account_id.account_type', 'not in', ['asset_receivable', 'liability_payable']),
                ('display_type', 'in', ['product', 'line_section', 'line_note', False]),
            ],
            'context': {'search_default_group_by_product': 1},
        }
        
        return action
    
    def wilco_action_view_invoice_journal_entry(self):
        """
        Show the journal entry for the specific invoice in this breakdown record.
        
        :return: Action to open the journal entry
        """
        self.ensure_one()
        
        # Check if this is a breakdown record with an invoice
        if not self.is_breakdown or not self.invoice_id:
            return {'type': 'ir.actions.act_window_close'}
        
        # Get the action definition to open the invoice journal entry
        action = {
            'name': f'Journal Entry for Invoice {self.invoice_number}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_id': self.invoice_id.id,
            'context': {'create': False},
        }
        
        return action
    
    def wilco_action_view_invoice_journal_items(self):
        """
        Show journal items for the specific invoice in this breakdown record.
        
        :return: Action to open the invoice journal items
        """
        self.ensure_one()
        
        # Check if this is a breakdown record with an invoice
        if not self.is_breakdown or not self.invoice_id:
            return {'type': 'ir.actions.act_window_close'}
        
        # Get the action definition to open invoice journal items
        action = {
            'name': f'Journal Items for Invoice {self.invoice_number}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('move_id', '=', self.invoice_id.id)],
            'context': {'search_default_group_by_account': 1},
        }
        
        return action
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
        Override read_group to handle aggregated fields correctly.
        Some fields like total_sales_amount and period_balance shouldn't be aggregated 
        when grouping by any field because they represent running totals and balances.
        
        Also exclude historical opening records from group totals for invoice_count and sales_amount.
        Also exclude invoice breakdown records from totals for sales_amount and settled_amount.
        """
        # Fields that don't make sense when grouped
        invalid_group_fields = ['total_sales_amount', 'period_balance']
        
        # Fields that should exclude historical opening records from totals
        exclude_historical_fields = ['invoice_count', 'sales_amount', 'amount_downpayment', 'amount_downpayment_deducted']
        
        # Fields that should exclude invoice breakdown records from totals
        exclude_breakdown_fields = ['sales_amount', 'settled_amount', 'balance', 'amount_downpayment', 'amount_downpayment_deducted']
        
        # Process all normal groups 
        result = super(WilcoCustomerInvoiceSummary, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit,
            orderby=orderby, lazy=lazy
        )
        
        # If we're grouping by any field, adjust certain fields
        if groupby and result:
            # For each group, we need to find and subtract historical opening records
            for group in result:
                # Clear invalid fields in group results (fields that don't make sense when grouped)
                for field in invalid_group_fields:
                    if field in group:
                        group[field] = 0.0  # Set to 0.0 instead of False for monetary fields
                
                # Get the domain for this group
                group_domain = group.get('__domain', [])
                
                # 1. Exclude historical opening records
                if any(field in exclude_historical_fields for field in fields):
                    # Create a domain to find historical opening records within this group
                    historical_domain = group_domain + [
                        ('is_opening', '=', True),
                        ('description', 'ilike', 'Historical')
                    ]
                    
                    # Find the historical records in this group
                    historical_records = self.search(historical_domain)
                    
                    if historical_records:
                        # Adjust the count fields for each historical record found
                        for field in exclude_historical_fields:
                            if field in group:
                                historical_total = sum(historical_records.mapped(field))
                                group[field] -= historical_total
                
                # 2. Exclude invoice breakdown records
                if any(field in exclude_breakdown_fields for field in fields):
                    # Create a domain to find breakdown records within this group
                    breakdown_domain = group_domain + [
                        ('is_breakdown', '=', True)
                    ]
                    
                    # Find the breakdown records in this group
                    breakdown_records = self.search(breakdown_domain)
                    
                    if breakdown_records:
                        # Adjust the fields for each breakdown record found
                        for field in exclude_breakdown_fields:
                            if field in group:
                                breakdown_total = sum(breakdown_records.mapped(field))
                                group[field] -= breakdown_total
        
        return result