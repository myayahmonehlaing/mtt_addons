from odoo import http
from odoo.http import request, Response
import json
import logging
import re

_logger = logging.getLogger(__name__)


class LeadController(http.Controller):

    @http.route('/api/create_lead', type='http', auth='public', methods=['POST'], csrf=False)
    def create_lead(self, **kwargs):
        try:
            raw_data = request.httprequest.get_data().decode('utf-8')
            data = json.loads(raw_data)
            _logger.info("Received lead data from IP %s: %s",
                         request.httprequest.remote_addr, data)

            # === PUBLIC USER RESTRICTIONS ===
            if request.env.user._is_public():
                # 1. Validate required fields
                if not all([data.get('name'), data.get('email_from')]):
                    raise ValueError("Name and email are required for public submissions")

                # 2. Validate email format
                if not re.match(r"[^@]+@[^@]+\.[^@]+", data.get('email_from', '')):
                    raise ValueError("Invalid email format")

                # 3. Rate limiting (pseudo-code - implement properly in production)
                if self._is_rate_limited(request.httprequest.remote_addr):
                    raise ValueError("Too many submissions. Please try again later")

            # === LEAD CREATION ===
            lead = request.env['crm.lead'].sudo().create({
                'name': data['name'],
                'email_from': data['email_from'],
                'phone': data.get('phone'),
                'partner_name': data.get('partner_name'),
                'description': data.get('description'),
                # Tag public submissions
                'tag_ids': [(4, request.env.ref('crm.categ_oppor1').id)]
                if request.env.user._is_public() else False
            })

            return Response(json.dumps({
                'success': True,
                'lead_id': lead.id,
                'message': 'Lead created successfully!'
            }), content_type='application/json')

        except Exception as e:
            _logger.error("Lead creation failed: %s", str(e), exc_info=True)
            return Response(json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to create lead. ' + str(e)
            }), content_type='application/json', status=400)

    def _is_rate_limited(self, ip):
        """Basic rate limiting (replace with proper implementation)"""
        # In production, use:
        # - request.env['ir.requests'].check_limit()
        # - Or Redis-based rate limiting
        return False

# from odoo import http
# from odoo.http import request, Response
# import json
# import logging
#
# _logger = logging.getLogger(__name__)
#
#
# class LeadController(http.Controller):
#
#     @http.route('/api/create_lead', type='http', auth='public', methods=['POST'], csrf=False)
#     def create_lead(self, **kwargs):
#         try:
#             raw_data = request.httprequest.get_data().decode('utf-8')
#             data = json.loads(raw_data)
#             _logger.info(f"Received lead data: {data}")
#
#             # Get the current user (public user if not authenticated)
#             current_user = request.env.user
#
#             # Option 1: Allow only authenticated users
#             if current_user._is_public():
#                 return Response(
#                     json.dumps({
#                         'success': False,
#                         'error': "Authentication required",
#                         'message': 'Please log in to create leads'
#                     }),
#                     content_type='application/json',
#                     status=401
#                 )
#
#             # Option 2: Or allow public users but with restrictions
#             # if current_user._is_public():
#             #     _logger.warning("Public user creating lead")
#
#             # Create lead with current user's environment
#             lead = request.env['crm.lead'].create({
#                 'name': data['name'],
#                 'email_from': data['email_from'],
#                 'phone': data.get('phone'),
#                 'partner_name': data.get('partner_name'),
#                 'description': data.get('description'),
#             })
#
#             response = {
#                 'success': True,
#                 'lead_id': lead.id,
#                 'message': 'Lead created successfully!'
#             }
#             _logger.info(f"Returning response: {response}")
#             return Response(json.dumps(response), content_type='application/json')
#
#         except Exception as e:
#             _logger.error("Lead creation failed", exc_info=True)
#             error_response = {
#                 'success': False,
#                 'error': str(e),
#                 'message': 'Failed to create lead.'
#             }
#             return Response(json.dumps(error_response), content_type='application/json', status=400)
