from odoo import fields, models


class FleetServiceLine(models.Model):
    _name = 'fleet.service.line'
    _description = 'Fleet Service Line'

    fleet_service_id = fields.Many2one(
        'fleet.service.record',
        string='Service Record',
        required=True,
        ondelete='cascade',
    )
    description = fields.Char(string='Part / Labour Description', required=True)
    quantity = fields.Integer(default=1)
    unit_price = fields.Float(string='Unit Price (INR)', default=0.0)
