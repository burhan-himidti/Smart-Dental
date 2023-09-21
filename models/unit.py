from odoo import models, fields


class Unit(models.Model):
    _name = 'unit'
    _rec_name = 'name'
    _description = "Unit"

    name = fields.Char(string="Unit", required=True)