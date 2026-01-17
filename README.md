# Custom-Email-Throttle
Because sending 1000+ emails at once is a bad idea.

Odoo is great at sending emails.
Sometimes, too great.

By default, bulk emails—especially from Email Marketing—can hit your SMTP server all at once, causing:

server overload,
SMTP rate-limit violations,
spam flags,
angry email providers.

This module was built to fix that problem properly, not with hacks.

🧠 What This Module Actually Does

This is not just a delay script.
It introduces a complete email throttling system in Odoo by combining:
queue-based email handling,
scheduled batch processing,
and user-controlled throttling inside Email Marketing itself.

You decide:

how many emails go out,
how often they go out,
and per campaign, not globally.

🔥 Key Features (Real, Practical)
✅ Queue-Based Email Sending

All emails are pushed into Odoo’s native mail.mail queue instead of being sent immediately.
No direct SMTP flooding. Ever.

✅ Scheduled Batch Processing

Emails are sent using Scheduled Actions, allowing you to define:
batch size (e.g. 1, 5, 10 emails)
execution interval (e.g. every 1, 5, 10 minutes)
This ensures predictable and controlled delivery.

✅ Throttle Control Inside Email Marketing

A custom Throttle Control tab is added to Email Marketing campaigns.
While creating a campaign, users can define:
emails per batch
interval between batches

No developer intervention needed.
No config files.
No guesswork.

✅ SMTP & Server Safe

Designed specifically to:
respect SMTP provider limits,
avoid spam-triggering spikes,
keep Odoo responsive during large campaigns.

✅ Production-Oriented Design

Uses native Odoo models and cron jobs
No external services required
Safe to deploy on live systems
Compatible with Enterprise setups

🧩 How It Works (Simple Flow)

Emails are generated and stored in the mail queue (mail.mail)
Emails are not sent immediately → no direct SMTP calls
A scheduled action processes emails in controlled batches
Campaign-level throttle settings define batch size & interval
Emails are delivered gradually, safely, and predictably
