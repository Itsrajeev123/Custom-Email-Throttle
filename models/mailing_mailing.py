from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class MailingMailing(models.Model):
    _inherit = 'mailing.mailing'

    use_throttle = fields.Boolean(
        string='Enable Throttle Sending',
        default=False,
    )

    throttle_batch_size = fields.Integer(
        string='Batch Size',
        default=10,
    )

    throttle_interval = fields.Integer(
        string='Interval Number',
        default=5,
    )

    throttle_interval_type = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ], string='Interval Type', default='minutes')

    estimated_completion_time = fields.Char(
        string='Estimated Completion',
        compute='_compute_estimated_completion',
    )

    @api.depends('throttle_batch_size', 'throttle_interval', 'throttle_interval_type', 'contact_list_ids')
    def _compute_estimated_completion(self):
        for mailing in self:
            if mailing.use_throttle and mailing.throttle_batch_size > 0:
                contact_count = sum(mailing.contact_list_ids.mapped('contact_count'))

                if contact_count > 0:
                    batches = (contact_count + mailing.throttle_batch_size - 1) // mailing.throttle_batch_size

                    interval_minutes = mailing.throttle_interval
                    if mailing.throttle_interval_type == 'hours':
                        interval_minutes = mailing.throttle_interval * 60
                    elif mailing.throttle_interval_type == 'days':
                        interval_minutes = mailing.throttle_interval * 60 * 24
                    elif mailing.throttle_interval_type == 'weeks':
                        interval_minutes = mailing.throttle_interval * 60 * 24 * 7
                    elif mailing.throttle_interval_type == 'months':
                        interval_minutes = mailing.throttle_interval * 60 * 24 * 30

                    total_minutes = batches * interval_minutes

                    if total_minutes < 60:
                        time_str = f"{total_minutes} minute(s)"
                    elif total_minutes < 1440:
                        hours = total_minutes // 60
                        mins = total_minutes % 60
                        time_str = f"{hours}h {mins}min" if mins > 0 else f"{hours}h"
                    else:
                        days = total_minutes // 1440
                        remaining_hours = (total_minutes % 1440) // 60
                        time_str = f"{days}d {remaining_hours}h" if remaining_hours > 0 else f"{days}d"

                    mailing.estimated_completion_time = f"~{time_str} ({batches} batches)"
                else:
                    mailing.estimated_completion_time = "No recipients"
            else:
                mailing.estimated_completion_time = "Instant (throttle disabled)"

    def action_send_mail(self, res_ids=None):
        """Send mail and configure CRON - LET emails be created normally"""

        if self.use_throttle:
            _logger.warning(f"🎯 THROTTLED MAILING: '{self.subject}'")
            _logger.warning(
                f"   Batch: {self.throttle_batch_size}, Interval: {self.throttle_interval} {self.throttle_interval_type}")

        # CALL PARENT - Let it create emails normally
        result = super(MailingMailing, self).action_send_mail(res_ids=res_ids)

        if self.use_throttle:
            # After emails created, configure CRON
            cron = self.env['ir.cron'].search([
                ('name', '=', 'Throttled Email Queue Manager')
            ], limit=1)

            if cron:
                cron.write({
                    'interval_number': self.throttle_interval,
                    'interval_type': self.throttle_interval_type,
                    'nextcall': datetime.now() + timedelta(seconds=10),
                    'active': True
                })
                _logger.warning(f"⚡ CRON configured: First batch in 10 seconds")

            # Verify emails were marked
            self.env.cr.commit()  # Ensure data is committed

            recent_mails = self.env['mail.mail'].search([
                ('mailing_id', '=', self.id),
                ('state', '=', 'outgoing')
            ])

            _logger.warning(f"📧 Found {len(recent_mails)} emails in outgoing state")

            if recent_mails:
                marked = recent_mails.filtered(lambda m: m.throttle_batch)
                _logger.warning(f"   {len(marked)} marked for throttle, {len(recent_mails) - len(marked)} not marked")

        return result
