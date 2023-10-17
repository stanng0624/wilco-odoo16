from odoo import api, fields, models, _


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    wilco_sale_order_count = fields.Integer("Sales Order Count", compute='_wilco_compute_sale_order_count')

    @api.depends('line_ids')
    def _wilco_compute_sale_order_count(self):
        for account in self:
            account.wilco_sale_order_count = self.env['sale.order'].search_count([
                ('order_line.invoice_lines.analytic_line_ids.account_id', '=', account.id)
            ])

    def wilco_action_view_sale_orders(self):
        self.ensure_one()
        sale_orders = self.env['sale.order'].search([
            ('order_line.invoice_lines.analytic_line_ids.account_id', '=', self.id)
        ])
        result = {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "domain": [['id', 'in', sale_orders.ids]],
            "name": _("Sale Orders"),
            'view_mode': 'tree,form',
        }
        if len(sale_orders) == 1:
            result['view_mode'] = 'form'
            result['res_id'] = sale_orders.id
        return result
