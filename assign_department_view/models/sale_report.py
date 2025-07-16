from odoo import fields, models


class SaleReport(models.Model):
    """Extends Sale Report to include department information."""
    _inherit = "sale.report"

    department_id = fields.Many2one('hr.department', string="Department")

    def _select_additional_fields(self):
        """Add department_id to the Sale Report selection query."""
        res = super()._select_additional_fields()
        res["department_id"] = "e.department_id"
        return res

    def _group_by_sale(self):
        """Add department_id to GROUP BY clause."""
        res = super()._group_by_sale()
        res += ", e.department_id"
        return res

    def _from_sale(self):
        """Add join with hr_employee table."""
        from_clause = super()._from_sale()
        return f"{from_clause} LEFT JOIN hr_employee e ON s.user_id = e.user_id"