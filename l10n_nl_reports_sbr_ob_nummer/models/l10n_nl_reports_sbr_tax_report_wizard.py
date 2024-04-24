from odoo import models, _
from odoo.exceptions import RedirectWarning

class L10nNlTaxReportSBRWizard(models.TransientModel):
    _inherit = 'l10n_nl_reports_sbr.tax.report.wizard'

    def _check_values(self):
        super()._check_values()
        if not self.env.company.l10n_nl_reports_sbr_ob_nummer:
            raise RedirectWarning(
                _("The Omzetbelastingnummer is missing. Please set it up before trying to send or download the report."),
                self.env.ref('base.action_res_company_form').id,
                _("Company settings"),
            )

    def _get_sbr_identifier(self):
        # OVERRIDE
        return self.env.company.l10n_nl_reports_sbr_ob_nummer
