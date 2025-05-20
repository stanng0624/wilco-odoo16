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
    
    # Group by sales account option
    show_by_sales_account = fields.Boolean(string='Show by Sales Account', default=False,
                                          help="Group data by sales account and show account-specific amounts")
    
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
        if self.show_by_sales_account:
            context['search_default_group_by_sales_account'] = 1
        elif self.show_by_customer:
            context['search_default_group_by_partner'] = 1
        
        action['context'] = context
        
        return action
        
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
        
        invoices = self.env['account.move'].search(domain)
        
        # Convert opening_month to integer for comparisons
        opening_month_int = int(self.opening_month) if self.use_opening_period and self.opening_month else 0
        
        # Process invoices differently depending on the grouping option
        if self.show_by_sales_account:
            self._generate_by_sales_account(invoices, opening_month_int)
        elif self.show_by_customer:
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
        
        # Store invoices by period for breakdown
        period_invoices = {}
        opening_invoices = []
        
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
                
                # Store invoice for breakdown if needed
                # Note: We're only storing for the opening period breakdown (2: Opening),
                # not for historical breakdown (1: Historical)
                if self.show_invoice_breakdown:
                    opening_invoices.append({
                        'invoice': invoice,
                        'before_amount': before_amount,
                        'during_amount': during_amount,
                        'total_settled': total_settled
                    })
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
                    
                    if self.show_invoice_breakdown:
                        period_invoices[key] = []
                
                invoice_data[key]['invoice_count'] += 1
                invoice_data[key]['sales_amount'] += invoice.amount_total
                
                # Calculate settled amount based on as_of_date using proper reconciliation data
                settled_amount = self._wilco_compute_settled_amount_as_of_date(invoice, self.as_of_date)
                invoice_data[key]['settled_amount'] += settled_amount
                
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
                            'settled_amount': settled_amount
                        })
        
        # Get all keys and sort them
        all_keys = list(invoice_data.keys())
        sorted_keys = sorted(all_keys)
        
        # Create summary records
        period_balance = 0  # Running balance for period_balance
        total_sales = 0
        
        # First create opening records if needed
        if self.use_opening_period and opening_data_before['sales_amount'] > 0:
            # First row: Historical row (before opening period)
            historical_period_balance = opening_data_before['sales_amount'] - opening_data_before['settled_amount']
            
            historical_period = self.env['wilco.customer.invoice.summary'].create({
                'year': opening_data_before['year'],
                'month': opening_data_before['month'],
                'invoice_count': opening_data_before['invoice_count'],
                'sales_amount': opening_data_before['sales_amount'],  # Show actual sales amount
                'total_sales_amount': 0.0,  # For opening period, total_sales MUST be zero
                'settled_amount': opening_data_before['settled_amount'],
                'balance': opening_data_before['sales_amount'] - opening_data_before['settled_amount'],  # Update: Show sales - settled
                'period_balance': historical_period_balance,  # Initial period balance
                'as_of_date': self.as_of_date,
                'partner_id': opening_data_before['partner_id'],
                'is_opening': True,
                'description': 'Historical - Settlement before opening',
                'is_breakdown': False
            })
            
            # Update running period balance for next period
            period_balance = historical_period_balance
            
            # Second row: Opening period (settlement during opening period)
            # For opening period, add the settlement during opening to the running period balance
            opening_period_balance = period_balance - opening_data_during['settled_amount']
            
            opening_period = self.env['wilco.customer.invoice.summary'].create({
                'year': opening_data_during['year'],
                'month': opening_data_during['month'],
                'invoice_count': 0,  # Don't count invoices twice
                'sales_amount': 0.0,  # Don't show sales twice
                'total_sales_amount': 0.0,  # For opening period, total_sales MUST be zero
                'settled_amount': opening_data_during['settled_amount'],
                'balance': 0.0 - opening_data_during['settled_amount'],  # Update: For opening period, this would be 0 (sales) - settled
                'period_balance': opening_period_balance,  # Roll up from previous period
                'as_of_date': self.as_of_date,
                'partner_id': opening_data_during['partner_id'],
                'is_opening': True,
                'description': 'Opening - Settlement during period',
                'is_breakdown': False
            })
            
            # Update running period balance for next period
            period_balance = opening_period_balance
            
            # Add invoice breakdown for opening periods if needed
            # Note: We're only creating breakdowns for the opening period (2: Opening),
            # not for historical opening records (1: Historical)
            if self.show_invoice_breakdown:
                # Skip the historical period breakdowns
                # Only create breakdowns for the regular opening period
                for inv_data in opening_invoices:
                    invoice = inv_data['invoice']
                    # We skip creating historical invoice breakdowns
                    
                    # Create opening breakdown (settlement during opening)
                    if inv_data['during_amount'] > 0:
                        # For invoice breakdowns, balance is simply invoice amount - settled amount
                        # In this case, it's 0 (sales) - settled = -settled
                        breakdown_balance = 0.0 - inv_data['during_amount']
                        
                        self.env['wilco.customer.invoice.summary'].create({
                            'year': opening_data_during['year'],
                            'month': opening_data_during['month'],
                            'invoice_count': 0,
                            'sales_amount': 0.0,  # Don't count sales twice
                            'total_sales_amount': 0.0,
                            'settled_amount': inv_data['during_amount'],
                            'balance': breakdown_balance,  # For breakdowns: sales - settled
                            'period_balance': 0.0,  # Not used for breakdowns
                            'as_of_date': self.as_of_date,
                            'partner_id': invoice.partner_id.id,
                            'is_opening': True,
                            'description': 'Opening Settlement Breakdown',
                            'is_breakdown': True,
                            'parent_period_id': opening_period.id,
                            'invoice_id': invoice.id,
                            'invoice_date': invoice.invoice_date,
                            'invoice_number': invoice.name,
                            'settled_dates': self._get_settlement_dates(invoice, self.as_of_date)
                        })
            
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
            
            # Calculate period balance: previous period balance + current sales - current settled
            period_balance = period_balance + current_sales - current_settled
            
            # Create summary record
            summary = self.env['wilco.customer.invoice.summary'].create({
                'year': invoice_data[key]['year'],
                'month': invoice_data[key]['month'],
                'invoice_count': invoice_data[key]['invoice_count'],
                'sales_amount': invoice_data[key]['sales_amount'],
                'total_sales_amount': total_sales,
                'settled_amount': invoice_data[key]['settled_amount'],
                'balance': invoice_data[key]['sales_amount'] - invoice_data[key]['settled_amount'],  # Update: Show sales - settled for the period
                'period_balance': period_balance,  # Running balance from previous periods
                'as_of_date': self.as_of_date,
                'partner_id': invoice_data[key]['partner_id'],
                'is_opening': False,
                'description': False,
                'is_breakdown': False
            })
            
            # Create invoice breakdowns if needed
            if self.show_invoice_breakdown and key in period_invoices:
                for inv_data in period_invoices[key]:
                    invoice = inv_data['invoice']
                    settled_amount = inv_data['settled_amount']
                    
                    # For invoice breakdowns, balance is simply invoice amount - settled amount
                    breakdown_balance = invoice.amount_total - settled_amount
                    
                    self.env['wilco.customer.invoice.summary'].create({
                        'year': key[0],
                        'month': key[1],
                        'invoice_count': 0,
                        'sales_amount': invoice.amount_total,
                        'total_sales_amount': 0.0,  # No total sales for individual invoices
                        'settled_amount': settled_amount,
                        'balance': breakdown_balance,  # For breakdowns: sales - settled
                        'period_balance': 0.0,  # Not used for breakdowns
                        'as_of_date': self.as_of_date,
                        'partner_id': invoice.partner_id.id,
                        'is_opening': False,
                        'description': False,
                        'is_breakdown': True,
                        'parent_period_id': summary.id,
                        'invoice_id': invoice.id,
                        'invoice_date': invoice.invoice_date,
                        'invoice_number': invoice.name,
                        'settled_dates': self._get_settlement_dates(invoice, self.as_of_date)
                    })
    
    def _generate_by_customer(self, invoices, opening_month_int):
        """Generate invoice summary by customer and period"""
        # Dictionary to store data: {(customer_id, year, month): data}
        customer_invoice_data = {}
        customer_opening_before = {}  # {customer_id: opening_data_before}
        customer_opening_during = {}  # {customer_id: opening_data_during}
        
        # For invoice breakdown
        customer_period_invoices = {}  # {(customer_id, year, month): [invoice_data]}
        customer_opening_invoices = {}  # {customer_id: [invoice_data]}
        
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
                    
                    if self.show_invoice_breakdown:
                        customer_opening_invoices[customer_id] = []
                
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
                
                # Store invoice for breakdown if needed
                if self.show_invoice_breakdown:
                    # Check if this invoice is already in the list
                    existing_invoice = next((x for x in customer_opening_invoices[customer_id] if x['invoice'] == invoice), None)
                    if existing_invoice:
                        # If invoice already exists, update the amounts
                        existing_invoice['before_amount'] += before_amount
                        existing_invoice['during_amount'] += during_amount
                        existing_invoice['total_settled'] += total_settled
                    else:
                        # Add new invoice entry
                        customer_opening_invoices[customer_id].append({
                            'invoice': invoice,
                            'before_amount': before_amount,
                            'during_amount': during_amount,
                            'total_settled': total_settled
                        })
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
                    
                    if self.show_invoice_breakdown:
                        customer_period_invoices[key] = []
                
                customer_invoice_data[key]['invoice_count'] += 1
                customer_invoice_data[key]['sales_amount'] += invoice.amount_total
                
                # Calculate settled amount
                settled_amount = self._wilco_compute_settled_amount_as_of_date(invoice, self.as_of_date)
                customer_invoice_data[key]['settled_amount'] += settled_amount
                
                # Store invoice for breakdown if needed
                if self.show_invoice_breakdown:
                    # Check if this invoice is already in the list
                    existing_invoice = next((x for x in customer_period_invoices[key] if x['invoice'] == invoice), None)
                    if existing_invoice:
                        # If invoice already exists, don't add it again
                        pass
                    else:
                        # Add new invoice entry
                        customer_period_invoices[key].append({
                            'invoice': invoice,
                            'settled_amount': settled_amount
                        })
        
        # Store created periods for invoice breakdown linking
        created_periods = {}  # {(customer_id, year, month, is_historical): record_id}
        
        # Track period balance by customer
        customer_period_balances = {}  # {customer_id: current_period_balance}
        
        # Process customer opening records
        for customer_id, opening_before in customer_opening_before.items():
            opening_during = customer_opening_during[customer_id]
            
            # Initialize period balance for this customer
            customer_period_balances[customer_id] = 0.0
            
            # First row: Historical row (before opening period)
            historical_period_balance = opening_before['sales_amount'] - opening_before['settled_amount']
            
            historical_period = self.env['wilco.customer.invoice.summary'].create({
                'year': opening_before['year'],
                'month': opening_before['month'],
                'invoice_count': opening_before['invoice_count'],
                'sales_amount': opening_before['sales_amount'],  # Show actual sales
                'total_sales_amount': 0.0,  # For opening period, total_sales MUST be zero
                'settled_amount': opening_before['settled_amount'],
                'balance': opening_before['sales_amount'] - opening_before['settled_amount'],  # Update: Show sales - settled
                'period_balance': historical_period_balance,  # Initial period balance
                'as_of_date': self.as_of_date,
                'partner_id': opening_before['partner_id'],
                'is_opening': True,
                'description': 'Historical - Settlement before opening',
                'is_breakdown': False
            })
            
            # Update running period balance for this customer
            customer_period_balances[customer_id] = historical_period_balance
            
            created_periods[(customer_id, opening_before['year'], opening_before['month'], True)] = historical_period.id
            
            # Second row: Opening period (settlement during opening period)
            opening_period_balance = customer_period_balances[customer_id] - opening_during['settled_amount']
            
            opening_period = self.env['wilco.customer.invoice.summary'].create({
                'year': opening_during['year'],
                'month': opening_during['month'],
                'invoice_count': 0,  # Don't count invoices twice
                'sales_amount': 0.0,  # Don't show sales twice
                'total_sales_amount': 0.0,  # For opening period, total_sales MUST be zero
                'settled_amount': opening_during['settled_amount'],
                'balance': 0.0 - opening_during['settled_amount'],  # Update: For opening period, this would be 0 (sales) - settled
                'period_balance': opening_period_balance,  # Roll up from previous period
                'as_of_date': self.as_of_date,
                'partner_id': opening_during['partner_id'],
                'is_opening': True,
                'description': 'Opening - Settlement during period',
                'is_breakdown': False
            })
            
            # Update running period balance for this customer
            customer_period_balances[customer_id] = opening_period_balance
            
            created_periods[(customer_id, opening_during['year'], opening_during['month'], False)] = opening_period.id
            
            # Add invoice breakdown for opening periods if needed
            # Note: We're only creating breakdowns for the opening period (2: Opening),
            # not for historical opening records (1: Historical)
            if self.show_invoice_breakdown and customer_id in customer_opening_invoices:
                # Skip the historical period breakdowns
                # Only create breakdowns for the regular opening period
                for inv_data in customer_opening_invoices[customer_id]:
                    invoice = inv_data['invoice']
                    # We skip creating historical invoice breakdowns
                    
                    # Create opening breakdown (settlement during opening)
                    if inv_data['during_amount'] > 0:
                        # For invoice breakdowns, balance is simply invoice amount - settled amount
                        # In this case, it's 0 (sales) - settled = -settled
                        breakdown_balance = 0.0 - inv_data['during_amount']
                        
                        self.env['wilco.customer.invoice.summary'].create({
                            'year': opening_during['year'],
                            'month': opening_during['month'],
                            'invoice_count': 0,
                            'sales_amount': 0.0,  # Don't count sales twice
                            'total_sales_amount': 0.0,
                            'settled_amount': inv_data['during_amount'],
                            'balance': breakdown_balance,  # For breakdowns: sales - settled
                            'period_balance': 0.0,  # Not used for breakdowns
                            'as_of_date': self.as_of_date,
                            'partner_id': invoice.partner_id.id,
                            'is_opening': True,
                            'description': 'Opening Settlement Breakdown',
                            'is_breakdown': True,
                            'parent_period_id': opening_period.id,
                            'invoice_id': invoice.id,
                            'invoice_date': invoice.invoice_date,
                            'invoice_number': invoice.name,
                            'settled_dates': self._get_settlement_dates(invoice, self.as_of_date)
                        })
        
        # Track customer sales totals
        customer_sales_totals = {}  # {customer_id: total_sales_excluding_opening}
        
        # Initialize customer totals
        for customer_id in customer_opening_before.keys():
            customer_sales_totals[customer_id] = 0.0
        
        # Create summary records
        sorted_keys = sorted(customer_invoice_data.keys())
        for key in sorted_keys:
            customer_id, year, month = key
            
            # Skip periods before the opening period if using opening period
            if self.use_opening_period:
                if (year < self.opening_year or 
                    (year == self.opening_year and month < opening_month_int)):
                    continue
            
            # Initialize tracking if not exists (for customers without opening records)
            if customer_id not in customer_period_balances:
                customer_period_balances[customer_id] = 0.0
                customer_sales_totals[customer_id] = 0.0
            
            # Current period calculation
            current_data = customer_invoice_data[key]
            current_sales = current_data['sales_amount']
            current_settled = current_data['settled_amount']
            
            # Update running totals for this customer
            customer_sales_totals[customer_id] += current_sales
            
            # Calculate period balance: previous period balance + current sales - current settled
            new_period_balance = customer_period_balances[customer_id] + current_sales - current_settled
            
            # Create summary record
            period_summary = self.env['wilco.customer.invoice.summary'].create({
                'year': current_data['year'],
                'month': current_data['month'],
                'invoice_count': current_data['invoice_count'],
                'sales_amount': current_data['sales_amount'],
                'total_sales_amount': customer_sales_totals[customer_id],
                'settled_amount': current_data['settled_amount'],
                'balance': current_data['sales_amount'] - current_data['settled_amount'],  # Update: Show sales - settled for the period
                'period_balance': new_period_balance,  # Running period balance for this customer
                'as_of_date': self.as_of_date,
                'partner_id': current_data['partner_id'],
                'is_opening': False,
                'description': False,
                'is_breakdown': False
            })
            
            # Update running period balance for next period
            customer_period_balances[customer_id] = new_period_balance
            
            created_periods[(customer_id, year, month, False)] = period_summary.id
            
            # Create invoice breakdowns if needed
            if self.show_invoice_breakdown and key in customer_period_invoices:
                for inv_data in customer_period_invoices[key]:
                    invoice = inv_data['invoice']
                    settled_amount = inv_data['settled_amount']
                    
                    # For invoice breakdowns, balance is simply invoice amount - settled amount
                    breakdown_balance = invoice.amount_total - settled_amount
                    
                    self.env['wilco.customer.invoice.summary'].create({
                        'year': year,
                        'month': month,
                        'invoice_count': 0,
                        'sales_amount': invoice.amount_total,
                        'total_sales_amount': 0.0,  # No total sales for individual invoices
                        'settled_amount': settled_amount,
                        'balance': breakdown_balance,  # For breakdowns: sales - settled
                        'period_balance': 0.0,  # Not used for breakdowns
                        'as_of_date': self.as_of_date,
                        'partner_id': invoice.partner_id.id,
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
        
    def _generate_by_sales_account(self, invoices, opening_month_int):
        """Generate invoice summary by sales account and period"""
        # Dictionary to store data: {(sales_account_id, year, month): data}
        account_invoice_data = {}
        account_opening_before = {}  # {sales_account_id: opening_data_before}
        account_opening_during = {}  # {sales_account_id: opening_data_during}
        
        # For invoice breakdown
        account_period_invoices = {}  # {(sales_account_id, year, month): [invoice_data]}
        account_opening_invoices = {}  # {sales_account_id: [invoice_data]}
        
        # Calculate the opening period start date and day before
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
                if (year < self.opening_year or 
                    (year == self.opening_year and month < opening_month_int)):
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

                if invoice.move_type == 'out_invoice':
                    account_amount = line.price_subtotal
                    # Calculate settled amount for this line
                    line_total_settled = self._wilco_compute_line_settled_amount_as_of_date(line, self.as_of_date)
                    line_before_settled = self._wilco_compute_line_settled_amount_as_of_date(line, day_before_opening) if is_opening_period else 0.0
                    line_during_settled = line_total_settled - line_before_settled if is_opening_period else line_total_settled
                elif invoice.move_type == 'out_refund':
                    account_amount = -line.price_subtotal
                    # Calculate settled amount for this line (negative for refunds)
                    line_total_settled = -self._wilco_compute_line_settled_amount_as_of_date(line, self.as_of_date)
                    line_before_settled = -self._wilco_compute_line_settled_amount_as_of_date(line, day_before_opening) if is_opening_period else 0.0
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
                            'is_opening': True,
                            'is_historical': False,
                            'partner_id': self.partner_id.id if self.partner_id else False,
                            'sales_account_id': account_id,
                        }
                        
                        if self.show_invoice_breakdown:
                            account_opening_invoices[account_id] = []
                    
                    # Add to opening data counts and sales
                    account_opening_before[account_id]['invoice_count'] += 1
                    account_opening_before[account_id]['sales_amount'] += account_amount
                    account_opening_during[account_id]['sales_amount'] += account_amount
                    
                    # Add line-specific settlement amounts
                    account_opening_before[account_id]['settled_amount'] += line_before_settled
                    account_opening_during[account_id]['settled_amount'] += line_during_settled
                    
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
                            existing_entry['before_amount'] += line_before_settled
                            existing_entry['during_amount'] += line_during_settled
                            existing_entry['total_settled'] += line_total_settled
                            existing_entry['account_amount'] += account_amount
                        else:
                            # Add new invoice entry
                            account_opening_invoices[account_id].append({
                                'invoice': invoice,
                                'before_amount': line_before_settled,
                                'during_amount': line_during_settled,
                                'total_settled': line_total_settled,
                                'account_id': account_id,
                                'account_amount': account_amount
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
                            'is_opening': False,
                            'is_historical': False,
                            'partner_id': self.partner_id.id if self.partner_id else False,
                            'sales_account_id': account_id,
                        }
                        
                        if self.show_invoice_breakdown:
                            account_period_invoices[key] = []
                    
                    account_invoice_data[key]['invoice_count'] += 1
                    account_invoice_data[key]['sales_amount'] += account_amount
                    account_invoice_data[key]['settled_amount'] += line_total_settled
                    
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
                        else:
                            # Add new invoice entry
                            account_period_invoices[key].append({
                                'invoice': invoice,
                                'settled_amount': line_total_settled,
                                'account_id': account_id,
                                'account_amount': account_amount
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
            historical_period_balance = opening_before['sales_amount'] - opening_before['settled_amount']
            
            historical_period = self.env['wilco.customer.invoice.summary'].create({
                'year': opening_before['year'],
                'month': opening_before['month'],
                'invoice_count': opening_before['invoice_count'],
                'sales_amount': opening_before['sales_amount'],  # Show actual sales
                'total_sales_amount': 0.0,  # For opening period, total_sales MUST be zero
                'settled_amount': opening_before['settled_amount'],
                'balance': opening_before['sales_amount'] - opening_before['settled_amount'],  # Update: Show sales - settled
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
                'balance': 0.0 - opening_during['settled_amount'],  # Update: For opening period, this would be 0 (sales) - settled
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
                        # For invoice breakdowns, balance is simply invoice amount - settled amount
                        # In this case, it's 0 (sales) - settled = -settled
                        breakdown_balance = 0.0 - inv_data['during_amount']
                        
                        self.env['wilco.customer.invoice.summary'].create({
                            'year': opening_during['year'],
                            'month': opening_during['month'],
                            'invoice_count': 0,
                            'sales_amount': 0.0,  # Don't count sales twice
                            'total_sales_amount': 0.0,
                            'settled_amount': inv_data['during_amount'],
                            'balance': breakdown_balance,  # For breakdowns: sales - settled
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
            if self.use_opening_period:
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
            
            # Update running totals for this sales account
            account_sales_totals[account_id] += current_sales
            
            # Calculate period balance: previous period balance + current sales - current settled
            new_period_balance = account_period_balances[account_id] + current_sales - current_settled
            
            # Create summary record
            period_summary = self.env['wilco.customer.invoice.summary'].create({
                'year': current_data['year'],
                'month': current_data['month'],
                'invoice_count': current_data['invoice_count'],
                'sales_amount': current_data['sales_amount'],
                'total_sales_amount': account_sales_totals[account_id],
                'settled_amount': current_data['settled_amount'],
                'balance': current_data['sales_amount'] - current_data['settled_amount'],  # Update: Show sales - settled for the period
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
            
            created_periods[(account_id, year, month, False)] = period_summary.id
            
            # Create invoice breakdowns if needed
            if self.show_invoice_breakdown and key in account_period_invoices:
                for inv_data in account_period_invoices[key]:
                    invoice = inv_data['invoice']
                    account_amount = inv_data['account_amount']
                    settled_amount = inv_data['settled_amount']
                    
                    # For invoice breakdowns, balance is account amount - settled amount
                    breakdown_balance = account_amount - settled_amount
                    
                    self.env['wilco.customer.invoice.summary'].create({
                        'year': year,
                        'month': month,
                        'invoice_count': 0,
                        'sales_amount': account_amount,  # Only the amount for this account
                        'total_sales_amount': 0.0,  # No total sales for individual invoices
                        'settled_amount': settled_amount,
                        'balance': breakdown_balance,  # For breakdowns: sales - settled
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