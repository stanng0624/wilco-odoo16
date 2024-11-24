class ExternalIdentifierUtil:
    @staticmethod
    def exist_external_identifier(env, model_name, record_id, module='__import__'):
        return bool(env['ir.model.data'].sudo().search([
            ('module', '=', module),
            ('model', '=', model_name),
            ('res_id', '=', record_id),
        ], limit=1))

    @staticmethod
    def create_external_identifier(env, model_name, record_id, external_identifier_name, module='__import__'):
        external_identifier_name = external_identifier_name.replace(" ", "")
        env['ir.model.data'].sudo().create({
            'name': external_identifier_name,
            'module': module,
            'model': model_name,
            'res_id': record_id,
            'noupdate': False
        })

    @staticmethod
    def update_external_identifier(env, model_name, record_id, external_identifier_name, module='__import__'):
        external_identifier_name = external_identifier_name.replace(" ", "")
        external_identifier = env['ir.model.data'].sudo().search([
            ('module', '=', module),
            ('model', '=', model_name),
            ('res_id', '=', record_id),
        ], limit=1)

        if external_identifier and external_identifier.name != external_identifier_name:
            external_identifier.sudo().write({'name': external_identifier_name})

    @staticmethod
    def write_external_identifier(env, model_name, record_id, external_identifier_name, 
                                module='__import__', override_existing=True):
        if override_existing and ExternalIdentifierUtil.exist_external_identifier(env, model_name, record_id, module):
            ExternalIdentifierUtil.update_external_identifier(env, model_name, record_id, external_identifier_name, module)
        else:
            ExternalIdentifierUtil.create_external_identifier(env, model_name, record_id, external_identifier_name, module) 