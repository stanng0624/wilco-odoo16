from odoo import models, fields, api
from datetime import date
import logging


class WilcoVendorBillSummaryWizard(models.TransientModel):
    _name = 'wilco.vendor.bill.summary.wizard'
    _description = 'Vendor Bill Summary Wizard'

    as_of_date = fields.Date(string='As Of Date', required=True, default=fields.Date.today)
    partner_id = fields.Many2one('res.partner', string='Vendor', domain=[('supplier_rank', '>', 0)])
    wilco_project_id = fields.Many2one('project.project', string='Project')
    
    # Opening period fields
    use_opening_period = fields.Boolean(string='Use Opening Period', default=True,
                                        help="Define an opening period to consolidate all previous activity")
    opening_year = fields.Integer(string='Opening Year', default=lambda self: fields.Date.today().year)
    opening_month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Opening Month', default='1')
    
    # Balance grouping option
    show_balance_by = fields.Selection([
        ('period', 'Period'),
        ('vendor', 'Vendor'),
        ('account', 'Expense Account'),
        ('project', 'Project')
    ], string='Show Balance By', default='period',
       help="Determines how to group the bill data in the report")
    
    # Bill breakdown option
    show_bill_breakdown = fields.Boolean(string='Show Bill Breakdown', default=False,
                                        help="Show individual bill details within each period")
    
    @api.onchange('as_of_date')
    def _onchange_as_of_date(self):
        """Update opening year and month when as_of_date changes."""
        if self.as_of_date and self.use_opening_period:
            self.opening_year = self.as_of_date.year
            self.opening_month = '1'
    
    @api.onchange('use_opening_period')
    def _onchange_use_opening_period(self):
        """Update opening year and month when toggling the use_opening_period field"""
        if self.use_opening_period and self.as_of_date:
            self.opening_year = self.as_of_date.year
            self.opening_month = '1'
    
    def wilco_action_generate_report(self):
        """Generate the vendor bill summary report."""
        self.ensure_one()
        
        # Clear existing temporary records
        self.env['wilco.vendor.bill.summary'].sudo().search([]).unlink()
        
        # Generate data
        self._wilco_generate_bill_summary_data()
        
        # Return action to open the list view
        action = {
            'name': 'Vendor Bill Summary',
            'type': 'ir.actions.act_window',
            'res_model': 'wilco.vendor.bill.summary',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': {},
        }
        
        # Set default filters based on options
        context = {}
        
        if not self.show_bill_breakdown:
            context['search_default_not_breakdown'] = 1
        
        if self.show_balance_by == 'account':
            context['search_default_group_by_expense_account'] = 1
        elif self.show_balance_by == 'vendor':
            context['search_default_group_by_partner'] = 1
        elif self.show_balance_by == 'project':
            context['search_default_group_by_project'] = 1
        
        action['context'] = context
        return action
    
    def _wilco_generate_bill_summary_data(self):
        """Main method to generate vendor bill summary data."""
        self.ensure_one()
        
        # Get all posted vendor bills up to the as_of_date
        bill_domain = [
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '<=', self.as_of_date)
        ]
        
        if self.partner_id:
            bill_domain.append(('partner_id', '=', self.partner_id.id))
        
        if self.wilco_project_id:
            bill_domain.append(('line_ids.analytic_distribution', 'ilike', str(self.wilco_project_id.id)))
        
        bills = self.env['account.move'].search(bill_domain)
        opening_month_int = int(self.opening_month) if self.opening_month else 0
        
        # Generate data based on grouping option
        self._generate_generic_report_data(bills, opening_month_int, self.show_balance_by)
    
    def _generate_generic_report_data(self, bills, opening_month_int, group_by='period'):
        """Generic method to generate bill summary data."""
        # Dictionary to store data
        bill_data = {}
        opening_data = {}
        
        # Calculate opening period start date
        opening_start_date = None
        if self.use_opening_period and opening_month_int > 0:
            opening_start_date = date(self.opening_year, opening_month_int, 1)
        
        # Process bills
        for bill in bills:
            if not bill.invoice_date:
                continue
                
            year, month = bill.invoice_date.year, bill.invoice_date.month
            
            # Check if opening period
            is_opening_period = False
            if self.use_opening_period and opening_start_date:
                if year < self.opening_year or (year == self.opening_year and month < opening_month_int):
                    is_opening_period = True
            
            # Create grouping key
            project_id = False
            if group_by == 'vendor':
                key_base = bill.partner_id.id if bill.partner_id else 0
            elif group_by == 'project':
                for line in bill.invoice_line_ids.filtered(lambda l: l.analytic_distribution):
                    if line.analytic_distribution:
                        project_id = int(list(line.analytic_distribution.keys())[0])
                        break
                key_base = project_id
            elif group_by == 'account':
                # For account grouping, we need to process at line level
                self._process_account_grouping(bill, is_opening_period, year, month)
                continue
            else:  # period
                key_base = 'period'
            
            # Create final key
            if is_opening_period:
                key = f"opening_{key_base}" if key_base != 'period' else 'opening'
            else:
                key = (key_base, year, month)
            
            # Calculate amounts
            bill_amount = abs(bill.amount_total)
            settled_amount = self._compute_settled_amount(bill)
            
            # Store in appropriate dict
            target_data = opening_data if is_opening_period else bill_data
            
            if key not in target_data:
                target_data[key] = {
                    'expense_amount': 0.0,
                    'settled_amount': 0.0,
                    'bill_count': 0,
                    'partner_id': bill.partner_id.id if bill.partner_id else False,
                    'project_id': project_id,
                    'year': year if not is_opening_period else self.opening_year,
                    'month': month if not is_opening_period else int(self.opening_month),
                }
            
            target_data[key]['expense_amount'] += bill_amount
            target_data[key]['settled_amount'] += settled_amount
            target_data[key]['bill_count'] += 1
        
        # Create records
        self._create_summary_records(opening_data, bill_data, group_by)
    
    def _process_account_grouping(self, bill, is_opening_period, year, month):
        """Process bill for account-level grouping."""
        # This would be implemented similar to the customer invoice summary
        # but focusing on expense accounts instead of sales accounts
        pass
    
    def _compute_settled_amount(self, bill):
        """Calculate settled amount for a vendor bill."""
        if bill.move_type not in ['in_invoice', 'in_refund']:
            return 0.0
        
        # Find the payable line for this vendor bill
        payable_lines = bill.line_ids.filtered(lambda l: l.account_id.account_type == 'liability_payable')
        
        if not payable_lines:
            return 0.0
        
        settled_amount = 0.0
        
        for line in payable_lines:
            # If there's no partial reconciliation, continue to next line
            if not line.matched_credit_ids and not line.matched_debit_ids:
                continue
                
            # Check partial payments (matched credits - payments made to vendor)
            for partial in line.matched_credit_ids:
                if partial.max_date <= self.as_of_date:
                    settled_amount += abs(partial.amount)
                    
            # Check partial payments (matched debits - refunds or adjustments)
            for partial in line.matched_debit_ids:
                if partial.max_date <= self.as_of_date:
                    settled_amount += abs(partial.amount)
        
        # Convert to bill currency if needed
        if bill.currency_id != bill.company_id.currency_id:
            settled_amount = bill.company_id.currency_id._convert(
                settled_amount,
                bill.currency_id,
                bill.company_id,
                self.as_of_date or fields.Date.today()
            )
                
        return settled_amount
    
    def _create_summary_records(self, opening_data, bill_data, group_by):
        """Create summary records from processed data."""
        # Create opening period records
        if self.use_opening_period and opening_data:
            for key, data in opening_data.items():
                record_vals = {
                    'year': self.opening_year,
                    'month': int(self.opening_month),
                    'is_opening': True,
                    'description': 'Opening Period',
                    'bill_count': data['bill_count'],
                    'expense_amount': data['expense_amount'],
                    'settled_amount': data['settled_amount'],
                    'balance': 0.0,
                    'period_balance': data['expense_amount'] - data['settled_amount'],
                    'total_expense_amount': data['expense_amount'],
                    'as_of_date': self.as_of_date,
                    'partner_id': data.get('partner_id', False),
                    'project_id': data.get('project_id', False),
                }
                self.env['wilco.vendor.bill.summary'].create(record_vals)
        
        # Create regular period records
        if bill_data:
            # Sort by year and month
            sorted_keys = sorted([k for k in bill_data.keys() if isinstance(k, tuple)], 
                               key=lambda x: (x[1], x[2]))  # year, month
            
            running_balance = 0.0
            total_expenses = 0.0
            
            for key in sorted_keys:
                data = bill_data[key]
                period_expense = data['expense_amount']
                period_settled = data['settled_amount']
                
                running_balance += period_expense - period_settled
                total_expenses += period_expense
                
                record_vals = {
                    'year': data['year'],
                    'month': data['month'],
                    'is_opening': False,
                    'bill_count': data['bill_count'],
                    'expense_amount': period_expense,
                    'settled_amount': period_settled,
                    'balance': 0.0,
                    'period_balance': running_balance,
                    'total_expense_amount': total_expenses,
                    'as_of_date': self.as_of_date,
                    'partner_id': data.get('partner_id', False),
                    'project_id': data.get('project_id', False),
                }
                self.env['wilco.vendor.bill.summary'].create(record_vals) 