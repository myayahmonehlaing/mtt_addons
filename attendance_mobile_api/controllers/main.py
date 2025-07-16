import json
import logging

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class AttendanceAPI(http.Controller):

    @http.route('/api/attendance_range', type='http', auth='user', methods=['POST'], csrf=False)
    def get_attendance_range(self, **kwargs):
        try:
            # Get the raw POST data
            raw_data = request.httprequest.get_data().decode('utf-8')
            data = json.loads(raw_data)

            _logger.info("Incoming attendance range request from user %s: %s",
                         request.env.user.name, data)

            # No need for token check - auth='user' already verifies authentication
            start_date = data.get('start_date')
            end_date = data.get('end_date')

            if not start_date or not end_date:
                raise ValueError("Start date and end date are required.")

            # Check if user has HR permissions
            if not request.env.user.has_group('hr.group_hr_user'):
                raise ValueError("You don't have permission to access attendance data")

            # Search with current user's environment (no need for user=1)
            attendances = request.env['hr.attendance'].search([
                ('check_in', '>=', f"{start_date} 00:00:00"),
                ('check_in', '<=', f"{end_date} 23:59:59")
            ])

            attendance_data = [{
                'employee': att.employee_id.name,
                'check_in': att.check_in.strftime("%Y-%m-%d %H:%M:%S") if att.check_in else None,
                'check_out': att.check_out.strftime("%Y-%m-%d %H:%M:%S") if att.check_out else None
            } for att in attendances]

            return Response(json.dumps({
                'success': True,
                'attendances': attendance_data
            }), content_type='application/json')

        except Exception as error:
            _logger.error("Attendance fetch failed for user %s: %s",
                          request.env.user.name, str(error), exc_info=True)
            return Response(json.dumps({
                'success': False,
                'error': str(error),
                'message': 'Unable to fetch attendance data.'
            }), content_type='application/json')

# import json
# import logging
#
# from odoo import http
# from odoo.http import request, Response
#
# _logger = logging.getLogger(__name__)
# API_TOKEN = "MY-CUSTOMER-API-KEY-456"
#
#
# class AttendanceAPI(http.Controller):
#
#
#     @http.route('/api/attendance_range', type='http', auth='none', methods=['POST'], csrf=False)
#     def get_attendance_range(self, **kwargs):
#         try:
#             raw_data = request.httprequest.get_data().decode('utf-8')
#             data = json.loads(raw_data)
#
#             _logger.info("Incoming attendance range request: %s", data)
#
#             if data.get('token') != API_TOKEN:
#                 raise ValueError("Unauthorized access — invalid token.")
#
#             start_date = data.get('start_date')
#             end_date = data.get('end_date')
#             if not start_date or not end_date:
#                 raise ValueError("Start date and end date are required.")
#
#             env = request.env(user=1)
#             attendance_model = env['hr.attendance']
#
#             attendances = attendance_model.search([
#                 ('check_in', '>=', f"{start_date} 00:00:00"),
#                 ('check_in', '<=', f"{end_date} 23:59:59")
#             ])
#
#             attendance_data = [{
#                 'employee': att.employee_id.name,
#                 'check_in': att.check_in.strftime("%Y-%m-%d %H:%M:%S") if att.check_in else None,
#                 'check_out': att.check_out.strftime("%Y-%m-%d %H:%M:%S") if att.check_out else None
#             } for att in attendances]
#
#             return Response(json.dumps({
#                 'success': True,
#                 'attendances': attendance_data
#             }), content_type='application/json')
#
#         except Exception as error:
#             _logger.error("Attendance fetch failed", exc_info=True)
#             return Response(json.dumps({
#                 'success': False,
#                 'error': str(error),
#                 'message': 'Unable to fetch attendance data.'
#             }), content_type='application/json')
