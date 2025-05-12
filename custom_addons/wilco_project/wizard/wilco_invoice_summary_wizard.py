from odoo import models, fields, api
from datetime import date


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
        Following naming conventions from PLANNING.md.
        """
        self.ensure_one()
        
        # Clear existing temporary records
        self.env['wilco.customer.invoice.summary'].sudo().search([]).unlink()
        
        # Generate data
        self._wilco_generate_invoice_summary_data()
        
        # Return action to open the list view with proper grouping
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
        
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        
        invoices = self.env['account.move'].search(domain)
        
        # Convert opening_month to integer for comparisons
        opening_month_int = int(self.opening_month) if self.use_opening_period and self.opening_month else 0
        
        # Group invoices by year and month
        invoice_data = {}
        opening_data = {
            'year': self.opening_year if self.use_opening_period else 0,
            'month': opening_month_int,  # Store as integer for the model
            'invoice_count': 0,
            'sales_amount': 0.0,  # Will accumulate total sales for periods before opening (for internal calculation only)
            'settled_amount': 0.0,
            'is_opening': True
        }
        
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
                # Add to opening data
                opening_data['invoice_count'] += 1
                # Accumulate sales amount for opening period (for internal balance calculation only)
                opening_data['sales_amount'] += invoice.amount_total
                
                # Calculate settled amount based on as_of_date using proper reconciliation data
                settled_amount = self._wilco_compute_settled_amount_as_of_date(invoice, self.as_of_date)
                opening_data['settled_amount'] += settled_amount
            else:
                # Add to regular periods
                if key not in invoice_data:
                    invoice_data[key] = {
                        'year': key[0],
                        'month': key[1],
                        'invoice_count': 0,
                        'sales_amount': 0.0,
                        'settled_amount': 0.0,
                        'is_opening': False
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
        
        # First create opening record if needed
        if self.use_opening_period and (opening_data['invoice_count'] > 0 or opening_data['settled_amount'] != 0):
            # Calculate opening balance (sales minus settled)
            # For internal calculation we use sales_amount to get the correct balance
            balance = opening_data['sales_amount'] - opening_data['settled_amount']
            
            # Create the opening record with sales_amount as 0 for display purposes
            summary = self.env['wilco.customer.invoice.summary'].create({
                'year': opening_data['year'],
                'month': opening_data['month'],
                'invoice_count': opening_data['invoice_count'],
                'sales_amount': 0.0,  # Display as 0 per requirement
                'total_sales_amount': 0.0,  # No total sales for opening
                'settled_amount': opening_data['settled_amount'],
                'balance': balance,
                'as_of_date': self.as_of_date,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'is_opening': True
            })
        
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
                'partner_id': self.partner_id.id if self.partner_id else False,
                'is_opening': False
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