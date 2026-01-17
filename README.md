# Custom-Email-Throttle
Custom Email Throttle for Odoo (Enterprise & Community)

This module introduces a queue-based email throttling mechanism in Odoo to prevent bulk email overload and SMTP rate-limit issues.

By default, certain Odoo features (especially bulk or automated emails) may send multiple emails at once, which can:

overload the mail server,

violate SMTP provider limits,

cause emails to be flagged as spam.

This module solves that problem by forcing emails to respect a controlled sending rate using Odoo’s native email queue (mail.mail) and scheduled actions.
