from odoo.tests import tagged
from odoo.tools import misc
from odoo.tools.misc import file_open

from freezegun import freeze_time

from .common import TestMxEdiCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestImportCFDIInvoice(TestMxEdiCommon):

    def _get_file_data_from_test_file(self, filename):
        file_path = f'{self.test_module}/tests/test_files/{filename}.xml'
        with file_open(file_path, 'rb') as file:
            cfdi_invoice = file.read()
        attachment = self.env['ir.attachment'].create({
            'mimetype': 'application/xml',
            'name': f'{filename}.xml',
            'raw': cfdi_invoice,
        })
        return attachment._unwrap_edi_attachments()[0]

    def test_import_invoice_tax_and_withholding(self):
        file_data = self._get_file_data_from_test_file('test_import_invoice_tax_withholding')
        invoice = self.env['account.move'].create({
            'journal_id': self.company_data['default_journal_purchase'].id,
        })
        self.env['account.move']._l10n_mx_edi_import_cfdi_invoice(invoice, file_data)

        wh_tax_4 = self.env['account.chart.template'].ref('tax1')
        tax_16 = self.env['account.chart.template'].ref('tax12')

        self.assertRecordValues(
            invoice.line_ids,
            [
                # pylint: disable=bad-whitespace
                {'balance':  147.00, 'account_type': 'expense'},
                {'balance': -164.64, 'account_type': 'liability_payable'},
                {'balance':   -5.88, 'account_type': 'liability_current', 'tax_line_id': wh_tax_4},
                {'balance':   23.52, 'account_type': 'asset_current',     'tax_line_id': tax_16},
            ],
        )

    @freeze_time('2017-01-01')
    def test_import_invoice_cfdi_unknown_partner(self):
        '''Test the import of invoices with unknown partners:
            * The partner should be created correctly
            * On the created move the "CFDI to Public" field (l10n_mx_edi_cfdi_to_public) should be set correctly.
        '''
        subtests = [
            {
                'xml_file': 'test_import_invoice_unknown_domestic_partner',
                'expected_invoice_vals': {
                    'l10n_mx_edi_cfdi_to_public': False,
                },
                'expected_partner_vals': {
                    'name': 'UNKNOWN PARTNER',
                    'vat': 'DEA040805DZ4',
                    'country_id': self.env.ref('base.mx').id,
                    'property_account_position_id': False,
                    'zip': '26670',
                },
            },
            {
                'xml_file': 'test_import_invoice_unknown_foreign_partner',
                'expected_invoice_vals': {
                    'l10n_mx_edi_cfdi_to_public': False,
                },
                'expected_partner_vals': {
                    'name': 'UNKNOWN FOREIGN PARTNER',
                    'vat': False,
                    'country_id': False,
                    'property_account_position_id': self.env['account.chart.template'].ref('account_fiscal_position_foreign').id,
                    'zip': False,
                },
            },
            {
                'xml_file': 'test_import_invoice_unknown_partner_to_public',
                'expected_invoice_vals': {
                    'l10n_mx_edi_cfdi_to_public': True,
                },
                'expected_partner_vals': {
                    'name': 'UNKNOWN PARTNER TO PUBLIC',
                    'vat': False,
                    'country_id': self.env.ref('base.mx').id,
                    'property_account_position_id': False,
                    'zip': False,
                },
            },
        ]
        for subtest in subtests:
            xml_file = subtest['xml_file']

            with self.subTest(msg=xml_file):
                preexisting_partners = self.env['res.partner'].sudo().search([])

                file_path = misc.file_path(f'{self.test_module}/tests/test_files/{xml_file}.xml')
                assert file_path
                with file_open(file_path, 'rb') as file:
                    content = file.read()

                invoice = self._upload_document_on_journal(
                    journal=self.company_data['default_journal_sale'],
                    content=content,
                    filename=f'{xml_file}.xml',
                )

                # Check that we actually created a new partner and did not use a preexisting partner
                self.assertFalse(invoice.partner_id in preexisting_partners)

                self.assertRecordValues(invoice, [subtest['expected_invoice_vals']])

                # field 'property_account_position_id' is company dependant
                partner = invoice.partner_id.with_company(company=invoice.company_id)
                self.assertRecordValues(partner, [subtest['expected_partner_vals']])

                # Check that exporting the invoice yields the same invoice.
                # (Even if we delete the original imported CFDI)
                invoice.l10n_mx_edi_document_ids.unlink()
                invoice.action_post()
                with self.with_mocked_pac_sign_success():
                    invoice._l10n_mx_edi_cfdi_invoice_try_send()
                self._assert_invoice_cfdi(invoice, xml_file)
