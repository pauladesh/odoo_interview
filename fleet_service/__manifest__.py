{
    'name': 'Fleet Service Manager',
    'version': '16.0.1.0.0',
    'depends': ['base', 'fleet', 'mail'],
    'application': True,
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/fleet_service_views.xml',
        'views/fleet_service_menu.xml',
    ],
}
