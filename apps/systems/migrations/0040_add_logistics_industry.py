"""
Add Logistics industry template and Nordic logistics systems.
Shipping, freight, warehouse management, and carrier integrations.
"""
from django.db import migrations


def add_logistics_industry(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    Interface = apps.get_model('systems', 'Interface')
    Resource = apps.get_model('systems', 'Resource')
    Action = apps.get_model('systems', 'Action')
    IndustryTemplate = apps.get_model('systems', 'IndustryTemplate')
    TermMapping = apps.get_model('systems', 'TermMapping')
    EntityType = apps.get_model('systems', 'EntityType')

    # ==========================================================================
    # LOGISTICS INDUSTRY TEMPLATE
    # ==========================================================================
    logistics = IndustryTemplate.objects.create(
        name='logistics',
        display_name='Logistics & Supply Chain',
        description='Freight forwarding, shipping, warehousing, and supply chain management. Integrates TMS, WMS, carrier APIs, and tracking systems.',
        icon='truck',
        is_active=True
    )

    # ==========================================================================
    # LOGISTICS ENTITY TYPES
    # ==========================================================================
    entity_types = [
        {
            'name': 'shipment',
            'display_name': 'Shipment',
            'description': 'A shipment or consignment being transported',
            'icon': 'box-seam',
        },
        {
            'name': 'carrier',
            'display_name': 'Carrier',
            'description': 'Transport company or freight carrier',
            'icon': 'truck',
        },
        {
            'name': 'warehouse',
            'display_name': 'Warehouse',
            'description': 'Storage facility or distribution center',
            'icon': 'building',
        },
        {
            'name': 'order',
            'display_name': 'Order',
            'description': 'Customer order or purchase order',
            'icon': 'cart',
        },
        {
            'name': 'product',
            'display_name': 'Product/SKU',
            'description': 'Product or stock keeping unit',
            'icon': 'upc',
        },
        {
            'name': 'route',
            'display_name': 'Route',
            'description': 'Delivery route or transport lane',
            'icon': 'signpost-split',
        },
        {
            'name': 'vehicle',
            'display_name': 'Vehicle',
            'description': 'Truck, van, or other transport vehicle',
            'icon': 'truck-front',
        },
        {
            'name': 'driver',
            'display_name': 'Driver',
            'description': 'Driver or transport operator',
            'icon': 'person-badge',
        },
    ]

    for et in entity_types:
        EntityType.objects.get_or_create(
            name=et['name'],
            defaults={
                'display_name': et['display_name'],
                'description': et['description'],
                'icon': et['icon'],
                'is_active': True,
            }
        )

    # ==========================================================================
    # UNIFAUN - Swedish Shipping Platform (Nordics #1)
    # ==========================================================================
    unifaun = System.objects.create(
        name='unifaun',
        alias='unifaun',
        display_name='Unifaun',
        description='Nordic shipping platform. Multi-carrier shipping, label printing, tracking. Part of nShift. Used by 90% of Nordic e-commerce.',
        system_type='other',
        icon='box-seam',
        website_url='https://www.unifaun.com',
        industry=logistics,
        variables={'api_url': 'https://api.unifaun.com'},
        meta={'api_version': 'v2', 'countries': ['SE', 'NO', 'DK', 'FI']},
        is_active=True
    )

    unifaun_api = Interface.objects.create(
        system=unifaun, alias='api', name='api', type='API',
        base_url='https://api.unifaun.com/rs-extapi/v1',
        auth={'type': 'basic', 'description': 'API ID and secret as Basic auth'},
        rate_limits={'requests_per_minute': 120}
    )

    # Shipments
    unifaun_shipments = Resource.objects.create(
        interface=unifaun_api, alias='shipments', name='shipments',
        description='Create and manage shipments'
    )
    for action_def in [
        ('create', 'POST', '/shipments', 'Create new shipment'),
        ('get', 'GET', '/shipments/{shipment_id}', 'Get shipment details'),
        ('list', 'GET', '/shipments', 'List shipments'),
        ('delete', 'DELETE', '/shipments/{shipment_id}', 'Delete/cancel shipment'),
        ('get_labels', 'GET', '/shipments/{shipment_id}/pdfs', 'Get shipping labels PDF'),
        ('consolidate', 'POST', '/shipments/consolidate', 'Consolidate multiple shipments'),
    ]:
        Action.objects.create(
            resource=unifaun_shipments, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Tracking
    unifaun_tracking = Resource.objects.create(
        interface=unifaun_api, alias='tracking', name='tracking',
        description='Track shipments'
    )
    for action_def in [
        ('get_status', 'GET', '/shipments/{shipment_id}/statuses', 'Get tracking status'),
        ('get_events', 'GET', '/shipments/{shipment_id}/events', 'Get tracking events'),
        ('subscribe', 'POST', '/tracking/webhooks', 'Subscribe to tracking updates'),
    ]:
        Action.objects.create(
            resource=unifaun_tracking, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Carriers/Agents
    unifaun_carriers = Resource.objects.create(
        interface=unifaun_api, alias='carriers', name='carriers',
        description='Carrier configurations and services'
    )
    for action_def in [
        ('list', 'GET', '/carriers', 'List available carriers'),
        ('get_services', 'GET', '/carriers/{carrier_id}/services', 'Get carrier services'),
        ('get_prices', 'POST', '/carriers/prices', 'Get shipping prices from carriers'),
    ]:
        Action.objects.create(
            resource=unifaun_carriers, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Addresses
    unifaun_addresses = Resource.objects.create(
        interface=unifaun_api, alias='addresses', name='addresses',
        description='Address book and validation'
    )
    for action_def in [
        ('list', 'GET', '/addresses', 'List saved addresses'),
        ('create', 'POST', '/addresses', 'Create address'),
        ('validate', 'POST', '/addresses/validate', 'Validate address'),
        ('lookup', 'GET', '/addresses/lookup', 'Lookup address by postal code'),
    ]:
        Action.objects.create(
            resource=unifaun_addresses, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # CONSIGNOR - Norwegian Shipping (Descartes)
    # ==========================================================================
    consignor = System.objects.create(
        name='consignor',
        alias='consignor',
        display_name='Consignor (Descartes)',
        description='Norwegian shipping and logistics platform. Now part of Descartes. Strong in Norway and Denmark.',
        system_type='other',
        icon='send',
        website_url='https://www.consignor.com',
        industry=logistics,
        variables={'api_url': 'https://api.consignor.com'},
        meta={'api_version': 'v1', 'countries': ['NO', 'DK', 'SE']},
        is_active=True
    )

    consignor_api = Interface.objects.create(
        system=consignor, alias='api', name='api', type='API',
        base_url='https://api.consignor.com/v1',
        auth={'type': 'oauth2', 'token_url': 'https://api.consignor.com/oauth/token'},
        rate_limits={'requests_per_minute': 100}
    )

    # Shipments
    consignor_shipments = Resource.objects.create(
        interface=consignor_api, alias='shipments', name='shipments',
        description='Shipment management'
    )
    for action_def in [
        ('create', 'POST', '/shipments', 'Create shipment'),
        ('get', 'GET', '/shipments/{id}', 'Get shipment'),
        ('list', 'GET', '/shipments', 'List shipments'),
        ('update', 'PUT', '/shipments/{id}', 'Update shipment'),
        ('cancel', 'POST', '/shipments/{id}/cancel', 'Cancel shipment'),
        ('get_label', 'GET', '/shipments/{id}/label', 'Get shipping label'),
        ('get_documents', 'GET', '/shipments/{id}/documents', 'Get shipment documents'),
    ]:
        Action.objects.create(
            resource=consignor_shipments, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Tracking
    consignor_tracking = Resource.objects.create(
        interface=consignor_api, alias='tracking', name='tracking',
        description='Shipment tracking'
    )
    for action_def in [
        ('track', 'GET', '/tracking/{tracking_number}', 'Track by tracking number'),
        ('get_history', 'GET', '/tracking/{tracking_number}/history', 'Get full tracking history'),
        ('get_pod', 'GET', '/tracking/{tracking_number}/pod', 'Get proof of delivery'),
    ]:
        Action.objects.create(
            resource=consignor_tracking, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # POSTI (Finnish Post / PostNord)
    # ==========================================================================
    posti = System.objects.create(
        name='posti',
        alias='posti',
        display_name='Posti',
        description='Finnish postal service. Parcels, freight, logistics services. Extensive API for e-commerce and business shipping.',
        system_type='other',
        icon='mailbox',
        website_url='https://www.posti.fi',
        industry=logistics,
        variables={'api_url': 'https://api.posti.fi'},
        meta={'api_version': 'v1', 'country': 'FI'},
        is_active=True
    )

    posti_api = Interface.objects.create(
        system=posti, alias='api', name='api', type='API',
        base_url='https://api.posti.fi',
        auth={'type': 'oauth2', 'token_url': 'https://oauth.posti.fi/oauth/token'},
        rate_limits={'requests_per_minute': 100}
    )

    # Shipments
    posti_shipments = Resource.objects.create(
        interface=posti_api, alias='shipments', name='shipments',
        description='Create and manage shipments'
    )
    for action_def in [
        ('create', 'POST', '/shipments', 'Create shipment'),
        ('get', 'GET', '/shipments/{id}', 'Get shipment'),
        ('list', 'GET', '/shipments', 'List shipments'),
        ('get_label', 'GET', '/shipments/{id}/label', 'Get shipping label'),
        ('create_return', 'POST', '/shipments/{id}/return', 'Create return shipment'),
    ]:
        Action.objects.create(
            resource=posti_shipments, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Tracking
    posti_tracking = Resource.objects.create(
        interface=posti_api, alias='tracking', name='tracking',
        description='Track shipments'
    )
    for action_def in [
        ('track', 'GET', '/tracking/{tracking_code}', 'Track shipment'),
        ('track_multiple', 'POST', '/tracking/batch', 'Track multiple shipments'),
    ]:
        Action.objects.create(
            resource=posti_tracking, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Pickup points
    posti_pickups = Resource.objects.create(
        interface=posti_api, alias='pickup_points', name='pickup_points',
        description='Posti pickup points and parcel lockers'
    )
    for action_def in [
        ('search', 'GET', '/pickup-points', 'Search pickup points'),
        ('get', 'GET', '/pickup-points/{id}', 'Get pickup point details'),
        ('nearest', 'GET', '/pickup-points/nearest', 'Find nearest pickup points'),
    ]:
        Action.objects.create(
            resource=posti_pickups, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # DB SCHENKER - Global Freight
    # ==========================================================================
    schenker = System.objects.create(
        name='db_schenker',
        alias='db_schenker',
        display_name='DB Schenker',
        description='Global logistics company. Land transport, air/ocean freight, contract logistics. Strong presence in Nordics.',
        system_type='other',
        icon='globe',
        website_url='https://www.dbschenker.com',
        industry=logistics,
        variables={'api_url': 'https://api.dbschenker.com'},
        meta={'api_version': 'v1', 'global': True},
        is_active=True
    )

    schenker_api = Interface.objects.create(
        system=schenker, alias='api', name='api', type='API',
        base_url='https://api.dbschenker.com/v1',
        auth={'type': 'oauth2', 'token_url': 'https://api.dbschenker.com/oauth/token'},
        rate_limits={'requests_per_minute': 60}
    )

    # Shipments
    schenker_shipments = Resource.objects.create(
        interface=schenker_api, alias='shipments', name='shipments',
        description='Freight shipments'
    )
    for action_def in [
        ('create', 'POST', '/shipments', 'Create shipment'),
        ('get', 'GET', '/shipments/{id}', 'Get shipment'),
        ('list', 'GET', '/shipments', 'List shipments'),
        ('get_quote', 'POST', '/shipments/quote', 'Get shipping quote'),
        ('book', 'POST', '/shipments/{id}/book', 'Book shipment'),
        ('get_documents', 'GET', '/shipments/{id}/documents', 'Get shipment documents'),
    ]:
        Action.objects.create(
            resource=schenker_shipments, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Tracking
    schenker_tracking = Resource.objects.create(
        interface=schenker_api, alias='tracking', name='tracking',
        description='Shipment tracking'
    )
    for action_def in [
        ('track', 'GET', '/tracking/{reference}', 'Track shipment'),
        ('get_events', 'GET', '/tracking/{reference}/events', 'Get tracking events'),
        ('get_eta', 'GET', '/tracking/{reference}/eta', 'Get estimated arrival'),
    ]:
        Action.objects.create(
            resource=schenker_tracking, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # MATKAHUOLTO - Finnish Parcel & Bus Freight
    # ==========================================================================
    matkahuolto = System.objects.create(
        name='matkahuolto',
        alias='matkahuolto',
        display_name='Matkahuolto',
        description='Finnish parcel delivery and bus freight. Extensive pickup point network across Finland.',
        system_type='other',
        icon='bus-front',
        website_url='https://www.matkahuolto.fi',
        industry=logistics,
        variables={'api_url': 'https://api.matkahuolto.fi'},
        meta={'api_version': 'v1', 'country': 'FI'},
        is_active=True
    )

    matkahuolto_api = Interface.objects.create(
        system=matkahuolto, alias='api', name='api', type='API',
        base_url='https://api.matkahuolto.fi/v1',
        auth={'type': 'api_key', 'header': 'X-API-Key'},
        rate_limits={'requests_per_minute': 60}
    )

    # Shipments
    mh_shipments = Resource.objects.create(
        interface=matkahuolto_api, alias='shipments', name='shipments',
        description='Parcel shipments'
    )
    for action_def in [
        ('create', 'POST', '/shipments', 'Create shipment'),
        ('get', 'GET', '/shipments/{id}', 'Get shipment'),
        ('list', 'GET', '/shipments', 'List shipments'),
        ('get_label', 'GET', '/shipments/{id}/label', 'Get shipping label'),
        ('cancel', 'POST', '/shipments/{id}/cancel', 'Cancel shipment'),
    ]:
        Action.objects.create(
            resource=mh_shipments, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Tracking
    mh_tracking = Resource.objects.create(
        interface=matkahuolto_api, alias='tracking', name='tracking',
        description='Track parcels'
    )
    for action_def in [
        ('track', 'GET', '/tracking/{tracking_code}', 'Track parcel'),
    ]:
        Action.objects.create(
            resource=mh_tracking, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Pickup points
    mh_pickups = Resource.objects.create(
        interface=matkahuolto_api, alias='pickup_points', name='pickup_points',
        description='Pickup points and bus stations'
    )
    for action_def in [
        ('search', 'GET', '/pickup-points', 'Search pickup points'),
        ('get', 'GET', '/pickup-points/{id}', 'Get pickup point details'),
    ]:
        Action.objects.create(
            resource=mh_pickups, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # CARGOSON - Estonian Multi-carrier Platform
    # ==========================================================================
    cargoson = System.objects.create(
        name='cargoson',
        alias='cargoson',
        display_name='Cargoson',
        description='Estonian shipping platform. Multi-carrier freight booking, tracking, and analytics. Popular in Baltics and Nordics.',
        system_type='other',
        icon='diagram-3',
        website_url='https://www.cargoson.com',
        industry=logistics,
        variables={'api_url': 'https://api.cargoson.com'},
        meta={'api_version': 'v1', 'countries': ['EE', 'LV', 'LT', 'FI', 'SE']},
        is_active=True
    )

    cargoson_api = Interface.objects.create(
        system=cargoson, alias='api', name='api', type='API',
        base_url='https://api.cargoson.com/v1',
        auth={'type': 'bearer'},
        rate_limits={'requests_per_minute': 100}
    )

    # Shipments
    cargoson_shipments = Resource.objects.create(
        interface=cargoson_api, alias='shipments', name='shipments',
        description='Freight shipments'
    )
    for action_def in [
        ('create', 'POST', '/shipments', 'Create shipment'),
        ('get', 'GET', '/shipments/{id}', 'Get shipment'),
        ('list', 'GET', '/shipments', 'List shipments'),
        ('update', 'PUT', '/shipments/{id}', 'Update shipment'),
        ('delete', 'DELETE', '/shipments/{id}', 'Delete shipment'),
        ('get_offers', 'GET', '/shipments/{id}/offers', 'Get carrier offers/quotes'),
        ('book', 'POST', '/shipments/{id}/book', 'Book with selected carrier'),
        ('get_label', 'GET', '/shipments/{id}/label', 'Get shipping label'),
    ]:
        Action.objects.create(
            resource=cargoson_shipments, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Tracking
    cargoson_tracking = Resource.objects.create(
        interface=cargoson_api, alias='tracking', name='tracking',
        description='Track shipments'
    )
    for action_def in [
        ('track', 'GET', '/tracking/{reference}', 'Track shipment'),
        ('get_events', 'GET', '/tracking/{reference}/events', 'Get tracking events'),
    ]:
        Action.objects.create(
            resource=cargoson_tracking, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Carriers
    cargoson_carriers = Resource.objects.create(
        interface=cargoson_api, alias='carriers', name='carriers',
        description='Carrier management'
    )
    for action_def in [
        ('list', 'GET', '/carriers', 'List connected carriers'),
        ('get', 'GET', '/carriers/{id}', 'Get carrier details'),
        ('get_services', 'GET', '/carriers/{id}/services', 'Get carrier services'),
    ]:
        Action.objects.create(
            resource=cargoson_carriers, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # LOGIAPPS - Finnish WMS
    # ==========================================================================
    logiapps = System.objects.create(
        name='logiapps',
        alias='logiapps',
        display_name='Logiapps WMS',
        description='Finnish warehouse management system. Inventory management, order fulfillment, pick/pack operations.',
        system_type='storage',
        icon='boxes',
        website_url='https://www.logiapps.fi',
        industry=logistics,
        variables={'api_url': 'https://api.logiapps.fi'},
        meta={'api_version': 'v1', 'country': 'FI'},
        is_active=True
    )

    logiapps_api = Interface.objects.create(
        system=logiapps, alias='api', name='api', type='API',
        base_url='https://api.logiapps.fi/v1',
        auth={'type': 'bearer'},
        rate_limits={'requests_per_minute': 100}
    )

    # Inventory
    logiapps_inventory = Resource.objects.create(
        interface=logiapps_api, alias='inventory', name='inventory',
        description='Inventory management'
    )
    for action_def in [
        ('list', 'GET', '/inventory', 'List inventory'),
        ('get', 'GET', '/inventory/{sku}', 'Get inventory for SKU'),
        ('adjust', 'POST', '/inventory/{sku}/adjust', 'Adjust inventory'),
        ('transfer', 'POST', '/inventory/transfer', 'Transfer between locations'),
        ('get_movements', 'GET', '/inventory/{sku}/movements', 'Get inventory movements'),
    ]:
        Action.objects.create(
            resource=logiapps_inventory, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Orders
    logiapps_orders = Resource.objects.create(
        interface=logiapps_api, alias='orders', name='orders',
        description='Order fulfillment'
    )
    for action_def in [
        ('list', 'GET', '/orders', 'List orders'),
        ('get', 'GET', '/orders/{id}', 'Get order details'),
        ('create', 'POST', '/orders', 'Create order'),
        ('update', 'PUT', '/orders/{id}', 'Update order'),
        ('cancel', 'POST', '/orders/{id}/cancel', 'Cancel order'),
        ('get_picks', 'GET', '/orders/{id}/picks', 'Get pick list'),
        ('confirm_pick', 'POST', '/orders/{id}/picks/confirm', 'Confirm picks'),
        ('ship', 'POST', '/orders/{id}/ship', 'Mark as shipped'),
    ]:
        Action.objects.create(
            resource=logiapps_orders, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Receiving
    logiapps_receiving = Resource.objects.create(
        interface=logiapps_api, alias='receiving', name='receiving',
        description='Inbound receiving'
    )
    for action_def in [
        ('list_asn', 'GET', '/receiving/asn', 'List advance ship notices'),
        ('create_asn', 'POST', '/receiving/asn', 'Create ASN'),
        ('receive', 'POST', '/receiving/{asn_id}/receive', 'Receive goods'),
        ('get_discrepancies', 'GET', '/receiving/{asn_id}/discrepancies', 'Get receiving discrepancies'),
    ]:
        Action.objects.create(
            resource=logiapps_receiving, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Locations
    logiapps_locations = Resource.objects.create(
        interface=logiapps_api, alias='locations', name='locations',
        description='Warehouse locations'
    )
    for action_def in [
        ('list', 'GET', '/locations', 'List warehouse locations'),
        ('get', 'GET', '/locations/{id}', 'Get location details'),
        ('get_inventory', 'GET', '/locations/{id}/inventory', 'Get inventory at location'),
    ]:
        Action.objects.create(
            resource=logiapps_locations, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # ONGOING WMS - Swedish Cloud WMS
    # ==========================================================================
    ongoing = System.objects.create(
        name='ongoing_wms',
        alias='ongoing_wms',
        display_name='Ongoing WMS',
        description='Swedish cloud-based warehouse management system. Used by 3PLs and e-commerce in Nordics.',
        system_type='storage',
        icon='cloud-arrow-up',
        website_url='https://www.ongoingwarehouse.com',
        industry=logistics,
        variables={'api_url': 'https://api.ongoingwarehouse.com'},
        meta={'api_version': 'v1', 'countries': ['SE', 'NO', 'DK', 'FI']},
        is_active=True
    )

    ongoing_api = Interface.objects.create(
        system=ongoing, alias='api', name='api', type='API',
        base_url='https://api.ongoingwarehouse.com',
        auth={'type': 'basic'},
        rate_limits={'requests_per_minute': 100}
    )

    # Articles (Products)
    ongoing_articles = Resource.objects.create(
        interface=ongoing_api, alias='articles', name='articles',
        description='Product/article master data'
    )
    for action_def in [
        ('list', 'GET', '/articles', 'List articles'),
        ('get', 'GET', '/articles/{id}', 'Get article'),
        ('create', 'POST', '/articles', 'Create article'),
        ('update', 'PUT', '/articles/{id}', 'Update article'),
        ('get_inventory', 'GET', '/articles/{id}/inventory', 'Get article inventory'),
    ]:
        Action.objects.create(
            resource=ongoing_articles, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Orders
    ongoing_orders = Resource.objects.create(
        interface=ongoing_api, alias='orders', name='orders',
        description='Outbound orders'
    )
    for action_def in [
        ('list', 'GET', '/orders', 'List orders'),
        ('get', 'GET', '/orders/{id}', 'Get order'),
        ('create', 'POST', '/orders', 'Create order'),
        ('update', 'PUT', '/orders/{id}', 'Update order'),
        ('cancel', 'DELETE', '/orders/{id}', 'Cancel order'),
        ('get_status', 'GET', '/orders/{id}/status', 'Get order status'),
    ]:
        Action.objects.create(
            resource=ongoing_orders, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # Purchase orders (inbound)
    ongoing_po = Resource.objects.create(
        interface=ongoing_api, alias='purchase_orders', name='purchase_orders',
        description='Inbound purchase orders'
    )
    for action_def in [
        ('list', 'GET', '/purchaseorders', 'List purchase orders'),
        ('get', 'GET', '/purchaseorders/{id}', 'Get purchase order'),
        ('create', 'POST', '/purchaseorders', 'Create purchase order'),
    ]:
        Action.objects.create(
            resource=ongoing_po, alias=action_def[0], name=action_def[0],
            method=action_def[1], path=action_def[2], description=action_def[3],
            parameters_schema={'type': 'object', 'properties': {}}
        )

    # ==========================================================================
    # TERM MAPPINGS FOR LOGISTICS
    # ==========================================================================

    # Unifaun term mappings
    for canonical, system_term in [
        ('shipment', 'Shipment'),
        ('carrier', 'Agent'),
        ('tracking', 'Status'),
        ('label', 'PDF'),
        ('order', 'Order'),
    ]:
        TermMapping.objects.create(
            template=logistics, canonical_term=canonical,
            system=unifaun, system_term=system_term
        )

    # Posti term mappings
    for canonical, system_term in [
        ('shipment', 'Lähetys'),
        ('tracking', 'Seuranta'),
        ('pickup_point', 'Noutopiste'),
        ('parcel', 'Paketti'),
        ('label', 'Osoitekortti'),
    ]:
        TermMapping.objects.create(
            template=logistics, canonical_term=canonical,
            system=posti, system_term=system_term
        )

    # Matkahuolto term mappings
    for canonical, system_term in [
        ('shipment', 'Lähetys'),
        ('tracking', 'Seuranta'),
        ('pickup_point', 'Noutopiste'),
        ('parcel', 'Paketti'),
    ]:
        TermMapping.objects.create(
            template=logistics, canonical_term=canonical,
            system=matkahuolto, system_term=system_term
        )

    # Logiapps term mappings
    for canonical, system_term in [
        ('order', 'Tilaus'),
        ('inventory', 'Varasto'),
        ('warehouse', 'Varasto'),
        ('product', 'Tuote'),
        ('location', 'Paikka'),
        ('pick', 'Keräily'),
    ]:
        TermMapping.objects.create(
            template=logistics, canonical_term=canonical,
            system=logiapps, system_term=system_term
        )


def remove_logistics_industry(apps, schema_editor):
    System = apps.get_model('systems', 'System')
    IndustryTemplate = apps.get_model('systems', 'IndustryTemplate')

    # Remove systems
    System.objects.filter(alias__in=[
        'unifaun', 'consignor', 'posti', 'db_schenker',
        'matkahuolto', 'cargoson', 'logiapps', 'ongoing_wms'
    ]).delete()

    # Remove industry template
    IndustryTemplate.objects.filter(name='logistics').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('systems', '0039_add_admicom_planner'),
    ]

    operations = [
        migrations.RunPython(add_logistics_industry, remove_logistics_industry),
    ]
