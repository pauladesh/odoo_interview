{
    'name': 'Fleet Service Manager',
    'version': '16.0.1.0.0',
    'depends': ['base', 'fleet', 'mail'],
    'application': True,
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/fleet_service_record_views.xml',
        'views/fleet_service_tag_views.xml',
        'views/fleet_service_line_views.xml',
        'views/fleet_service_menus.xml',
    ],
}
