from odoo import models, fields, api
from datetime import date, datetime, timedelta


class WilcoInvoiceSummaryWizard(models.TransientModel):
    _name = 'wilco.invoice.summary.wizard'
    _description = 'Customer Invoice Summary Wizard'

    as_of_date = fields.Date(string='As Of Date', required=True, default=fields.Date.today)
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('customer_rank', '>', 0)])
    
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
    
    # Group by customer option
    show_by_customer = fields.Boolean(string='Show by Customer', default=False,
                                      help="Group data by customer instead of just by period")
    
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
        
        # Return action to open the list view without any grouping
        action = {
            'name': 'Customer Invoice Summary',
            'type': 'ir.actions.act_window',
            'res_model': 'wilco.customer.invoice.summary',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': {},
        }
        
        return action
        
    def _wilco_generate_invoice_summary_data(self):
        """
        Generate the invoice summary data grouped by year and month.
        Calculate settled amounts based on the as_of_date.
        Handles opening periods and prevents generating periods after as-of-date.
        """
        self.ensure_one()
        
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ]
        
        # Add date filter to only get invoices up to as_of_date
        domain.append(('invoice_date', '<=', self.as_of_date))
        
        # Only filter by partner if not showing by customer and a partner is selected
        if not self.show_by_customer and self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        
        invoices = self.env['account.move'].search(domain)
        
        # Convert opening_month to integer for comparisons
        opening_month_int = int(self.opening_month) if self.use_opening_period and self.opening_month else 0
        
        # Process invoices differently depending on whether we're showing by customer
        if self.show_by_customer:
            self._generate_by_customer(invoices, opening_month_int)
        else:
            self._generate_by_period(invoices, opening_month_int)
    
    def _generate_by_period(self, invoices, opening_month_int):
        """Generate invoice summary by period only (original method)"""
        # Group invoices by year and month
        invoice_data = {}
        opening_data_before = {
            'year': self.opening_year if self.use_opening_period else 0,
            'month': opening_month_int,  # Store as integer for the model
            'invoice_count': 0,
            'sales_amount': 0.0,  # Sales amount for all invoices before opening period
            'settled_amount': 0.0,  # Amount settled BEFORE opening period start
            'is_opening': True,
            'is_historical': True,  # Flag for historical opening row
            'partner_id': self.partner_id.id if self.partner_id else False,
        }
        
        opening_data_during = {
            'year': self.opening_year if self.use_opening_period else 0,
            'month': opening_month_int,  # Store as integer for the model
            'invoice_count': 0,
            'sales_amount': 0.0,  # Same as opening_data_before sales amount
            'settled_amount': 0.0,  # Amount settled DURING opening period to as-of-date
            'is_opening': True,
            'is_historical': False,  # Flag for regular opening row
            'partner_id': self.partner_id.id if self.partner_id else False,
        }
        
        # Calculate the opening period start date and day before
        opening_start_date = date(self.opening_year, opening_month_int, 1)
        day_before_opening = opening_start_date - timedelta(days=1)
        
        for invoice in invoices:
            # Skip invoices without invoice_date
            if not invoice.invoice_date:
                continue
                
            key = (invoice.invoice_date.year, invoice.invoice_date.month)
            
            # Check if this invoice belongs to opening period
            is_opening_period = False
            if self.use_opening_period:
                if (invoice.invoice_date.year < self.opening_year or 
                    (invoice.invoice_date.year == self.opening_year and 
                     invoice.invoice_date.month < opening_month_int)):
                    is_opening_period = True
            
            if is_opening_period:
                # Add to opening data counts and total sales
                opening_data_before['invoice_count'] += 1
                opening_data_before['sales_amount'] += invoice.amount_total
                opening_data_during['sales_amount'] += invoice.amount_total
                
                # Calculate settlement BEFORE the opening period
                before_amount = self._wilco_compute_settled_amount_as_of_date(invoice, day_before_opening)
                opening_data_before['settled_amount'] += before_amount
                
                # Calculate settlement FROM opening period start TO as_of_date
                total_settled = self._wilco_compute_settled_amount_as_of_date(invoice, self.as_of_date)
                during_amount = total_settled - before_amount
                opening_data_during['settled_amount'] += during_amount
            else:
                # Add to regular periods
                if key not in invoice_data:
                    invoice_data[key] = {
                        'year': key[0],
                        'month': key[1],
                        'invoice_count': 0,
                        'sales_amount': 0.0,
                        'settled_amount': 0.0,
                        'is_opening': False,
                        'is_historical': False,
                        'partner_id': self.partner_id.id if self.partner_id else False,
                    }
                
                invoice_data[key]['invoice_count'] += 1
                invoice_data[key]['sales_amount'] += invoice.amount_total
                
                # Calculate settled amount based on as_of_date using proper reconciliation data
                settled_amount = self._wilco_compute_settled_amount_as_of_date(invoice, self.as_of_date)
                invoice_data[key]['settled_amount'] += settled_amount
        
        # Get all keys and sort them
        all_keys = list(invoice_data.keys())
        sorted_keys = sorted(all_keys)
        
        # Create summary records
        balance = 0
        total_sales = 0
        
        # First create opening records if needed
        if self.use_opening_period and opening_data_before['sales_amount'] > 0:
            # First row: Historical row (before opening period)
            balance_before = opening_data_before['sales_amount'] - opening_data_before['settled_amount']
            
            self.env['wilco.customer.invoice.summary'].create({
                'year': opening_data_before['year'],
                'month': opening_data_before['month'],
                'invoice_count': opening_data_before['invoice_count'],
                'sales_amount': opening_data_before['sales_amount'],  # Show actual sales amount
                'total_sales_amount': 0.0,  # For opening period, total_sales MUST be zero
                'settled_amount': opening_data_before['settled_amount'],
                'balance': balance_before,
                'as_of_date': self.as_of_date,
                'partner_id': opening_data_before['partner_id'],
                'is_opening': True,
                'description': 'Historical - Settlement before opening'
            })
            
            # Second row: Opening period (settlement during opening period)
            balance_during = opening_data_during['sales_amount'] - (opening_data_before['settled_amount'] + opening_data_during['settled_amount'])
            
            self.env['wilco.customer.invoice.summary'].create({
                'year': opening_data_during['year'],
                'month': opening_data_during['month'],
                'invoice_count': 0,  # Don't count invoices twice
                'sales_amount': 0.0,  # Don't show sales twice
                'total_sales_amount': 0.0,  # For opening period, total_sales MUST be zero
                'settled_amount': opening_data_during['settled_amount'],
                'balance': balance_during,
                'as_of_date': self.as_of_date,
                'partner_id': opening_data_during['partner_id'],
                'is_opening': True,
                'description': 'Opening - Settlement during period'
            })
            
            # Set initial balance for regular periods
            balance = balance_during
            
            # Do NOT include opening sales in total_sales for regular periods
            total_sales = 0
        
        # Then create regular period records
        for key in sorted_keys:
            # Skip periods before the opening period if using opening period
            if self.use_opening_period:
                if (key[0] < self.opening_year or 
                    (key[0] == self.opening_year and key[1] < opening_month_int)):
                    continue
            
            # Current period calculation
            current_sales = invoice_data[key]['sales_amount']
            current_settled = invoice_data[key]['settled_amount']
            
            # Update running totals
            total_sales += current_sales
            balance = balance + current_sales - current_settled
            
            # Create summary record
            summary = self.env['wilco.customer.invoice.summary'].create({
                'year': invoice_data[key]['year'],
                'month': invoice_data[key]['month'],
                'invoice_count': invoice_data[key]['invoice_count'],
                'sales_amount': invoice_data[key]['sales_amount'],
                'total_sales_amount': total_sales,
                'settled_amount': invoice_data[key]['settled_amount'],
                'balance': balance,
                'as_of_date': self.as_of_date,
                'partner_id': invoice_data[key]['partner_id'],
                'is_opening': False,
                'description': False
            })
    
    def _generate_by_customer(self, invoices, opening_month_int):
        """Generate invoice summary by customer and period"""
        # Dictionary to store data: {(customer_id, year, month): data}
        customer_invoice_data = {}
        customer_opening_before = {}  # {customer_id: opening_data_before}
        customer_opening_during = {}  # {customer_id: opening_data_during}
        
        # Calculate the opening period start date and day before
        opening_start_date = date(self.opening_year, opening_month_int, 1)
        day_before_opening = opening_start_date - timedelta(days=1)
        
        # Group by customer, year, month
        for invoice in invoices:
            # Skip invoices without invoice_date
            if not invoice.invoice_date:
                continue
                
            customer_id = invoice.partner_id.id
            year = invoice.invoice_date.year
            month = invoice.invoice_date.month
            key = (customer_id, year, month)
            
            # Check if this invoice belongs to opening period
            is_opening_period = False
            if self.use_opening_period:
                if (year < self.opening_year or 
                    (year == self.opening_year and month < opening_month_int)):
                    is_opening_period = True
            
            if is_opening_period:
                # Initialize customer opening data if not exists
                if customer_id not in customer_opening_before:
                    customer_opening_before[customer_id] = {
                        'year': self.opening_year if self.use_opening_period else 0,
                        'month': opening_month_int,
                        'invoice_count': 0,
                        'sales_amount': 0.0,
                        'settled_amount': 0.0,
                        'is_opening': True,
                        'is_historical': True,
                        'partner_id': customer_id,
                    }
                    
                    customer_opening_during[customer_id] = {
                        'year': self.opening_year if self.use_opening_period else 0,
                        'month': opening_month_int,
                        'invoice_count': 0,
                        'sales_amount': 0.0,
                        'settled_amount': 0.0,
                        'is_opening': True,
                        'is_historical': False,
                        'partner_id': customer_id,
                    }
                
                # Add to opening data counts and sales
                customer_opening_before[customer_id]['invoice_count'] += 1
                customer_opening_before[customer_id]['sales_amount'] += invoice.amount_total
                customer_opening_during[customer_id]['sales_amount'] += invoice.amount_total
                
                # Calculate settlement BEFORE opening period
                before_amount = self._wilco_compute_settled_amount_as_of_date(invoice, day_before_opening)
                customer_opening_before[customer_id]['settled_amount'] += before_amount
                
                # Calculate settlement DURING opening period to as-of-date
                total_settled = self._wilco_compute_settled_amount_as_of_date(invoice, self.as_of_date)
                during_amount = total_settled - before_amount
                customer_opening_during[customer_id]['settled_amount'] += during_amount
            else:
                # Add to regular periods by customer
                if key not in customer_invoice_data:
                    customer_invoice_data[key] = {
                        'year': year,
                        'month': month,
                        'invoice_count': 0,
                        'sales_amount': 0.0,
                        'settled_amount': 0.0,
                        'is_opening': False,
                        'is_historical': False,
                        'partner_id': customer_id,
                    }
                
                customer_invoice_data[key]['invoice_count'] += 1
                customer_invoice_data[key]['sales_amount'] += invoice.amount_total
                
                # Calculate settled amount
                settled_amount = self._wilco_compute_settled_amount_as_of_date(invoice, self.as_of_date)
                customer_invoice_data[key]['settled_amount'] += settled_amount
        
        # Process customer opening records
        for customer_id, opening_before in customer_opening_before.items():
            opening_during = customer_opening_during[customer_id]
            
            # First row: Historical row (before opening period)
            balance_before = opening_before['sales_amount'] - opening_before['settled_amount']
            
            self.env['wilco.customer.invoice.summary'].create({
                'year': opening_before['year'],
                'month': opening_before['month'],
                'invoice_count': opening_before['invoice_count'],
                'sales_amount': opening_before['sales_amount'],  # Show actual sales
                'total_sales_amount': 0.0,  # For opening period, total_sales MUST be zero
                'settled_amount': opening_before['settled_amount'],
                'balance': balance_before,
                'as_of_date': self.as_of_date,
                'partner_id': opening_before['partner_id'],
                'is_opening': True,
                'description': 'Historical - Settlement before opening'
            })
            
            # Second row: Opening period (settlement during opening period)
            balance_during = opening_during['sales_amount'] - (opening_before['settled_amount'] + opening_during['settled_amount'])
            
            self.env['wilco.customer.invoice.summary'].create({
                'year': opening_during['year'],
                'month': opening_during['month'],
                'invoice_count': 0,  # Don't count invoices twice
                'sales_amount': 0.0,  # Don't show sales twice
                'total_sales_amount': 0.0,  # For opening period, total_sales MUST be zero
                'settled_amount': opening_during['settled_amount'],
                'balance': balance_during,
                'as_of_date': self.as_of_date,
                'partner_id': opening_during['partner_id'],
                'is_opening': True,
                'description': 'Opening - Settlement during period'
            })
        
        # Process customer regular records
        # First sort by customer, then by year and month
        customer_totals = {}  # {customer_id: {'total_sales': 0.0, 'balance': 0.0}}
        
        # Initialize customer totals with balance but not sales
        for customer_id, opening_before in customer_opening_before.items():
            opening_during = customer_opening_during[customer_id]
            customer_totals[customer_id] = {
                'total_sales': 0.0,  # Do NOT include opening sales in total
                'balance': opening_before['sales_amount'] - (opening_before['settled_amount'] + opening_during['settled_amount'])
            }
        
        # Create summary records
        sorted_keys = sorted(customer_invoice_data.keys())
        for key in sorted_keys:
            customer_id, year, month = key
            
            # Skip periods before the opening period if using opening period
            if self.use_opening_period:
                if (year < self.opening_year or 
                    (year == self.opening_year and month < opening_month_int)):
                    continue
            
            # Initialize customer totals if not exists (for customers without opening records)
            if customer_id not in customer_totals:
                customer_totals[customer_id] = {
                    'total_sales': 0.0,
                    'balance': 0.0
                }
            
            # Update customer running totals
            current_data = customer_invoice_data[key]
            customer_totals[customer_id]['total_sales'] += current_data['sales_amount']
            customer_totals[customer_id]['balance'] += (current_data['sales_amount'] - current_data['settled_amount'])
            
            # Create summary record
            self.env['wilco.customer.invoice.summary'].create({
                'year': current_data['year'],
                'month': current_data['month'],
                'invoice_count': current_data['invoice_count'],
                'sales_amount': current_data['sales_amount'],
                'total_sales_amount': customer_totals[customer_id]['total_sales'],
                'settled_amount': current_data['settled_amount'],
                'balance': customer_totals[customer_id]['balance'],
                'as_of_date': self.as_of_date,
                'partner_id': current_data['partner_id'],
                'is_opening': False,
                'description': False
            })
    
    def _wilco_compute_settled_amount_as_of_date(self, invoice, as_of_date):
        """
        Calculate how much of an invoice has been settled as of a specific date.
        Following naming conventions from PLANNING.md.
        
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
            
        # Get the total invoice amount
        invoice_amount = abs(sum(receivable_line.mapped('amount_currency')))
        
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