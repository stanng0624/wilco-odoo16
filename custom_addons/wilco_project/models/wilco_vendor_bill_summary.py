from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class WilcoVendorBillSummary(models.Model):
    _name = 'wilco.vendor.bill.summary'
    _description = 'Vendor Bill Summary Report'
    _order = 'is_opening desc, year asc, month asc, is_breakdown asc, bill_date asc, id asc'

    year = fields.Integer(string='Year', readonly=True)
    month = fields.Integer(string='Month', readonly=True)
    month_name = fields.Char(string='Month Name', compute='_wilco_compute_month_name', store=True)
    period = fields.Char(string='Period', compute='_compute_period', store=True, 
                       help="Period in YYYY-MM format for easy grouping")
    bill_count = fields.Integer(string='No of Bills', readonly=True)
    expense_amount = fields.Monetary(string='Expenses', currency_field='company_currency_id', readonly=True)
    total_expense_amount = fields.Monetary(string='Total Expenses', currency_field='company_currency_id', readonly=True, 
                                         help="Accumulated expenses from previous periods including current period")
    settled_amount = fields.Monetary(string='Settled', currency_field='company_currency_id', readonly=True)
    amount_prepayment = fields.Monetary(string='Prepayment', currency_field='company_currency_id', readonly=True,
                                      help="Prepayment amount for this period")
    amount_prepayment_applied = fields.Monetary(string='Prepayment Applied', currency_field='company_currency_id', readonly=True,
                                              help="Prepayment applied amount for this period")
    balance = fields.Monetary(string='Balance', currency_field='company_currency_id', readonly=True,
                           help="For bill breakdowns: Expenses - Settled + Prepayment - Prepayment Applied. For period records, it's always 0.")
    period_balance = fields.Monetary(string='Period Balance', currency_field='company_currency_id', readonly=True,
                               help="Running balance that includes all previous periods: previous period balance + current expenses - current settled + prepayment - prepayment applied")
    is_opening = fields.Boolean(string='Is Opening Period', default=False, 
                              help="Indicates this is an opening period record with consolidated previous activity")
    description = fields.Char(string='Description', readonly=True,
                            help="Additional description for opening period records")
    
    # Fields for bill breakdown
    is_breakdown = fields.Boolean(string='Is Bill Breakdown', default=False,
                                help="Indicates this is a bill breakdown record")
    parent_period_id = fields.Many2one('wilco.vendor.bill.summary', string='Parent Period',
                                     help="Reference to the parent period summary record")
    bill_id = fields.Many2one('account.move', string='Bill', readonly=True)
    bill_date = fields.Date(string='Bill Date', readonly=True)
    bill_number = fields.Char(string='Bill Number', readonly=True)
    settled_dates = fields.Char(string='Settled Date(s)', readonly=True,
                              help="Dates when payments were applied to this bill")
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    
    # For filtering
    as_of_date = fields.Date(string='As Of Date')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    expense_account_id = fields.Many2one('account.account', string='Expense Account')
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
                opening_period_exists = self.env['wilco.vendor.bill.summary'].search_count([
                    ('is_opening', '=', True),
                    ('year', '=', record.year)
                ], limit=1)
                
                if record.month == 1 and opening_period_exists:
                    record.period = f"{period_string} (3: First period)"
                else:
                    record.period = period_string
    
    def name_get(self):
        """
        Return a better display name for the vendor bill summary records.
        
        Format:
        - If vendor exists: "[Month Year] Vendor Name"
        - If no vendor: "[Month Year] All Vendors"
        - For bill breakdowns: "Bill: [Number] ([Date])"
        """
        result = []
        for record in self:
            if record.is_breakdown and record.bill_number:
                bill_date = record.bill_date.strftime('%Y-%m-%d') if record.bill_date else ''
                display_name = f"Bill: {record.bill_number} ({bill_date})"
            else:
                # Get vendor name if exists
                vendor_name = record.partner_id.name if record.partner_id else 'All Vendors'
                
                # Create display name
                if record.is_opening:
                    display_name = f"Opening Period {record.year} - {vendor_name}"
                else:
                    month_name = record.month_name or ''
                    display_name = f"{month_name} {record.year} - {vendor_name}"
                
            result.append((record.id, display_name))
        return result
    
    @api.depends('month')
    def _wilco_compute_month_name(self):
        """
        Compute the month name based on the month number.
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
                
    def _wilco_prepare_bill_domain(self):
        """
        Helper method to prepare the bill domain based on period type.
        
        :return: Domain for filtering bills for this period
        """
        domain = [
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('state', '=', 'posted')
        ]
        
        # Add date range filter
        if self.is_opening:
            # For opening periods, get all bills BEFORE this year-month (strictly before)
            # Convert to string for date comparison
            opening_date = f"{self.year}-{self.month:02d}-01"
            domain.append(('invoice_date', '<', opening_date))
        else:
            # For regular periods, get bills for the specific year-month
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
    
    def wilco_action_view_bills(self):
        """
        Show related vendor bills for this period.
        
        :return: Action to open the list of related bills
        """
        self.ensure_one()
        
        # Create domain for bill search
        domain = self._wilco_prepare_bill_domain()
        
        # Get the action definition to open bills
        action = {
            'name': f'Bills for {self.month_name} {self.year}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': domain,
            'context': {'search_default_posted': 1},
        }
        
        return action
        
    def wilco_action_view_bill_items(self):
        """
        Show related vendor bill items for this period.
        
        :return: Action to open the list of related bill items
        """
        self.ensure_one()
        
        # Create domain for bill search
        bill_domain = self._wilco_prepare_bill_domain()
        
        # Search for bills matching the criteria
        bills = self.env['account.move'].search(bill_domain)
        
        # Create domain for bill lines
        domain = [
            ('move_id', 'in', bills.ids),
            ('display_type', '=', 'product'),
            ('account_id', '!=', False)
        ]
        
        # Get the action definition to open bill lines
        action = {
            'name': f'Bill Items for {self.month_name} {self.year}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': domain,
            'context': {},
        }
        
        return action
    
    def wilco_action_view_journal_entries(self):
        """
        Show related journal entries for this period.
        
        :return: Action to open the list of related journal entries
        """
        self.ensure_one()
        
        # Create domain for bill search
        bill_domain = self._wilco_prepare_bill_domain()
        
        # Search for bills matching the criteria
        bills = self.env['account.move'].search(bill_domain)
        
        # Create domain for journal entries (bills themselves)
        domain = [('id', 'in', bills.ids)]
        
        # Get the action definition to open journal entries
        action = {
            'name': f'Journal Entries for {self.month_name} {self.year}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': domain,
            'context': {},
        }
        
        return action
        
    def wilco_action_view_journal_items(self):
        """
        Show related journal items for this period.
        
        :return: Action to open the list of related journal items
        """
        self.ensure_one()
        
        # Create domain for bill search
        bill_domain = self._wilco_prepare_bill_domain()
        
        # Search for bills matching the criteria
        bills = self.env['account.move'].search(bill_domain)
        
        # Create domain for journal items
        domain = [('move_id', 'in', bills.ids)]
        
        # Get the action definition to open journal items
        action = {
            'name': f'Journal Items for {self.month_name} {self.year}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': domain,
            'context': {},
        }
        
        return action
    
    def wilco_action_view_bill(self):
        """
        Show the related bill for this breakdown record.
        
        :return: Action to open the bill
        """
        self.ensure_one()
        
        if not self.is_breakdown or not self.bill_id:
            return {}
        
        # Get the action definition to open the bill
        action = {
            'name': f'Bill: {self.bill_number}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.bill_id.id,
            'target': 'current',
        }
        
        return action
    
    def wilco_action_view_bill_lines(self):
        """
        Show the related bill lines for this breakdown record.
        
        :return: Action to open the bill lines
        """
        self.ensure_one()
        
        if not self.is_breakdown or not self.bill_id:
            return {}
        
        # Create domain for bill lines
        domain = [
            ('move_id', '=', self.bill_id.id),
            ('display_type', '=', 'product'),
            ('account_id', '!=', False)
        ]
        
        # Get the action definition to open bill lines
        action = {
            'name': f'Bill Lines: {self.bill_number}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': domain,
            'context': {},
        }
        
        return action
    
    def wilco_action_view_bill_journal_entry(self):
        """
        Show the related journal entry for this breakdown record.
        
        :return: Action to open the journal entry
        """
        self.ensure_one()
        
        if not self.is_breakdown or not self.bill_id:
            return {}
        
        # Get the action definition to open the journal entry
        action = {
            'name': f'Journal Entry: {self.bill_number}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.bill_id.id,
            'target': 'current',
        }
        
        return action
    
    def wilco_action_view_bill_journal_items(self):
        """
        Show the related journal items for this breakdown record.
        
        :return: Action to open the journal items
        """
        self.ensure_one()
        
        if not self.is_breakdown or not self.bill_id:
            return {}
        
        # Create domain for journal items
        domain = [('move_id', '=', self.bill_id.id)]
        
        # Get the action definition to open journal items
        action = {
            'name': f'Journal Items: {self.bill_number}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': domain,
            'context': {},
        }
        
        return action
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
        Override read_group to customize group display.
        """
        result = super(WilcoVendorBillSummary, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )
        
        return result 