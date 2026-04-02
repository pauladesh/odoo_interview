from odoo import fields, models


class FleetServiceTag(models.Model):
    _name = 'fleet.service.tag'
    _description = 'Fleet Service Tag'

    name = fields.Char(required=True)
    color = fields.Integer(string='Color')
