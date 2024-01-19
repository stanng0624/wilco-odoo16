from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    wilco_line_ref = fields.Char(string='Line reference')

    @api.ondelete(at_uninstall=False)
    def _unlink_except_linked_order_line(self):
        # Allow delete when it is delete from header, dynamic_unlink will be True if delete from header
        dynamic_unlink = self._context.get('dynamic_unlink')
        if not dynamic_unlink and self.sale_line_ids and self.move_id.sale_order_count == 1:
            sale_order = self.sale_line_ids.order_id
            if sale_order.id and sale_order.wilco_invoice_method == 'invoice_by_order':
                raise UserError(_("You can not remove the first order line since it will affect the sales order linkage with invoice"))

    @api.onchange('product_id')
    def _wilco_onchange_product_id(self):
        if not self.product_id:
            return

        self._wilco_set_name_from_source_order()

        self._wilco_set_analytic_distribution_from_project()

    def _wilco_set_name_from_source_order(self):
        self.ensure_one()

        order_name = ''

        account_move = self.move_id
        if account_move.is_sale_document() and account_move.sale_order_count == 1:
            sale_order = account_move.line_ids.sale_line_ids.order_id
            if sale_order.id and sale_order.name and sale_order.wilco_invoice_method == 'invoice_by_order':
                order_name = sale_order.name

        if order_name != '':
            self.name = _("Bill To Order: {}").format(order_name)

    def _wilco_set_analytic_distribution_from_project(self):
        self.ensure_one()

        account_move = self.move_id
        if account_move.wilco_project_id:
            analytic_account_id = account_move.wilco_project_id.analytic_account_id.id
            if analytic_account_id and self.display_type == 'product':
                analytic_account_id_str = str(analytic_account_id)
                self.analytic_distribution = {analytic_account_id_str: 100}


    # @api.model_create_multi
    # def create(self, vals_list):
    #     lines = super().create(vals_list)
    #
    #     for line in lines:
    #         if line.move_id:
    #             account_move = line.move_id
    #             if account_move.wilco_project_id and not line.analytic_distribution:
    #                 analytic_account_id = account_move.wilco_project_id.analytic_account_id.id
    #                 if analytic_account_id and line.display_type == 'product':
    #                     analytic_account_id_str = str(analytic_account_id)
    #                     line.write({'analytic_distribution': {analytic_account_id_str: 100}})
    #
    #     return lines