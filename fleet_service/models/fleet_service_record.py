from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class FleetServiceRecord(models.Model):
    _name = 'fleet.service.record'
    _description = 'Fleet Service Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        (
            'fleet_service_record_name_vehicle_unique',
            'unique(name, vehicle_id)',
            'A service record with this reference already exists for this vehicle.',
        ),
    ]

    name = fields.Char(
        string='Service Reference',
        required=True,
        copy=False,
        default='New',
        readonly=True,
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehicle',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    technician_id = fields.Many2one(
        'res.users',
        string='Assigned Technician',
        tracking=True,
    )
    service_date = fields.Date(
        string='Service Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    service_type = fields.Selection(
        [
            ('oil_change', 'Oil Change'),
            ('tyre', 'Tyre'),
            ('brake', 'Brake'),
            ('engine', 'Engine'),
            ('general', 'General'),
        ],
        string='Service Type',
        tracking=True,
    )
    cost = fields.Float(
        string='Cost (INR)',
        default=0.0,
        digits=(10, 2),
        tracking=True,
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
    )
    notes = fields.Text(string='Internal Notes')
    tag_ids = fields.Many2many(
        'fleet.service.tag',
        'fleet_service_record_tag_rel',
        'service_record_id',
        'tag_id',
        string='Tags',
    )
    service_line_ids = fields.One2many(
        'fleet.service.line',
        'fleet_service_id',
        string='Service Lines',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Currency',
        readonly=True,
    )
    total_lines_cost = fields.Float(
        string='Total Lines Cost',
        compute='_compute_total_lines_cost',
        store=True,
    )
    is_expensive = fields.Boolean(
        string='Is Expensive',
        compute='_compute_is_expensive',
        store=True,
    )
    duration_days = fields.Integer(
        string='Duration (Days)',
        compute='_compute_duration_days',
        store=True,
    )
    vehicle_service_count = fields.Integer(
        string='Vehicle Service Count',
        compute='_compute_vehicle_service_count',
    )
    color = fields.Integer(
        string='Color',
        compute='_compute_color',
        store=True,
    )

    @api.depends('service_line_ids.quantity', 'service_line_ids.unit_price')
    def _compute_total_lines_cost(self):
        for record in self:
            record.total_lines_cost = sum(
                line.quantity * line.unit_price for line in record.service_line_ids
            )

    @api.depends('cost', 'total_lines_cost')
    def _compute_is_expensive(self):
        for record in self:
            record.is_expensive = record.cost > 10000 or record.total_lines_cost > 10000

    @api.depends('service_date')
    def _compute_duration_days(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.service_date and record.service_date <= today:
                record.duration_days = (today - record.service_date).days
            else:
                record.duration_days = 0

    @api.depends('vehicle_id')
    def _compute_vehicle_service_count(self):
        for record in self:
            if record.vehicle_id:
                record.vehicle_service_count = self.search_count([('vehicle_id', '=', record.vehicle_id.id)])
            else:
                record.vehicle_service_count = 0

    @api.depends('tag_ids', 'tag_ids.color')
    def _compute_color(self):
        for record in self:
            record.color = record.tag_ids[:1].color or 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('fleet.service.record') or 'New'
        return super().create(vals_list)

    def write(self, vals):
        protected_fields = {'cost', 'service_date'}
        if protected_fields.intersection(vals) and self.filtered(lambda rec: rec.state == 'done'):
            raise UserError(_('Completed service records cannot be modified.'))
        return super().write(vals)

    @api.constrains('cost', 'service_line_ids', 'service_line_ids.unit_price')
    def _check_non_negative_costs(self):
        for record in self:
            if record.cost < 0:
                raise ValidationError(_('Service cost cannot be negative.'))
            if any(line.unit_price < 0 for line in record.service_line_ids):
                raise ValidationError(_('Unit price cannot be negative.'))

    @api.onchange('service_type')
    def _onchange_service_type(self):
        defaults = {
            'oil_change': 500.0,
            'tyre': 1500.0,
            'brake': 2000.0,
            'engine': 8000.0,
        }
        if self.service_type in defaults:
            self.cost = defaults[self.service_type]
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _('Default cost applied. Please verify before saving.'),
                }
            }
        return {}

    def action_start(self):
        invalid_records = self.filtered(lambda rec: rec.state != 'draft')
        if invalid_records:
            raise ValidationError(_('Service can only be started from Draft state.'))
        self.write({'state': 'in_progress'})

    def action_done(self):
        invalid_records = self.filtered(lambda rec: rec.state != 'in_progress')
        if invalid_records:
            raise ValidationError(_('Service can only be marked Done from In Progress state.'))
        self.write({'state': 'done'})

    def action_cancel(self):
        invalid_records = self.filtered(lambda rec: rec.state not in ('draft', 'in_progress'))
        if invalid_records:
            raise ValidationError(_('Only Draft or In Progress services can be cancelled.'))
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        invalid_records = self.filtered(lambda rec: rec.state != 'cancelled')
        if invalid_records:
            raise ValidationError(_('Only Cancelled services can be reset to Draft.'))
        self.write({'state': 'draft'})

    def action_view_vehicle_services(self):
        self.ensure_one()
        return {
            'name': _('Vehicle Service Records'),
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.service.record',
            'view_mode': 'tree,kanban,form',
            'domain': [('vehicle_id', '=', self.vehicle_id.id)],
            'context': {'default_vehicle_id': self.vehicle_id.id},
        }
