from odoo import models, fields, api
from datetime import date, datetime, timedelta
import logging


class WilcoInvoiceSummaryWizard(models.TransientModel):
    _name = 'wilco.invoice.summary.wizard'
    _description = 'Customer Invoice Summary Wizard'

    as_of_date = fields.Date(string='As Of Date', required=True, default=fields.Date.today)
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('customer_rank', '>', 0)])
    wilco_project_id = fields.Many2one('project.project', string='Project')
    
    # Opening period fields
    use_opening_period = fields.Boolean(string='Use Opening Period', default=True,
                                        help="Define an opening period to consolidate all previous activity")
    opening_year = fields.Integer(string='Opening Year', default=lambda self: fields.Date.today().year)
    # Convert integers to strings to avoid AttributeError with the replace() method during XML ID generation
    opening_month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Opening Month', default='1')
    
    # Balance grouping option
    show_balance_by = fields.Selection([
        ('period', 'Period'),
        ('customer', 'Customer'),
        ('account', 'Sales Account'),
        ('project', 'Project')
    ], string='Show Balance By', default='period',
       help="Determines how to group the invoice data in the report")
    
    # Invoice breakdown option
    show_invoice_breakdown = fields.Boolean(string='Show Invoice Breakdown', default=False,
                                           help="Show individual invoice details within each period")
    
    @api.onchange('as_of_date')
    def _onchange_as_of_date(self):
        """
        Update opening year and month when as_of_date changes.
        Sets it to January of the year of the as_of_date.
        """
        if self.as_of_date and self.use_opening_period:
            # Set opening period to January of the as_of_date's year
            self.opening_year = self.as_of_date.year
            self.opening_month = '1'  # January
    
    @api.onchange('use_opening_period')
    def _onchange_use_opening_period(self):
        """Update opening year and month when toggling the use_opening_period field"""
        if self.use_opening_period and self.as_of_date:
            # Set to January of as_of_date's year when enabling
            self.opening_year = self.as_of_date.year
            self.opening_month = '1'  # January
    
    def wilco_action_generate_report(self):
        """
        Generate the invoice summary report based on the as_of_date
        and optional partner_id filter.
        """
        self.ensure_one()
        
        # Clear existing temporary records
        self.env['wilco.customer.invoice.summary'].sudo().search([]).unlink()
        
        # Generate data
        self._wilco_generate_invoice_summary_data()
        
        # Return action to open the list view with appropriate grouping and filters
        action = {
            'name': 'Customer Invoice Summary',
            'type': 'ir.actions.act_window',
            'res_model': 'wilco.customer.invoice.summary',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': {},
        }
        
        # Set default filters based on options
        context = {}
        
        # If not showing invoice breakdowns, add filter to hide them
        if not self.show_invoice_breakdown:
            context['search_default_not_breakdown'] = 1
        
        # Set grouping based on options - use search_default filters instead of forced group_by
        # This allows users to ungroup the data if needed
        if self.show_balance_by == 'account':
            context['search_default_group_by_sales_account'] = 1
        elif self.show_balance_by == 'customer':
            context['search_default_group_by_partner'] = 1
        elif self.show_balance_by == 'project':
            context['search_default_group_by_project'] = 1
        
        action['context'] = context
        
        return action
        
    def _generate_by_period(self, invoices, opening_month_int):
        """Generate invoice summary by period only"""
        self._generate_generic_report_data(invoices, opening_month_int, 'period')
    
    def _generate_by_customer(self, invoices, opening_month_int):
        """Generate invoice summary by customer and period"""
        self._generate_generic_report_data(invoices, opening_month_int, 'customer')
        
    def _generate_by_project(self, invoices, opening_month_int):
        """Generate invoice summary by project and period"""
        self._generate_generic_report_data(invoices, opening_month_int, 'project')
        
    def _generate_by_sales_account(self, invoices, opening_month_int):
        """Generate invoice summary by sales account and period"""
        # This method is implemented separately as it requires special handling for invoice lines
        # It doesn't use the generic method due to its different processing logic
        # Dictionary to store data: {(sales_account_id, year, month): data}
        account_invoice_data = {}
        account_opening_before = {}  # {sales_account_id: opening_data_before}
        account_opening_during = {}  # {sales_account_id: opening_data_during}
        
        # For invoice breakdown
        account_period_invoices = {}  # {(sales_account_id, year, month): [invoice_data]}
        account_opening_invoices = {}  # {sales_account_id: [invoice_data]}
        
        # Calculate the opening period start date and day before
        opening_start_date = None
        day_before_opening = None
        if self.use_opening_period and opening_month_int > 0:
            opening_start_date = date(self.opening_year, opening_month_int, 1)
            day_before_opening = opening_start_date - timedelta(days=1)
        
        # Group by sales account, year, month
        for invoice in invoices:
            # Skip invoices without invoice_date
            if not invoice.invoice_date:
                continue
                
            year = invoice.invoice_date.year
            month = invoice.invoice_date.month
            
            # Check if this invoice belongs to opening period
            is_opening_period = False
            if self.use_opening_period:
                if opening_start_date and ((year < self.opening_year or 
                    (year == self.opening_year and month < opening_month_int))):
                    is_opening_period = True
            
            # Process each invoice line with account
            for line in invoice.invoice_line_ids.filtered(
                lambda l: l.display_type == 'product' and l.account_id
            ):
                account_id = line.account_id.id

                account_amount = 0.0
                line_total_settled = 0.0
                line_before_settled = 0.0
                line_during_settled = 0.0
                line_downpayment = 0.0
                line_downpayment_deducted = 0.0

                # Check if line is a down payment line
                is_downpayment_line = hasattr(line, 'is_downpayment') and line.is_downpayment

                if invoice.move_type == 'out_invoice':
                    if is_downpayment_line:
                        # For down payment lines: 
                        # - Positive quantity: Down Payment amount
                        # - Negative quantity: Down Payment Deducted amount (now positive in invoice)
                        if line.quantity > 0:
                            line_downpayment = line.price_subtotal
                            account_amount = 0.0  # Not counted in sales
                        else:
                            line_downpayment_deducted = line.price_subtotal * -1
                            account_amount = 0.0  # Not counted in sales
                    else:
                        # Regular line
                        account_amount = line.price_subtotal
                        
                    # Calculate settled amount for this line
                    line_total_settled = self._wilco_compute_line_settled_amount_as_of_date(line, self.as_of_date)
                    line_before_settled = 0.0
                    if is_opening_period and day_before_opening:
                        line_before_settled = self._wilco_compute_line_settled_amount_as_of_date(line, day_before_opening)
                    line_during_settled = line_total_settled - line_before_settled if is_opening_period else line_total_settled
                elif invoice.move_type == 'out_refund':
                    if is_downpayment_line:
                        # For refund down payment lines:
                        # - Positive quantity: refunding Down Payment Deducted (now positive in invoice)
                        # - Negative quantity: refunding Down Payment
                        if line.quantity > 0:
                            # Value is already positive in invoice, just negate for refund
                            line_downpayment_deducted = -line.price_subtotal  # Negative as it's a refund
                            account_amount = 0.0  # Not counted in sales
                        else:
                            line_downpayment = line.price_subtotal
                            account_amount = 0.0  # Not counted in sales
                    else:
                        # Regular refund line
                        account_amount = -line.price_subtotal
                        
                    # Calculate settled amount for this line (negative for refunds)
                    line_total_settled = -self._wilco_compute_line_settled_amount_as_of_date(line, self.as_of_date)
                    line_before_settled = 0.0
                    if is_opening_period and day_before_opening:
                        line_before_settled = -self._wilco_compute_line_settled_amount_as_of_date(line, day_before_opening)
                    line_during_settled = line_total_settled - line_before_settled if is_opening_period else line_total_settled
                
                if is_opening_period:
                    # Initialize sales account opening data if not exists
                    if account_id not in account_opening_before:
                        account_opening_before[account_id] = {
                            'year': self.opening_year if self.use_opening_period else 0,
                            'month': opening_month_int,
                            'invoice_count': 0,
                            'sales_amount': 0.0,
                            'settled_amount': 0.0,
                            'amount_downpayment': 0.0,
                            'amount_downpayment_deducted': 0.0,
                            'is_opening': True,
                            'is_historical': True,
                            'partner_id': self.partner_id.id if self.partner_id else False,
                            'sales_account_id': account_id,
                        }
                        
                        account_opening_during[account_id] = {
                            'year': self.opening_year if self.use_opening_period else 0,
                            'month': opening_month_int,
                            'invoice_count': 0,
                            'sales_amount': 0.0,
                            'settled_amount': 0.0,
                            'amount_downpayment': 0.0,
                            'amount_downpayment_deducted': 0.0,
                            'is_opening': True,
                            'is_historical': False,
                            'partner_id': self.partner_id.id if self.partner_id else False,
                            'sales_account_id': account_id,
                        }
                        
                        if self.show_invoice_breakdown:
                            account_opening_invoices[account_id] = []
                    
                    # Add to opening data counts and sales
                    if not is_downpayment_line or (is_downpayment_line and account_amount > 0):
                        # Only count invoice once for each account
                        account_opening_before[account_id]['invoice_count'] += 1
                    
                    account_opening_before[account_id]['sales_amount'] += account_amount
                    account_opening_during[account_id]['sales_amount'] += account_amount
                    
                    # Add down payment amounts
                    account_opening_before[account_id]['amount_downpayment'] += line_downpayment
                    account_opening_during[account_id]['amount_downpayment'] += line_downpayment
                    
                    account_opening_before[account_id]['amount_downpayment_deducted'] += line_downpayment_deducted
                    account_opening_during[account_id]['amount_downpayment_deducted'] += line_downpayment_deducted
                    
                    # Calculate settlement BEFORE opening period
                    before_amount = 0.0
                    if day_before_opening:
                        before_amount = self._wilco_compute_settled_amount_as_of_date(invoice, day_before_opening)
                    account_opening_before[account_id]['settled_amount'] += before_amount
                    
                    # Calculate settlement DURING opening period to as-of-date
                    total_settled = self._wilco_compute_settled_amount_as_of_date(invoice, self.as_of_date)
                    during_amount = total_settled - before_amount
                    account_opening_during[account_id]['settled_amount'] += during_amount
                    
                    # Store invoice for breakdown if needed
                    if self.show_invoice_breakdown:
                        # For grouped breakdown, create a dictionary keyed by invoice and account_id
                        invoice_key = (invoice.id, account_id)
                        
                        # Check if we already have this invoice for this account in the list
                        existing_entry = next((
                            item for item in account_opening_invoices[account_id] 
                            if item['invoice'] == invoice and item['account_id'] == account_id
                        ), None)
                        
                        if existing_entry:
                            # Update existing invoice entry
                            existing_entry['before_amount'] += before_amount
                            existing_entry['during_amount'] += during_amount
                            existing_entry['total_settled'] += line_total_settled
                            existing_entry['account_amount'] += account_amount
                            existing_entry['amount_downpayment'] += line_downpayment
                            existing_entry['amount_downpayment_deducted'] += line_downpayment_deducted
                        else:
                            # Add new invoice entry
                            account_opening_invoices[account_id].append({
                                'invoice': invoice,
                                'before_amount': before_amount,
                                'during_amount': during_amount,
                                'total_settled': line_total_settled,
                                'account_id': account_id,
                                'account_amount': account_amount,
                                'amount_downpayment': line_downpayment,
                                'amount_downpayment_deducted': line_downpayment_deducted
                            })
                else:
                    # Add to regular periods by sales account
                    key = (account_id, year, month)
                    
                    if key not in account_invoice_data:
                        account_invoice_data[key] = {
                            'year': year,
                            'month': month,
                            'invoice_count': 0,
                            'sales_amount': 0.0,
                            'settled_amount': 0.0,
                            'amount_downpayment': 0.0,
                            'amount_downpayment_deducted': 0.0,
                            'is_opening': False,
                            'is_historical': False,
                            'partner_id': self.partner_id.id if self.partner_id else False,
                            'sales_account_id': account_id,
                        }
                        
                        if self.show_invoice_breakdown:
                            account_period_invoices[key] = []
                    
                    if not is_downpayment_line or (is_downpayment_line and account_amount > 0):
                        # Only count invoice once for each account
                        account_invoice_data[key]['invoice_count'] += 1
                    
                    account_invoice_data[key]['sales_amount'] += account_amount
                    account_invoice_data[key]['settled_amount'] += line_total_settled
                    account_invoice_data[key]['amount_downpayment'] += line_downpayment
                    account_invoice_data[key]['amount_downpayment_deducted'] += line_downpayment_deducted
                    
                    # Store invoice for breakdown if needed
                    if self.show_invoice_breakdown:
                        # For grouped breakdown, check if invoice already exists for this account and period
                        existing_entry = next((
                            item for item in account_period_invoices[key] 
                            if item['invoice'] == invoice and item['account_id'] == account_id
                        ), None)
                        
                        if existing_entry:
                            # Update existing invoice entry
                            existing_entry['settled_amount'] += line_total_settled
                            existing_entry['account_amount'] += account_amount
                            existing_entry['amount_downpayment'] += line_downpayment
                            existing_entry['amount_downpayment_deducted'] += line_downpayment_deducted
                        else:
                            # Add new invoice entry
                            account_period_invoices[key].append({
                                'invoice': invoice,
                                'settled_amount': line_total_settled,
                                'account_id': account_id,
                                'account_amount': account_amount,
                                'amount_downpayment': line_downpayment,
                                'amount_downpayment_deducted': line_downpayment_deducted
                            })
        
        # Store created periods for invoice breakdown linking
        created_periods = {}  # {(account_id, year, month, is_historical): record_id}
        
        # Track period balance by sales account
        account_period_balances = {}  # {account_id: current_period_balance}
        
        # Process sales account opening records
        for account_id, opening_before in account_opening_before.items():
            opening_during = account_opening_during[account_id]
            
            # Initialize period balance for this sales account
            account_period_balances[account_id] = 0.0
            
            # First row: Historical row (before opening period)
            # Calculate balance with new formula: sales - settled + dp - dpd
            historical_period_balance = (
                opening_before['sales_amount'] 
                - opening_before['settled_amount']
                + opening_before['amount_downpayment']
                - opening_before['amount_downpayment_deducted']
            )
            
            historical_period = self.env['wilco.customer.invoice.summary'].create({
                'year': opening_before['year'],
                'month': opening_before['month'],
                'invoice_count': opening_before['invoice_count'],
                'sales_amount': opening_before['sales_amount'],  # Show actual sales
                'total_sales_amount': 0.0,  # For opening period, total_sales MUST be zero
                'settled_amount': opening_before['settled_amount'],
                'amount_downpayment': opening_before['amount_downpayment'],
                'amount_downpayment_deducted': opening_before['amount_downpayment_deducted'],
                'balance': (
                    opening_before['sales_amount'] 
                    - opening_before['settled_amount']
                    + opening_before['amount_downpayment']
                    - opening_before['amount_downpayment_deducted']
                ),
                'period_balance': historical_period_balance,  # Initial period balance
                'as_of_date': self.as_of_date,
                'partner_id': opening_before['partner_id'],
                'sales_account_id': opening_before['sales_account_id'],
                'is_opening': True,
                'description': 'Historical - Settlement before opening',
                'is_breakdown': False
            })
            
            # Update running period balance for this sales account
            account_period_balances[account_id] = historical_period_balance
            
            created_periods[(account_id, opening_before['year'], opening_before['month'], True)] = historical_period.id
            
            # Second row: Opening period (settlement during opening period)
            opening_period_balance = account_period_balances[account_id] - opening_during['settled_amount']
            
            opening_period = self.env['wilco.customer.invoice.summary'].create({
                'year': opening_during['year'],
                'month': opening_during['month'],
                'invoice_count': 0,  # Don't count invoices twice
                'sales_amount': 0.0,  # Don't show sales twice
                'total_sales_amount': 0.0,  # For opening period, total_sales MUST be zero
                'settled_amount': opening_during['settled_amount'],
                'amount_downpayment': 0.0,  # Don't show down payment twice
                'amount_downpayment_deducted': 0.0,  # Don't show down payment deducted twice
                'balance': 0.0 - opening_during['settled_amount'],
                'period_balance': opening_period_balance,  # Roll up from previous period
                'as_of_date': self.as_of_date,
                'partner_id': opening_during['partner_id'],
                'sales_account_id': opening_during['sales_account_id'],
                'is_opening': True,
                'description': 'Opening - Settlement during period',
                'is_breakdown': False
            })
            
            # Update running period balance for this sales account
            account_period_balances[account_id] = opening_period_balance
            
            created_periods[(account_id, opening_during['year'], opening_during['month'], False)] = opening_period.id
            
            # Add invoice breakdown for opening periods if needed
            if self.show_invoice_breakdown and account_id in account_opening_invoices:
                # Skip the historical period breakdowns
                # Only create breakdowns for the regular opening period
                for inv_data in account_opening_invoices[account_id]:
                    invoice = inv_data['invoice']
                    
                    # Create opening breakdown (settlement during opening)
                    if inv_data['during_amount'] > 0:
                        # For invoice breakdowns, balance using new formula:
                        # sales - settled + dp - dpd
                        # For opening periods: 0 - settled + 0 - 0 = -settled
                        breakdown_balance = 0.0 - inv_data['during_amount']
                        
                        self.env['wilco.customer.invoice.summary'].create({
                            'year': opening_during['year'],
                            'month': opening_during['month'],
                            'invoice_count': 0,
                            'sales_amount': 0.0,  # Don't count sales twice
                            'total_sales_amount': 0.0,
                            'settled_amount': inv_data['during_amount'],
                            'amount_downpayment': 0.0,  # Don't count down payment twice
                            'amount_downpayment_deducted': 0.0,  # Don't count down payment deducted twice
                            'balance': breakdown_balance,
                            'period_balance': 0.0,  # Not used for breakdowns
                            'as_of_date': self.as_of_date,
                            'partner_id': invoice.partner_id.id,
                            'sales_account_id': inv_data['account_id'],
                            'is_opening': True,
                            'description': 'Opening Settlement Breakdown',
                            'is_breakdown': True,
                            'parent_period_id': opening_period.id,
                            'invoice_id': invoice.id,
                            'invoice_date': invoice.invoice_date,
                            'invoice_number': invoice.name,
                            'settled_dates': self._get_settlement_dates(invoice, self.as_of_date)
                        })
        
        # Track sales account sales totals
        account_sales_totals = {}  # {account_id: total_sales_excluding_opening}
        
        # Initialize sales account totals
        for account_id in account_opening_before.keys():
            account_sales_totals[account_id] = 0.0
        
        # Create summary records
        sorted_keys = sorted(account_invoice_data.keys())
        for key in sorted_keys:
            account_id, year, month = key
            
            # Skip periods before the opening period if using opening period
            if self.use_opening_period and opening_start_date:
                if (year < self.opening_year or 
                    (year == self.opening_year and month < opening_month_int)):
                    continue
            
            # Initialize tracking if not exists (for accounts without opening records)
            if account_id not in account_period_balances:
                account_period_balances[account_id] = 0.0
                account_sales_totals[account_id] = 0.0
            
            # Current period calculation
            current_data = account_invoice_data[key]
            current_sales = current_data['sales_amount']
            current_settled = current_data['settled_amount']
            current_downpayment = current_data['amount_downpayment']
            current_downpayment_deducted = current_data['amount_downpayment_deducted']
            
            # Update running totals for this sales account
            account_sales_totals[account_id] += current_sales
            
            # Calculate period balance with new formula:
            # previous balance + (sales - settled + dp - dpd)
            new_period_balance = (
                account_period_balances[account_id] 
                + current_sales 
                - current_settled
                + current_downpayment
                - current_downpayment_deducted
            )
            
            # Create summary record
            period_summary = self.env['wilco.customer.invoice.summary'].create({
                'year': current_data['year'],
                'month': current_data['month'],
                'invoice_count': current_data['invoice_count'],
                'sales_amount': current_data['sales_amount'],
                'total_sales_amount': account_sales_totals[account_id],
                'settled_amount': current_data['settled_amount'],
                'amount_downpayment': current_data['amount_downpayment'],
                'amount_downpayment_deducted': current_data['amount_downpayment_deducted'],
                'balance': (
                    current_data['sales_amount'] 
                    - current_data['settled_amount']
                    + current_data['amount_downpayment']
                    - current_data['amount_downpayment_deducted']
                ),
                'period_balance': new_period_balance,  # Running period balance for this sales account
                'as_of_date': self.as_of_date,
                'partner_id': current_data['partner_id'],
                'sales_account_id': current_data['sales_account_id'],
                'is_opening': False,
                'description': False,
                'is_breakdown': False
            })
            
            # Update running period balance for next period
            account_period_balances[account_id] = new_period_balance
            
            # Store period for breakdown linking
            created_periods[(account_id, year, month, False)] = period_summary.id
            
            # Create invoice breakdowns if needed
            if self.show_invoice_breakdown and key in account_period_invoices:
                for inv_data in account_period_invoices[key]:
                    invoice = inv_data['invoice']
                    account_amount = inv_data['account_amount']
                    settled_amount = inv_data['settled_amount']
                    downpayment = inv_data.get('amount_downpayment', 0.0)
                    downpayment_deducted = inv_data.get('amount_downpayment_deducted', 0.0)
                    
                    # Calculate balance with new formula
                    breakdown_balance = (
                        account_amount 
                        - settled_amount
                        + downpayment
                        - downpayment_deducted
                    )
                    
                    self.env['wilco.customer.invoice.summary'].create({
                        'year': year,
                        'month': month,
                        'invoice_count': 0,
                        'sales_amount': account_amount,  # Only the amount for this account
                        'total_sales_amount': 0.0,  # No total sales for individual invoices
                        'settled_amount': settled_amount,
                        'amount_downpayment': downpayment,
                        'amount_downpayment_deducted': downpayment_deducted,
                        'balance': breakdown_balance,
                        'period_balance': 0.0,  # Not used for breakdowns
                        'as_of_date': self.as_of_date,
                        'partner_id': invoice.partner_id.id,
                        'sales_account_id': inv_data['account_id'],
                        'is_opening': False,
                        'description': False,
                        'is_breakdown': True,
                        'parent_period_id': period_summary.id,
                        'invoice_id': invoice.id,
                        'invoice_date': invoice.invoice_date,
                        'invoice_number': invoice.name,
                        'settled_dates': self._get_settlement_dates(invoice, self.as_of_date)
                    })
    
    def _wilco_compute_line_settled_amount_as_of_date(self, invoice_line, as_of_date):
        """
        Calculate how much of an invoice line has been settled as of a specific date.
        This considers the invoice line's proportion of the total invoice when distributing
        settlement amounts.
        
        :param invoice_line: The invoice line record to calculate settlement for
        :param as_of_date: The date to check settlement status
        :return: Float amount that has been settled for this specific line
        """
        self.ensure_one()
        
        invoice = invoice_line.move_id
        
        # Get total invoice amount (sum of all line subtotals)
        total_invoice_amount = sum(invoice.invoice_line_ids.filtered(
            lambda l: l.display_type == 'product' and l.account_id
        ).mapped('price_subtotal'))
        
        if total_invoice_amount <= 0:
            return 0.0
            
        # Calculate this line's proportion of the total invoice
        line_amount = invoice_line.price_subtotal
        proportion = line_amount / total_invoice_amount if total_invoice_amount else 0.0
        
        # Calculate total invoice settled amount and multiply by this line's proportion
        total_settled = self._wilco_compute_settled_amount_as_of_date(invoice, as_of_date)
        line_settled = proportion * total_settled
        
        return line_settled
        
    def _wilco_compute_settled_amount_as_of_date(self, invoice, as_of_date):
        """
        Calculate how much of an invoice has been settled as of a specific date.
        
        :param invoice: The invoice record to calculate settlement for
        :param as_of_date: The date to check settlement status
        :return: Float amount that has been settled
        """
        self.ensure_one()
        
        # Find the receivable line for this invoice
        receivable_line = invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == 'asset_receivable'
        )
        
        if not receivable_line:
            return 0.0
        
        # If there's no partial reconciliation, return 0
        if not receivable_line.matched_credit_ids and not receivable_line.matched_debit_ids:
            return 0.0
            
        # Check reconciled payments up to the as_of_date
        settled_amount = 0.0
        
        # Check partial payments (matched credits)
        for partial in receivable_line.matched_credit_ids:
            if partial.max_date <= as_of_date:
                settled_amount += abs(partial.amount)
                
        # Check partial payments (matched debits)
        for partial in receivable_line.matched_debit_ids:
            if partial.max_date <= as_of_date:
                settled_amount += abs(partial.amount)
                
        # Convert to invoice currency if needed
        if invoice.currency_id != invoice.company_id.currency_id:
            settled_amount = invoice.company_id.currency_id._convert(
                settled_amount,
                invoice.currency_id,
                invoice.company_id,
                as_of_date or fields.Date.today()
            )
                
        return settled_amount
        
    def _get_settlement_dates(self, invoice, as_of_date):
        """
        Get the dates when payments were applied to this invoice.
        Only includes dates after the first day of the first period and on or before as-of-date.
        
        :param invoice: The invoice record to get settlement dates for
        :param as_of_date: Only include settlement dates up to this date
        :return: String with comma-separated settlement dates
        """
        self.ensure_one()
        
        # Find the receivable line for this invoice
        receivable_line = invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == 'asset_receivable'
        )
        
        if not receivable_line:
            return ''
        
        # Determine the first day of the first period
        # If using opening period, use the opening month's first day
        # Otherwise use the first day of January for the first year in the report
        if self.use_opening_period:
            first_period_date = fields.Date.from_string(f"{self.opening_year}-{int(self.opening_month):02d}-01")
        else:
            # Find the earliest year in the data
            # We'll use the current year if no data available
            current_year = fields.Date.today().year
            first_period_date = fields.Date.from_string(f"{current_year}-01-01")
            
        settlement_dates = set()
        
        # Collect dates from matched credits
        for partial in receivable_line.matched_credit_ids:
            # Only include dates after first period date and on or before as-of-date
            if first_period_date <= partial.max_date <= as_of_date:
                settlement_dates.add(partial.max_date)
                
        # Collect dates from matched debits
        for partial in receivable_line.matched_debit_ids:
            # Only include dates after first period date and on or before as-of-date
            if first_period_date <= partial.max_date <= as_of_date:
                settlement_dates.add(partial.max_date)
        
        # Sort dates and convert to string format
        sorted_dates = sorted(settlement_dates)
        formatted_dates = [date.strftime('%Y-%m-%d') for date in sorted_dates]
        
        return ', '.join(formatted_dates) if formatted_dates else ''

    def _wilco_generate_invoice_summary_data(self):
        """
        Generate the invoice summary data grouped by year and month.
        Calculate settled amounts based on the as_of_date.
        Handles opening periods and prevents generating periods after as-of-date.
        """
        self.ensure_one()
        
        domain = [
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
        ]
        
        # Add date filter to only get invoices up to as_of_date
        domain.append(('invoice_date', '<=', str(self.as_of_date)))
        
        # Filter by partner if a partner is selected (regardless of view option)
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        
        # Filter by project if wilco_project_id is available in the model
        if hasattr(self, 'wilco_project_id') and self.wilco_project_id:
            domain.append(('wilco_project_id', '=', self.wilco_project_id.id))
        
        invoices = self.env['account.move'].search(domain)
        
        # Convert opening_month to integer for comparisons
        opening_month_int = int(self.opening_month) if self.use_opening_period and self.opening_month else 0
        
        # Process invoices differently depending on the grouping option
        if self.show_balance_by == 'account':
            self._generate_by_sales_account(invoices, opening_month_int)
        elif self.show_balance_by == 'customer':
            self._generate_by_customer(invoices, opening_month_int)
        elif self.show_balance_by == 'project':
            self._generate_by_project(invoices, opening_month_int)
        else:  # Default: 'period'
            self._generate_by_period(invoices, opening_month_int)
            
    def _generate_generic_report_data(self, invoices, opening_month_int, group_by='period'):
        """
        Generic method to generate invoice summary data with different grouping options.
        
        :param invoices: account.move recordset containing the invoices to process
        :param opening_month_int: Integer representing the opening month
        :param group_by: String indicating how to group data ('period', 'customer', 'project')
        """
        self.ensure_one()
        
        # Add logging header
        _logger = logging.getLogger(__name__)
        _logger.info("====== START GENERIC REPORT GENERATION ======")
        _logger.info(f"Group by: {group_by}, Opening month: {opening_month_int}, Invoices count: {len(invoices)}")
        
        # Dictionary to store data
        invoice_data = {}  # For regular periods
        opening_data_before = {}  # Settlement before opening period
        opening_data_during = {}  # Settlement during opening period
        
        # For invoice breakdown
        period_invoices = {}  # Regular period invoices
        opening_invoices = {}  # Opening period invoices
        
        # Calculate the opening period start date and day before ONLY when use_opening_period is True
        opening_start_date = None
        day_before_opening = None
        if self.use_opening_period and opening_month_int > 0:
            opening_start_date = date(self.opening_year, opening_month_int, 1)
            day_before_opening = opening_start_date - timedelta(days=1)
            _logger.info(f"Opening start date: {opening_start_date}, Day before: {day_before_opening}")
        
        # Group by specific dimensions based on the group_by parameter
        invoice_count_opening = 0
        invoice_count_regular = 0
        
        for invoice in invoices:
            # Skip invoices without invoice_date
            if not invoice.invoice_date:
                continue
                
            year = invoice.invoice_date.year
            month = invoice.invoice_date.month
            
            # Create grouping key based on the group_by parameter
            invoice_customer_id = invoice.partner_id.id
            invoice_project_id = invoice.wilco_project_id.id if hasattr(invoice, 'wilco_project_id') and invoice.wilco_project_id else False
            
            if group_by == 'customer':
                key = (invoice_customer_id, year, month)
                opening_key = invoice_customer_id
            elif group_by == 'project':
                key = (invoice_project_id, year, month)
                opening_key = invoice_project_id
            else:  # 'period'
                key = (year, month)
                opening_key = 'default'
            
            # Skip records without project when grouping by project
            if group_by == 'project' and not invoice_project_id:
                continue
                
            # Check if this invoice belongs to opening period
            is_opening_period = False
            if self.use_opening_period:
                if opening_start_date and ((year < self.opening_year or 
                    (year == self.opening_year and month < opening_month_int))):
                    is_opening_period = True
            
            # Get down payment amounts from invoice
            invoice_downpayment = 0.0
            invoice_downpayment_deducted = 0.0
            invoice_downpayment = invoice.wilco_amount_downpayment
            invoice_downpayment_deducted = invoice.wilco_amount_downpayment_deducted
            
            # Calculate adjusted sales amount
            # Sales = Invoice amount - downpayment + downpayment deducted
            invoice_sales_amount = invoice.amount_total - invoice_downpayment + invoice_downpayment_deducted
            
            if is_opening_period:
                invoice_count_opening += 1
                # Initialize opening data if not exists
                if opening_key not in opening_data_before:
                    if group_by == 'customer':
                        partner_id = invoice_customer_id
                        project_id = False
                    elif group_by == 'project':
                        partner_id = self.partner_id.id if self.partner_id else False
                        project_id = invoice_project_id
                    else:  # 'period'
                        partner_id = self.partner_id.id if self.partner_id else False
                        project_id = False
                    
                    opening_data_before[opening_key] = {
                        'year': self.opening_year if self.use_opening_period else 0,
                        'month': opening_month_int,
                        'invoice_count': 0,
                        'sales_amount': 0.0,
                        'settled_amount': 0.0,
                        'amount_downpayment': 0.0,
                        'amount_downpayment_deducted': 0.0,
                        'is_opening': True,
                        'is_historical': True,
                        'partner_id': partner_id,
                        'project_id': project_id,
                    }
                    
                    opening_data_during[opening_key] = {
                        'year': self.opening_year if self.use_opening_period else 0,
                        'month': opening_month_int,
                        'invoice_count': 0,
                        'sales_amount': 0.0,
                        'settled_amount': 0.0,
                        'amount_downpayment': 0.0,
                        'amount_downpayment_deducted': 0.0,
                        'is_opening': True,
                        'is_historical': False,
                        'partner_id': partner_id,
                        'project_id': project_id,
                    }
                    
                    if self.show_invoice_breakdown:
                        opening_invoices[opening_key] = []
                
                # Add to opening data counts and sales
                opening_data_before[opening_key]['invoice_count'] += 1
                opening_data_before[opening_key]['sales_amount'] += invoice_sales_amount
                opening_data_before[opening_key]['amount_downpayment'] += invoice_downpayment
                opening_data_before[opening_key]['amount_downpayment_deducted'] += invoice_downpayment_deducted
                
                opening_data_during[opening_key]['sales_amount'] += invoice_sales_amount
                opening_data_during[opening_key]['amount_downpayment'] += invoice_downpayment
                opening_data_during[opening_key]['amount_downpayment_deducted'] += invoice_downpayment_deducted
                
                # Calculate settlement BEFORE opening period
                before_amount = 0.0
                if day_before_opening:
                    before_amount = self._wilco_compute_settled_amount_as_of_date(invoice, day_before_opening)
                opening_data_before[opening_key]['settled_amount'] += before_amount
                
                # Calculate settlement DURING opening period to as-of-date
                total_settled = self._wilco_compute_settled_amount_as_of_date(invoice, self.as_of_date)
                during_amount = total_settled - before_amount
                opening_data_during[opening_key]['settled_amount'] += during_amount
                
                # Store invoice for breakdown if needed
                if self.show_invoice_breakdown:
                    # Check if this invoice is already in the list
                    existing_invoice = next((x for x in opening_invoices[opening_key] if x['invoice'] == invoice), None)
                    if existing_invoice:
                        # If invoice already exists, update the amounts
                        existing_invoice['before_amount'] += before_amount
                        existing_invoice['during_amount'] += during_amount
                        existing_invoice['total_settled'] += total_settled
                        existing_invoice['account_amount'] += invoice_sales_amount
                        existing_invoice['amount_downpayment'] += invoice_downpayment
                        existing_invoice['amount_downpayment_deducted'] += invoice_downpayment_deducted
                    else:
                        # Add new invoice entry
                        opening_invoices[opening_key].append({
                            'invoice': invoice,
                            'before_amount': before_amount,
                            'during_amount': during_amount,
                            'total_settled': total_settled,
                            'account_id': invoice_customer_id,
                            'account_amount': invoice_sales_amount,
                            'amount_downpayment': invoice_downpayment,
                            'amount_downpayment_deducted': invoice_downpayment_deducted
                        })
            else:
                invoice_count_regular += 1
                # Add to regular periods 
                if key not in invoice_data:
                    if group_by == 'customer':
                        partner_id = invoice_customer_id
                        project_id = False
                    elif group_by == 'project':
                        partner_id = self.partner_id.id if self.partner_id else False
                        project_id = invoice_project_id
                    else:  # 'period'
                        partner_id = self.partner_id.id if self.partner_id else False
                        project_id = False
                    
                    invoice_data[key] = {
                        'year': year,
                        'month': month,
                        'invoice_count': 0,
                        'sales_amount': 0.0,
                        'settled_amount': 0.0,
                        'amount_downpayment': 0.0,
                        'amount_downpayment_deducted': 0.0,
                        'is_opening': False,
                        'is_historical': False,
                        'partner_id': partner_id,
                        'project_id': project_id,
                    }
                    
                    if self.show_invoice_breakdown:
                        period_invoices[key] = []
                
                invoice_data[key]['invoice_count'] += 1
                invoice_data[key]['sales_amount'] += invoice_sales_amount
                invoice_data[key]['amount_downpayment'] += invoice_downpayment
                invoice_data[key]['amount_downpayment_deducted'] += invoice_downpayment_deducted
                
                # Calculate settled amount
                total_settled = self._wilco_compute_settled_amount_as_of_date(invoice, self.as_of_date)
                invoice_data[key]['settled_amount'] += total_settled
                
                # Store invoice for breakdown if needed
                if self.show_invoice_breakdown:
                    # Check if this invoice is already in the list
                    existing_invoice = next((x for x in period_invoices[key] if x['invoice'] == invoice), None)
                    if existing_invoice:
                        # If invoice already exists, don't add it again
                        pass
                    else:
                        # Add new invoice entry
                        period_invoices[key].append({
                            'invoice': invoice,
                            'settled_amount': total_settled,
                            'amount_downpayment': invoice_downpayment,
                            'amount_downpayment_deducted': invoice_downpayment_deducted,
                            'sales_amount': invoice_sales_amount
                        })
        
        _logger.info(f"Processed {invoice_count_opening} opening period invoices and {invoice_count_regular} regular period invoices")
        _logger.info(f"Collected data for {len(opening_data_before)} opening groups and {len(invoice_data)} regular periods")
                        
        # Store created periods for invoice breakdown linking
        created_periods = {}  # Track created period records for linking breakdowns
        
        # Track period balances by group
        period_balances = {}  # {group_key: current_balance}
        
        # Track sales totals by group
        sales_totals = {}  # {group_key: total_sales_excluding_opening}
        
        # Process opening records first
        _logger.info(f"Processing opening periods. Count of opening_data_before: {len(opening_data_before)}, keys: {list(opening_data_before.keys())}")
        opening_historical_count = 0
        opening_settlement_count = 0
        
        for opening_key, opening_before in opening_data_before.items():
            opening_during = opening_data_during[opening_key]
            
            # Initialize group tracking
            period_balances[opening_key] = 0.0
            sales_totals[opening_key] = 0.0
            
            # First row: Historical row (before opening period)
            # Calculate balance including down payment: Sales - Settled + DP - DPD
            historical_period_balance = (
                opening_before['sales_amount'] 
                - opening_before['settled_amount'] 
                + opening_before['amount_downpayment'] 
                - opening_before['amount_downpayment_deducted']
            )
            
            _logger.info(f"Creating historical opening period for key {opening_key}: year={opening_before['year']}, month={opening_before['month']}")
            _logger.info(f"Historical data: sales={opening_before['sales_amount']}, settled={opening_before['settled_amount']}, dp={opening_before['amount_downpayment']}, dpd={opening_before['amount_downpayment_deducted']}")
            
            historical_period = self.env['wilco.customer.invoice.summary'].create({
                'year': opening_before['year'],
                'month': opening_before['month'],
                'invoice_count': opening_before['invoice_count'],
                'sales_amount': opening_before['sales_amount'],  # Show actual sales
                'total_sales_amount': 0.0,  # For opening period, total_sales MUST be zero
                'settled_amount': opening_before['settled_amount'],
                'amount_downpayment': opening_before['amount_downpayment'],
                'amount_downpayment_deducted': opening_before['amount_downpayment_deducted'],
                'balance': (
                    opening_before['sales_amount'] 
                    - opening_before['settled_amount'] 
                    + opening_before['amount_downpayment'] 
                    - opening_before['amount_downpayment_deducted']
                ),
                'period_balance': historical_period_balance,  # Initial period balance
                'as_of_date': self.as_of_date,
                'partner_id': opening_before['partner_id'],
                'project_id': opening_before['project_id'],
                'is_opening': True,
                'description': 'Historical - Settlement before opening',
                'is_breakdown': False
            })
            opening_historical_count += 1
            
            # Update running period balance for this group
            period_balances[opening_key] = historical_period_balance
            
            # Track created periods for breakdown linking
            if group_by == 'customer':
                created_periods[(opening_key, opening_before['year'], opening_before['month'], True)] = historical_period.id
            elif group_by == 'project':
                created_periods[(opening_key, opening_before['year'], opening_before['month'], True)] = historical_period.id
            else:
                created_periods[(opening_before['year'], opening_before['month'], True)] = historical_period.id
            
            # Second row: Opening period (settlement during opening period)
            # Update period balance including down payment fields
            opening_period_balance = (
                period_balances[opening_key] 
                - opening_during['settled_amount']
            )
            
            _logger.info(f"Creating settlement opening period for key {opening_key}: year={opening_during['year']}, month={opening_during['month']}")
            _logger.info(f"Settlement data: settled={opening_during['settled_amount']}, balance={opening_period_balance}")
            
            opening_period = self.env['wilco.customer.invoice.summary'].create({
                'year': opening_during['year'],
                'month': opening_during['month'],
                'invoice_count': 0,  # Don't count invoices twice
                'sales_amount': 0.0,  # Don't show sales twice
                'total_sales_amount': 0.0,  # For opening period, total_sales MUST be zero
                'settled_amount': opening_during['settled_amount'],
                'amount_downpayment': 0.0,  # Don't show down payment twice
                'amount_downpayment_deducted': 0.0,  # Don't show down payment deducted twice
                'balance': 0.0 - opening_during['settled_amount'],
                'period_balance': opening_period_balance,  # Roll up from previous period
                'as_of_date': self.as_of_date,
                'partner_id': opening_during['partner_id'],
                'project_id': opening_during['project_id'],
                'is_opening': True,
                'description': 'Opening - Settlement during period',
                'is_breakdown': False
            })
            opening_settlement_count += 1
            
            # Update running period balance for this group
            period_balances[opening_key] = opening_period_balance
            
            # Track created periods for breakdown linking
            if group_by == 'customer':
                created_periods[(opening_key, opening_during['year'], opening_during['month'], False)] = opening_period.id
            elif group_by == 'project':
                created_periods[(opening_key, opening_during['year'], opening_during['month'], False)] = opening_period.id
            else:
                created_periods[(opening_during['year'], opening_during['month'], False)] = opening_period.id
            
            # Add invoice breakdown for opening periods if needed
            breakdown_count = 0
            if self.show_invoice_breakdown and opening_key in opening_invoices:
                for inv_data in opening_invoices[opening_key]:
                    invoice = inv_data['invoice']
                    
                    # Create opening breakdown (settlement during opening)
                    if inv_data['during_amount'] > 0:
                        breakdown_count += 1
                        # For invoice breakdowns, balance is now: sales - settled + dp - dpd
                        # In this case, it's 0 (sales) - settled + 0 (dp) - 0 (dpd) = -settled
                        breakdown_balance = 0.0 - inv_data['during_amount']
                        
                        self.env['wilco.customer.invoice.summary'].create({
                            'year': opening_during['year'],
                            'month': opening_during['month'],
                            'invoice_count': 0,
                            'sales_amount': 0.0,  # Don't count sales twice
                            'total_sales_amount': 0.0,
                            'settled_amount': inv_data['during_amount'],
                            'amount_downpayment': 0.0,  # Don't count down payment twice
                            'amount_downpayment_deducted': 0.0,  # Don't count down payment deducted twice
                            'balance': breakdown_balance,  # For breakdowns: sales - settled
                            'period_balance': 0.0,  # Not used for breakdowns
                            'as_of_date': self.as_of_date,
                            'partner_id': invoice.partner_id.id,
                            'project_id': invoice.wilco_project_id.id if hasattr(invoice, 'wilco_project_id') and invoice.wilco_project_id else False,
                            'is_opening': True,
                            'description': 'Opening Settlement Breakdown',
                            'is_breakdown': True,
                            'parent_period_id': opening_period.id,
                            'invoice_id': invoice.id,
                            'invoice_date': invoice.invoice_date,
                            'invoice_number': invoice.name,
                            'settled_dates': self._get_settlement_dates(invoice, self.as_of_date)
                        })
            
            _logger.info(f"Created {breakdown_count} invoice breakdowns for opening period")
        
        _logger.info(f"Created {opening_historical_count} historical opening periods and {opening_settlement_count} settlement opening periods")
        
        # Sort keys for consistent processing
        sorted_keys = sorted(invoice_data.keys())
        _logger.info(f"Processing {len(sorted_keys)} regular periods")
        reg_period_count = 0
        reg_breakdown_count = 0
        
        # Process regular periods after opening periods
        for key in sorted_keys:
            # Extract key components based on grouping
            period_key = None
            if group_by == 'customer':
                customer_id, year, month = key
                group_key = customer_id
                period_key = (customer_id, year, month, False)
            elif group_by == 'project':
                project_id, year, month = key
                group_key = project_id
                period_key = (project_id, year, month, False)
            else:  # 'period'
                year, month = key
                group_key = 'default'
                period_key = (year, month, False)
            
            # Skip periods before the opening period if using opening period
            if self.use_opening_period and opening_start_date:
                if (year < self.opening_year or 
                    (year == self.opening_year and month < opening_month_int)):
                    _logger.info(f"Skipping period {year}-{month} as it's before opening period {self.opening_year}-{opening_month_int}")
                    continue
            
            # Initialize tracking if not exists (for groups without opening records)
            if group_key not in period_balances:
                period_balances[group_key] = 0.0
                sales_totals[group_key] = 0.0
            
            # Current period calculation
            current_data = invoice_data[key]
            current_sales = current_data['sales_amount']
            current_settled = current_data['settled_amount']
            current_downpayment = current_data['amount_downpayment']
            current_downpayment_deducted = current_data['amount_downpayment_deducted']
            
            # Update running totals for this group
            sales_totals[group_key] += current_sales
            
            # Calculate period balance with new formula: 
            # previous balance + (sales - settled + dp - dpd)
            new_period_balance = (
                period_balances[group_key] 
                + current_sales 
                - current_settled 
                + current_downpayment 
                - current_downpayment_deducted
            )
            
            _logger.info(f"Creating regular period for {year}-{month}: sales={current_sales}, settled={current_settled}, dp={current_downpayment}, dpd={current_downpayment_deducted}")
            _logger.info(f"Previous balance: {period_balances[group_key]}, New balance: {new_period_balance}")
            
            # Create summary record
            period_summary = self.env['wilco.customer.invoice.summary'].create({
                'year': current_data['year'],
                'month': current_data['month'],
                'invoice_count': current_data['invoice_count'],
                'sales_amount': current_data['sales_amount'],
                'total_sales_amount': sales_totals[group_key],
                'settled_amount': current_data['settled_amount'],
                'amount_downpayment': current_data['amount_downpayment'],
                'amount_downpayment_deducted': current_data['amount_downpayment_deducted'],
                'balance': (
                    current_data['sales_amount'] 
                    - current_data['settled_amount'] 
                    + current_data['amount_downpayment'] 
                    - current_data['amount_downpayment_deducted']
                ),
                'period_balance': new_period_balance,
                'as_of_date': self.as_of_date,
                'partner_id': current_data['partner_id'],
                'project_id': current_data['project_id'],
                'is_opening': False,
                'description': False,
                'is_breakdown': False
            })
            reg_period_count += 1
            
            # Update running period balance for next period
            period_balances[group_key] = new_period_balance
            
            # Store period for breakdown linking
            created_periods[period_key] = period_summary.id
            
            # Create invoice breakdowns if needed
            period_breakdown_count = 0
            if self.show_invoice_breakdown and key in period_invoices:
                for inv_data in period_invoices[key]:
                    invoice = inv_data['invoice']
                    settled_amount = inv_data['settled_amount']
                    downpayment = inv_data.get('amount_downpayment', 0.0)
                    downpayment_deducted = inv_data.get('amount_downpayment_deducted', 0.0)
                    sales_amount = inv_data.get('sales_amount', invoice.amount_total)
                    
                    # For invoice breakdowns, balance with new formula: 
                    # sales - settled + dp - dpd
                    breakdown_balance = (
                        sales_amount 
                        - settled_amount 
                        + downpayment 
                        - downpayment_deducted
                    )
                    
                    self.env['wilco.customer.invoice.summary'].create({
                        'year': year,
                        'month': month,
                        'invoice_count': 0,
                        'sales_amount': sales_amount,
                        'total_sales_amount': 0.0,  # No total sales for individual invoices
                        'settled_amount': settled_amount,
                        'amount_downpayment': downpayment,
                        'amount_downpayment_deducted': downpayment_deducted,
                        'balance': breakdown_balance,
                        'period_balance': 0.0,  # Not used for breakdowns
                        'as_of_date': self.as_of_date,
                        'partner_id': invoice.partner_id.id,
                        'project_id': invoice.wilco_project_id.id if hasattr(invoice, 'wilco_project_id') and invoice.wilco_project_id else False,
                        'is_opening': False,
                        'description': False,
                        'is_breakdown': True,
                        'parent_period_id': period_summary.id,
                        'invoice_id': invoice.id,
                        'invoice_date': invoice.invoice_date,
                        'invoice_number': invoice.name,
                        'settled_dates': self._get_settlement_dates(invoice, self.as_of_date)
                    })
                    period_breakdown_count += 1
                    reg_breakdown_count += 1
            
            _logger.info(f"Created {period_breakdown_count} invoice breakdowns for period {year}-{month}")
        
        _logger.info(f"Created {reg_period_count} regular periods with {reg_breakdown_count} invoice breakdowns")
        _logger.info("====== END GENERIC REPORT GENERATION ======")