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

import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LabRequest(models.Model):
    _name = 'lab.request'
    _inherit = ['mail.thread']
    _rec_name = 'lab_request_id'
    _description = 'Lab Request'

    name = fields.Char(string='Lab Test', size=16, readonly=True, required=True, help="Lab result ID", default=lambda *a: '#')
    lab_request_id = fields.Char(string='Request ID', help="Lab appointment ID")
    app_id = fields.Many2one('lab.appointment', string='Requests')
    lab_requestor = fields.Many2one('lab.patient', string='Customer', required=True, select=True,
                                    help='Patient Name')
    test_request = fields.Many2one('lab.test', string='Test')
    lab_requesting_date = fields.Datetime(string='Requested Date')
    comment = fields.Text('Comment')
    request_line = fields.One2many('lab.test.attribute', 'test_request_reverse', string="Test Lines")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scanner', 'Scanner'),
        ('design', 'Design'),
        ('milling', 'Milling'),
        ('finishing', 'Finishing'),
        ('packing', 'Packing'),
        ('delivery', 'Delivery'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),

    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    # account_analytic_id = fields.Many2one('account.analytic.account', store=True, string='Analytic Account', compute='_compute_analytic_id_and_tag_ids', readonly=False)

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('lab.request')
        vals['name'] = sequence or '/'
        return super(LabRequest, self).create(vals)

    def set_to_scanner(self):
        return self.write({'state': 'scanner'})

    def set_to_design(self):
        return self.write({'state': 'design'})

    def set_to_milling(self):
        return self.write({'state': 'milling'})

    def set_to_finishing(self):
        return self.write({'state': 'finishing'})

    def set_to_packing(self):
        return self.write({'state': 'packing'})

    def set_to_delivery(self):
        return self.write({'state': 'delivery'})

    def cancel_lab_test(self):
        return self.write({'state': 'cancel'})

    def set_to_test_completed(self):
        if not self.request_line:
            raise ValidationError(_("No Result Lines Entered !"))
        req_obj = self.env['lab.request'].search_count([('app_id', '=', self.app_id.id),
                                                        ('id', '!=', self.id)])
        req_obj_count = self.env['lab.request'].search_count([('app_id', '=', self.app_id.id),
                                                              ('id', '!=', self.id),
                                                              ('state', '=', 'completed')])
        if req_obj == req_obj_count:
            app_obj = self.env['lab.appointment'].search([('id', '=', self.app_id.id)])
            app_obj.write({'state': 'completed'})
        return self.write({'state': 'completed'})

    def print_lab_test(self):
        return self.env.ref('medical_lab_management.print_lab_test').report_action(self)

    def lab_invoice_create(self):
        invoice_obj = self.env["account.move"]
        invoice_line_obj = self.env["account.move.line"]
        for lab in self:
            if lab.lab_requestor:
                curr_invoice = {
                    'partner_id': lab.lab_requestor.customer.id,
                    'account_id': lab.lab_requestor.customer.property_account_receivable_id.id,
                    'state': 'draft',
                    'type': 'out_invoice',
                    'date_invoice': datetime.datetime.now(),
                    'origin': "Lab Test# : " + lab.name,
                    'target': 'new',
                    'lab_request': lab.id,
                    'is_lab_invoice': True
                }

                inv_ids = invoice_obj.create(curr_invoice)
                inv_id = inv_ids.id

                if inv_ids:
                    journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
                    prd_account_id = journal.default_credit_account_id.id
                    if lab.test_request:
                        curr_invoice_line = {
                            'name': "Charge for lab test",
                            'price_unit': lab.test_request.test_cost or 0,
                            'quantity': 1.0,
                            'account_id': prd_account_id,
                            'invoice_id': inv_id,
                        }

                        invoice_line_obj.create(curr_invoice_line)

                self.write({'state': 'completed'})
                form_view_ref = self.env.ref('account.view_move_form', False)
                tree_view_ref = self.env.ref('account.view_move_tree', False)

                return {
                    'domain': "[('id', '=', " + str(inv_id) + ")]",
                    'name': 'Lab Invoices',
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'type': 'ir.actions.act_window',
                    'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
                }

    # def create_invoice(self):
    #     invoice_id = self.env['request.invoice'].create({
    #                                             'customer': self.lab_requestor.customer.id,
    #                                             'request_id': self.name,
    #                                             'invoiced_date': datetime.datetime.now()
    #                                         })
    #     invoice_list = []
    #     if self.request_line:
    #         for line in self.request_line:
    #             # data = self.env['lab.test'].search([('lab_test', '=', line.lab_test.lab_test)])
    #             invoice_list.append((0, 0, {
    #                                         'multi_ht': line.multi_ht,
    #                                         'sep_con': line.sep_con,
    #                                         'shade': line.shade,
    #                                         'lab_test': line.lab_test.id,
    #                                         'cost': line.cost
    #                                         }))
    #         invoice_id.write({'invoice_line': invoice_list})

    #         self.write({'state': 'payment'})
    #         inv_id = invoice_id.id 
    #         view_id = self.env.ref('medical_lab_management.view_invoice_form').id
    #         return {
    #             'view_mode': 'form',
    #             'res_model': 'request.invoice',
    #             'view_id': view_id,
    #             'type': 'ir.actions.act_window',
    #             'name': _('Lab Invoices'),
    #             'res_id': inv_id
    #         }
    def create_invoice(self):
        invoice_obj = self.env["account.move"]
        invoice_line_obj = self.env["account.move.line"]
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        # prd_account_id = journal.default_credit_account_id.id
        prd_account_id = journal.default_account_id.id
        for lab in self:
            # lab.write({'state': 'to_invoice'})
            if lab.lab_requestor:
                curr_invoice = {
                    'partner_id': lab.lab_requestor.customer.id,
                    # 'account_id': lab.patient_id.patient.property_account_receivable_id.id,
                    'state': 'draft',
                    'move_type': 'out_invoice',
                    'invoice_date': str(datetime.datetime.now()),
                    # 'invoice_origin': "Lab Test# : " + lab.name,
                    # 'target': 'new',
                    # 'lab_request': lab.id,
                    'is_lab_invoice': True,
                }

                inv_ids = invoice_obj.create(curr_invoice)
                inv_id = inv_ids.id

                if inv_ids:
                    journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
                    prd_account_id = journal.default_account_id.id
                    list_value = []
                    if lab.request_line:
                        for line in lab.request_line:
                            list_value.append((0,0, {
                                                    'tooth_unit': line.tooth_unit,
                                                    'lab_test': line.lab_test.id,
                                                    'discription': line.multi_ht + '/' + line.sep_con + '/' + line.shade,
                                                    'price_unit': line.cost,
                                                    'quantity': 1.0,
                                                    'account_id': prd_account_id,
                                                    'move_id': inv_id,
                                    }))
                        print(list_value)
                        inv_ids.write({'invoice_line_ids': list_value})
                            # invoice_line_obj.update({
                            #     'name': line.lab_test.lab_test,
                            #     'price_unit': line.cost,
                            #     'quantity': 1.0,
                            #     'account_id': prd_account_id,
                            #     'move_id': inv_id,
                            # })


                self.write({'state': 'completed'})
                view_id = self.env.ref('account.view_move_form').id
                return {
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Lab Invoices'),
                    'res_id': inv_id
                }
       
