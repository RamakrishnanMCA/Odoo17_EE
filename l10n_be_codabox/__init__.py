from . import models

from odoo.tools.translate import _lt
from odoo.exceptions import UserError


def _l10n_be_codabox_pre_init_hook(env):
    domain = [
        ('partner_id.country_id.code', '=', 'BE'),
        ('vat', '!=', False),
    ]
    # The field is defined in account_reports module which this module does not depend on in 17.0
    if "account_representative_id" in env['res.company']._fields:
        # If we are in a demo db, create a demo accounting firm.
        if bool(env['ir.module.module'].search_count([('demo', '=', True)])):
            accounting_firm = env['res.partner'].create({
                'name': 'Demo Accounting Firm',
                'vat': 'BE0428759497',
                'country_id': env.ref('base.be').id,
            })
            env['res.company'].search(domain).write({
                'account_representative_id': accounting_firm.id,
            })
        domain.append(('account_representative_id.vat', '!=', False))
    companies = env['res.company'].search(domain)
    if not companies:
        raise UserError(_lt("The CodaBox module must be installed and configured by an Accounting Firm."))
