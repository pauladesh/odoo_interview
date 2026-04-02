from odoo import _, fields, models


class FleetRescheduleWizard(models.TransientModel):
    _name = 'fleet.reschedule.wizard'
    _description = 'Fleet Reschedule Wizard'

    service_ids = fields.Many2many(
        'fleet.service.record',
        'fleet_reschedule_wizard_service_rel',
        'wizard_id',
        'service_id',
        string='Records to Reschedule',
        required=True,
    )
    new_date = fields.Date(string='New Service Date', required=True)
    new_cost = fields.Float(string='Updated Cost (leave 0 to keep existing cost)')
    reason = fields.Text(string='Reason for Rescheduling', required=True)

    def confirm(self):
        self.ensure_one()
        for service in self.service_ids:
            old_service_date = service.service_date
            vals = {'service_date': self.new_date}
            if self.new_cost > 0:
                vals['cost'] = self.new_cost

            service.with_context(allow_completed_service_edit=True).write(vals)

            old_date_str = fields.Date.to_string(old_service_date) if old_service_date else '-'
            message = _(
                'Service rescheduled.\nOld Service Date: %(old_date)s\nReason: %(reason)s',
                old_date=old_date_str,
                reason=self.reason,
            )
            service.message_post(body=message)

        return self.env.ref('fleet_service.action_fleet_service_record').read()[0]
