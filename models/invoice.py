from odoo import fields, models, api, _

class RequestInvoice(models.Model):
    _name = 'request.invoice'
    _inherit = ['mail.thread']
    _rec_name = 'customer'

    seq = fields.Char(required=True,copy=False,readonly=True,index=True,default=lambda self: _('New'),string='Invoice ID')
    customer = fields.Many2one('res.partner', string='Customer', required=True)
    invoiced_date = fields.Datetime(string='Invoiced Date')
    request_id = fields.Char(string = "Request ID")
    payment_reference = fields.Char(string = "Payment Reference", compute = "payment_ref")
    total = fields.Float(sting = "Total", compute = "compute_total")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed')], string="Status", default="draft")
    invoice_line = fields.One2many('request.invoice.line', 'invoice_rel', string='Invoice Line')

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('request.invoice')
        vals['seq'] = sequence or '/'
        return super(RequestInvoice, self).create(vals)

    def payment_ref(self):
        for rec in self:
            rec.payment_reference = rec.seq

    def compute_total(self):
        total_val = 0.0
        for rec in self:
            total_val = sum(clause_id.cost for clause_id in rec.invoice_line)
            rec.total = total_val

    def set_to_confirm(self):
        return self.write({'state': 'confirm'})

    def reset_to_draft(self):
        return self.write({'state': 'draft'})


class RequestInvoiceLine(models.Model):
    _name = 'request.invoice.line'

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
    lab_test = fields.Many2one('test.unit', string="Unit")
    cost = fields.Float(related = "lab_test.cost", string="Cost")
    invoice_rel = fields.Many2one('request.invoice', String = "Invoice Rel")



