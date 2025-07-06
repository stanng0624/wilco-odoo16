-- COMPREHENSIVE ORPHANED RELATION CLEANUP
-- Run this to fix ALL foreign key violations at once

-- 1. Account payment register relations
DELETE FROM account_payment_register_move_line_rel 
WHERE wizard_id NOT IN (SELECT id FROM account_payment_register);

-- 2. Sale advance payment invoice relations  
DELETE FROM sale_advance_payment_inv_sale_order_rel 
WHERE sale_advance_payment_inv_id NOT IN (SELECT id FROM sale_advance_payment_inv);

-- 3. Account invoice send relations
DELETE FROM account_move_account_invoice_send_rel 
WHERE account_invoice_send_id NOT IN (SELECT id FROM account_invoice_send);

-- 4. Accounting report relations (current issue)
DELETE FROM account_journal_accounting_report_rel 
WHERE accounting_report_id NOT IN (SELECT id FROM accounting_report);


DELETE FROM mail_compose_message_ir_attachments_rel 
WHERE wizard_id NOT IN (SELECT id FROM mail_compose_message);

DELETE FROM mail_compose_message_res_partner_rel 
WHERE wizard_id NOT IN (SELECT id FROM mail_compose_message);