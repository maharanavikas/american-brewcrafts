# -*- coding: utf-8 -*-
import base64
from odoo.http import request, Controller, route
from datetime import datetime
from werkzeug.exceptions import NotFound


class FleetTrack(Controller):

    @route('/abcl/fleet_track', type='http', auth='public', website=True)
    def send_fleet_tracking_link(self, **kwargs):
        name = kwargs.get('t')
        if not name:
            raise NotFound("Access Declined or Invalid link.")

        return request.render('abcl_stock.get_fleet_location_template', {'name': name})

    @route('/abcl/tracking', type='http', auth='public', methods=['POST'], website=True, )
    def track_form_submit(self, **post):
        name = post.get('name')
        if not name:
            return "Access Declined2."
        latitude = post.get('latitude')
        longitude = post.get('longitude')
        timestamp = post.get('timestamp')

        get_record = request.env['stock.picking'].sudo().search([('name', '=', name)], limit=1)
        if not get_record:
            raise NotFound("Record not found with name: {}".format(name))

        timestamp_sec = int(timestamp) / 1000
        dt = datetime.utcfromtimestamp(timestamp_sec)

        request.env['fleet.vehicle.tracking'].sudo().create({
            'dispatch_id': get_record.id,
            'longitude': longitude,
            'latitude': latitude,
            'timestamp': dt,
        })
        
        return request.render('abcl_stock.thank_you')
