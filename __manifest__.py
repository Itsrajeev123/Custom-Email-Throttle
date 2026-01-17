{
    'name': 'Custom Email Throttle',
    'version': '2.0',
    'category': 'Marketing/Email Marketing',
    'summary': 'Send emails in controlled batches with time delay',
    'depends': ['mail', 'mass_mailing'],
    'data': [
        'views/mailing_mailing_views.xml', 
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
