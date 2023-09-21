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
from odoo.exceptions import UserError
from odoo import fields, models, api, _


class Appointment(models.Model):
    _name = 'lab.appointment'
    _inherit = ['mail.thread']
    _rec_name = 'name'
    _description = "Appointment"
    _order = 'appointment_date'

    user_id = fields.Many2one('res.users', 'Responsible', readonly=True)
    patient_id = fields.Many2one('lab.patient', string='Customer', required=True, select=True,
                                 help='Patient Name')
    name = fields.Char(string='Request ID', readonly=True, default=lambda self: _('New'))
    date = fields.Datetime(string='Requested Date', default=lambda s: fields.Datetime.now(),
                           help="This is the date in which customer request is noted")
    appointment_date = fields.Datetime(string='Request Date', default=lambda s: fields.Datetime.now(),
                                       help="This is the request date")
    physician_id = fields.Many2one('res.partner', string='Referred By', select=True)
    comment = fields.Text(string='Comments')
    appointment_lines = fields.One2many('lab.appointment.lines', 'test_line_appointment', string="Test Request")

    request_count = fields.Integer(compute="_compute_state", string='# of Requests', copy=False, default=0)
    inv_count = fields.Integer(compute="_compute_state", string='# of Invoices', copy=False, default=0)
    received_signature = fields.Binary(string = "Signature")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('request_lab', 'Lab Requested'),
        ('completed', 'Completed'),
        ('to_invoice', 'To Invoice'),
        ('invoiced', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft',
    )

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High')
    ], size=1)

    _defaults = {
        'priority': '0',
    }

    @api.model
    def create(self, vals):
        if vals:
            vals['name'] = self.env['ir.sequence'].next_by_code('lab.appointment') or _('New')
            result = super(Appointment, self).create(vals)
            return result

    def _compute_state(self):
        for obj in self:
            obj.request_count = self.env['lab.request'].search_count([('app_id', '=', obj.id)])
            obj.inv_count = self.env['account.move'].search_count([('lab_request', '=', obj.id)])

    def create_invoice(self):
        invoice_obj = self.env["account.move"]
        invoice_line_obj = self.env["account.move.line"]
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        # prd_account_id = journal.default_credit_account_id.id
        prd_account_id = journal.default_account_id.id
        for lab in self:
            lab.write({'state': 'to_invoice'})
            if lab.patient_id:
                curr_invoice = {
                    'partner_id': lab.patient_id.customer.id,
                    # 'account_id': lab.patient_id.patient.property_account_receivable_id.id,
                    'state': 'draft',
                    'move_type': 'out_invoice',
                    'invoice_date': str(datetime.datetime.now()),
                    'invoice_origin': "Lab Test# : " + lab.name,
                    # 'target': 'new',
                    'lab_request': lab.id,
                    'is_lab_invoice': True,
                }

                inv_ids = invoice_obj.create(curr_invoice)
                inv_id = inv_ids.id

                if inv_ids:
                    journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
                    prd_account_id = journal.default_account_id.id
                    list_value = []
                    if lab.appointment_lines:
                        for line in lab.appointment_lines:
                            unit_str = ""
                            for unit in line.tooth_unit:
                                unit_str += unit.name + ","

                            list_value.append((0,0, {
                                                    'lab_test': line.lab_test.id,
                                                    'tooth_unit': line.tooth_unit,
                                                    'discription': line.multi_ht + '/' + line.sep_con + '/' + unit_str + '/' + line.shade,
                                                    'name': line.multi_ht + '/' + line.sep_con + '/' + unit_str + '/' + line.shade,
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


                self.write({'state': 'invoiced'})
                view_id = self.env.ref('account.view_move_form').id
                return {
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Lab Invoices'),
                    'res_id': inv_id
                }

    def action_request(self):
        request_id = self.env['lab.request'].create({'lab_request_id': self.name,
                                                     'app_id': self.id,
                                                     'lab_requestor': self.patient_id.id,
                                                     'lab_requesting_date': self.appointment_date,
                                                            # 'test_request': line.lab_test.id,
                                                            # 'request_line': [(6, 0, [x.id for x in line])],
                
                                                    })
        request_list = []
        if self.appointment_lines:
            for line in self.appointment_lines:
                # data = self.env['lab.test'].search([('lab_test', '=', line.lab_test.lab_test)])
                request_list.append((0, 0, {
                                            'multi_ht': line.multi_ht,
                                            'sep_con': line.sep_con,
                                            'shade': line.shade,
                                            'tooth_unit': line.tooth_unit,
                                            'lab_test': line.lab_test.id,
                                            'cost': line.cost
                                            }))
            request_id.write({'request_line': request_list})
            self.state = 'request_lab'
        else:
            raise UserError(_('Please Select Lab Test.'))

        inv_id = request_id.id 
        form_view_ref = self.env.ref('medical_lab_management.view_lab_reques_form', False)
        tree_view_ref = self.env.ref('medical_lab_management.view_lab_request_tree', False)

        return {
            'domain': "[('id', '=', " + str(inv_id) + ")]",
            'name': 'Lab Request',
            'view_mode': 'form',
            'res_model': 'lab.request',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
        }

    def confirm_appointment(self):

        message_body = "Dear " + self.patient_id.customer.name + "," + "<br>Your Appointment Has been Confirmed " \
                                             + "<br>Appointment ID : " + self.name + "<br>Date : " + str(self.appointment_date) + \
                       '<br><br>Thank you'

        template_obj = self.env['mail.mail']
        template_data = {
            'subject': 'Appointment Confirmation',
            'body_html': message_body,
            'email_from': self.env.user.company_id.email,
            'email_to': self.patient_id.email
        }
        template_id = template_obj.create(template_data)
        template_obj.send(template_id)
        self.write({'state': 'confirm'})

    def cancel_appointment(self):
        return self.write({'state': 'cancel'})


class LabAppointmentLines(models.Model):
    _name = 'lab.appointment.lines'
    shade = fields.Selection([
        ('a1', 'A1'),
        ('a2', 'A2'),
        ('a3', 'A3'),
        ('a3.5', 'A3.5'),
        ('a4', 'A4'),
        ('b1', 'B1'),
        ('b2', 'B2'),
        ('b3', 'B3'),
        ('b4', 'B4'),
        ('c1', 'C1'),
        ('c2', 'C2'),
        ('c3', 'C3'),
        ('c4', 'C4'),
        ('d2', 'D2'),
        ('d3', 'D3'),
        ('d4', 'D4'),
        ('om1', 'OM1'),
        ('om2', 'OM2'),
        ('om3', 'OM3')], string = "Shade")
    multi_ht = fields.Selection([
        ('multi', 'Multi-Layer'),
        ('ht', 'HT')], string = "Multi-Layer/HT")
    sep_con = fields.Selection([
        ('connected', 'Connected'),
        ('separate', 'Separate')], string = "Connected/Separate")
    tooth_unit = fields.Many2many('unit', string = "Unit")
    lab_test = fields.Many2one('test.unit', string="Type")
    cost = fields.Float(related = "lab_test.cost", string="Cost")
    requesting_date = fields.Date(string="Date")
    test_line_appointment = fields.Many2one('lab.appointment', string="Appointment")

    # @api.onchange('lab_test')
    # def cost_update(self):
    #     if self.lab_test:
    #         self.cost = self.lab_test.test_cost


class LabPatientInherit(models.Model):
    _inherit = 'lab.patient'

    app_count = fields.Integer(compute="_compute_state", string='# of Appointments', copy=False, default=0)

    def _compute_state(self):
        for obj in self:
            obj.app_count = self.env['lab.appointment'].search_count([('patient_id', '=', obj.id)])

