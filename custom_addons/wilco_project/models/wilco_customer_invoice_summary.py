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
    invoice_count = fields.Integer(string='No of Invoice', readonly=True)
    sales_amount = fields.Monetary(string='Sales', currency_field='company_currency_id', readonly=True)
    total_sales_amount = fields.Monetary(string='Total Sales', currency_field='company_currency_id', readonly=True, 
                                       help="Accumulated sales from previous periods including current period")
    settled_amount = fields.Monetary(string='Settled', currency_field='company_currency_id', readonly=True)
    balance = fields.Monetary(string='Balance', currency_field='company_currency_id', readonly=True)
    is_opening = fields.Boolean(string='Is Opening Period', default=False, 
                              help="Indicates this is an opening period record with consolidated previous activity")
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    
    # For filtering
    as_of_date = fields.Date(string='As Of Date')
    partner_id = fields.Many2one('res.partner', string='Customer')
    
    # Ledger account breakdown relation
    ledger_breakdown_ids = fields.One2many('wilco.customer.invoice.ledger', 'summary_id', 
                                        string='Ledger Account Breakdown')
    
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
            # For opening periods, get all invoices before this year-month
            domain.extend([
                '|',
                ('invoice_date', '<', f"{self.year}-{self.month:02d}-01"),  # Before this year-month
                '&',
                ('invoice_date', '>=', f"{self.year}-{self.month:02d}-01"),  # This year-month
                ('invoice_date', '<', f"{self.year}-{self.month+1 if self.month < 12 else 1:02d}-01")  # Before next month
            ])
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
    
    def wilco_action_view_ledger_breakdown(self):
        """
        Show ledger account breakdown for this period.
        Following naming conventions from PLANNING.md for action methods.
        
        :return: Action to open the list of ledger account details
        """
        self.ensure_one()
        
        # Get the action definition to open ledger breakdown
        action = {
            'name': f'Ledger Account Breakdown for {self.month_name} {self.year}',
            'type': 'ir.actions.act_window',
            'res_model': 'wilco.customer.invoice.ledger',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('summary_id', '=', self.id)],
            'context': {'search_default_group_by_account': 1},
        }
        
        return action


class WilcoCustomerInvoiceLedger(models.Model):
    _name = 'wilco.customer.invoice.ledger'
    _description = 'Customer Invoice Ledger Summary'
    _order = 'summary_id, account_id'
    
    summary_id = fields.Many2one('wilco.customer.invoice.summary', string='Invoice Summary', 
                                ondelete='cascade', required=True)
    account_id = fields.Many2one('account.account', string='Ledger Account', required=True)
    account_code = fields.Char(related='account_id.code', string='Account Code', store=True)
    account_name = fields.Char(related='account_id.name', string='Account Name', store=True)
    
    # Summary amounts
    amount = fields.Monetary(string='Amount', currency_field='company_currency_id', readonly=True)
    
    # Related fields from parent summary
    year = fields.Integer(related='summary_id.year', string='Year', readonly=True, store=True)
    month = fields.Integer(related='summary_id.month', string='Month', readonly=True, store=True)
    month_name = fields.Char(related='summary_id.month_name', string='Month Name', readonly=True)
    is_opening = fields.Boolean(related='summary_id.is_opening', string='Is Opening Period', readonly=True, store=True)
    partner_id = fields.Many2one(related='summary_id.partner_id', string='Customer', readonly=True)
    company_id = fields.Many2one(related='summary_id.company_id', string='Company', readonly=True)
    company_currency_id = fields.Many2one(related='summary_id.company_currency_id', readonly=True)