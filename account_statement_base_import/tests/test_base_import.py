# -*- coding: utf-8 -*-
#
#
# Authors: Laurent Mignon
# Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
# All Rights Reserved
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
import base64
import inspect
import os
from openerp.tests import common
from openerp import tools
from openerp.modules import get_module_resource


class TestCodaImport(common.TransactionCase):

    def setUp(self):
        super(TestCodaImport, self).setUp()
        self.company_a = self.browse_ref('base.main_company')
        tools.convert_file(self.cr, 'account',
                           get_module_resource('account', 'test',
                                               'account_minimal_test.xml'),
                           {}, 'init', False, 'test')
        self.account_move_obj = self.env["account.move"]
        self.account_move_line_obj = self.env["account.move.line"]
        self.account_id = self.ref("account.a_recv")
        self.journal = self.browse_ref("account.bank_journal")
        self.import_wizard_obj = self.env['credit.statement.import']
        self.partner = self.browse_ref("base.res_partner_12")
        self.journal.write({
            'used_for_import': True,
            "import_type": "generic_csvxls_so",
            'partner_id': self.partner.id,
            'commission_account_id': self.account_id,
            'receivable_account_id': self.account_id,
        })

    def _filename_to_abs_filename(self, file_name):
        dir_name = os.path.dirname(inspect.getfile(self.__class__))
        return os.path.join(dir_name, file_name)

    def _import_file(self, file_name):
        """ import a file using the wizard
        return the create account.bank.statement object
        """
        with open(file_name) as f:
            content = f.read()
            self.wizard = self.import_wizard_obj.create({
                "journal_id": self.journal.id,
                'input_statement': base64.b64encode(content),
                'file_name': os.path.basename(file_name),
            })
            res = self.wizard.import_statement()
            return self.account_move_obj.browse(res['res_id'])

    def test_simple_xls(self):
        """Test import from xls
        """
        file_name = self._filename_to_abs_filename(
            os.path.join("..", "data", "statement.xls"))
        move = self._import_file(file_name)
        self._validate_imported_move(move)

    def test_simple_csv(self):
        """Test import from csv
        """
        file_name = self._filename_to_abs_filename(
            os.path.join("..", "data", "statement.csv"))
        move = self._import_file(file_name)
        self._validate_imported_move(move)

    def _validate_imported_move(self, move):
        self.assertEqual("/", move.name)
        self.assertEqual(5, len(move.line_ids))
        move_line = move.line_ids[4]
        # common infos
        self.assertEqual(move_line.date_maturity, "2011-03-02")
        self.assertEqual(move_line.credit, 189.0)
        self.assertEqual(move_line.name, "label b")
