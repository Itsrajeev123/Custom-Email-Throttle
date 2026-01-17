from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    throttle_batch = fields.Boolean(
        string='Use Throttle Batch',
        default=False,
        index=True,
    )

    throttle_batch_size = fields.Integer(
        string='Batch Size',
        default=10,
    )

    throttle_interval = fields.Integer(
        string='Interval',
        default=5,
    )

    throttle_interval_type = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ], string='Interval Type', default='minutes')

    # -*- create() method override -*-
    @api.model_create_multi
    def create(self, vals_list):
        """Mark emails from throttled mailings"""
        mails = super(MailMail, self).create(vals_list)

        for mail in mails:
            if mail.mailing_id and mail.mailing_id.use_throttle:
                mail.write({
                    'throttle_batch': True,
                    'throttle_batch_size': mail.mailing_id.throttle_batch_size,
                    'throttle_interval': mail.mailing_id.throttle_interval,
                    'throttle_interval_type': mail.mailing_id.throttle_interval_type,
                })
                _logger.warning(
                    f"🎯 Email {mail.id} MARKED for throttle: batch={mail.throttle_batch_size}, interval={mail.throttle_interval} {mail.throttle_interval_type}")

        return mails

    # -*- send() method override -*-
    def send(self, auto_commit=False, raise_exception=False):
        """BLOCK throttled emails from immediate sending"""
        throttled = self.filtered(lambda m: m.throttle_batch)
        non_throttled = self - throttled

        if throttled:
            _logger.warning(f"🛑 BLOCKED {len(throttled)} throttled emails from immediate send")
            _logger.warning(f"   IDs: {throttled.ids}")
            _logger.warning(f"   These emails will ONLY be sent by CRON job")
            # DON'T send - return True without doing anything
            return True

        if non_throttled:
            _logger.info(f"📮 Sending {len(non_throttled)} non-throttled emails normally")
            return super(MailMail, non_throttled).send(auto_commit=auto_commit, raise_exception=raise_exception)

        return True

    # -*- _send() method override -*-
    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None, **kwargs):
        """BLOCK at _send level too"""
        throttled = self.filtered(lambda m: m.throttle_batch)
        non_throttled = self - throttled

        if throttled:
            _logger.warning(f"🛑 _send() BLOCKED {len(throttled)} throttled emails")
            return True

        if non_throttled:
            return super(MailMail, non_throttled)._send(
                auto_commit=auto_commit,
                raise_exception=raise_exception,
                smtp_session=smtp_session,
                **kwargs
            )

        return True

    # -*- Custom Method - process_email_queue_throttled() -*-
    def process_email_queue_throttled(self, batch_size=None):
        """Process throttled emails in controlled batches"""

        if batch_size is None:
            sample = self.search([
                ('state', '=', 'outgoing'),
                ('throttle_batch', '=', True)
            ], limit=1)
            batch_size = sample.throttle_batch_size if sample and sample.throttle_batch_size else 10

        _logger.info(f"🚀 Throttled Queue: Processing batch of {batch_size} emails")

        domain = [
            ('state', '=', 'outgoing'),
            ('throttle_batch', '=', True),
            '|',
            ('scheduled_date', '<=', fields.Datetime.now()),
            ('scheduled_date', '=', False)
        ]

        pending = self.search(domain, limit=batch_size, order='create_date asc')

        if pending:
            _logger.info(f"📧 Found {len(pending)} throttled emails")
            _logger.info(f"   IDs: {pending.ids}")

            # Remove throttle flag BEFORE sending
            pending.write({'throttle_batch': False})

            try:
                # Now send via parent method
                super(MailMail, pending).send(auto_commit=True)
                _logger.info(f"✅ Successfully sent {len(pending)} emails")
            except Exception as e:
                _logger.error(f"❌ Error: {e}")
                pending.write({'throttle_batch': True})
                raise
        else:
            _logger.info("📭 No throttled emails in queue")

        return True
