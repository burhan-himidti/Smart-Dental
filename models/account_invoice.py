# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anusha P P @ cybrosys and Niyas Raphy @ cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields, api


class LabRequestInvoices(models.Model):
    _inherit = 'account.move'

    is_lab_invoice = fields.Boolean(string="Is Lab Invoice")
    lab_request = fields.Many2one('lab.appointment', string="Request ID", help="Source Document")
    phone = fields.Char(related="partner_id.phone", string="Phone")

    def action_invoice_paid(self):
        res = super(LabRequestInvoices, self).action_invoice_paid()
        lab_app_obj = self.env['lab.appointment'].search([('id', '=', self.lab_request.id)])
        for obj in lab_app_obj:
            obj.write({'state': 'invoiced'})
        return res

class LabRequestInvoicesLine(models.Model):
    _inherit = 'account.move.line'

    # tooth_unit = fields.Selection([
    #     ('11', 'Anatomic-Crown-11'),
    #     ('21', 'Anatomic-Crown-21'),
    #     ('22', 'Anatomic-Crown-22'),
    #     ('12', 'Adjacent-Tooth-12'),
    #     ('23', 'Adjacent-Tooth-23'),
    #     ('41', 'Antagonist-41'),
    #     ('31', 'Antagonist-31'),
    #     ('32', 'Antagonist-32'),
    #     ('13', '13'),
    #     ('14', '14'),
    #     ('15', '15'),
    #     ('16', '16'),
    #     ('17', '17'),
    #     ('18', '18'),
    #     ('42', '42'),
    #     ('43', '43'),
    #     ('44', '44'),
    #     ('45', '45'),
    #     ('46', '46'),
    #     ('47', '47'),
    #     ('48', '48'),
    #     ('24', '24'),
    #     ('25', '25'),
    #     ('26', '26'),
    #     ('27', '27'),
    #     ('28', '28'),
    #     ('33', '33'),
    #     ('34', '34'),
    #     ('35', '35'),
    #     ('36', '36'),
    #     ('37', '37'),
    #     ('38', '38')], string = "Units")
    tooth_unit = fields.Many2many('unit', string= "Unit")
    lab_test = fields.Many2one('test.unit', string="Type")
    discription = fields.Char(String = "Discription")
