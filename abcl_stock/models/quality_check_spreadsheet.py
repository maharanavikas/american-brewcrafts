from odoo import models, fields
import json
import re


class QualityCheckSpreadsheet(models.Model):
    _inherit = 'quality.check.spreadsheet'


##############for receipts################
    # def join_spreadsheet_session(self, access_token=None):
    #     print("join_spreadsheet_session")
    #     data = super().join_spreadsheet_session(access_token)
    #
    #     check = self.env['quality.check'].search([('spreadsheet_id', '=', self.id)], limit=1)
    #     data.update({
    #         'quality_check_display_name': check.display_name,
    #         'quality_check_cell': self.check_cell
    #     })
    #
    #     if check.picking_id.picking_type_code != 'incoming' or not check.point_id:
    #         return data
    #
    #     point = check.point_id
    #     cell_map = {
    #         'Product': point.product_cell,
    #         'Quantity': point.qty_cell,
    #         'UOM': point.uom_cell,
    #     }
    #
    #     positions = {
    #         field: (
    #             ''.join(filter(str.isalpha, ref)).upper(),
    #             int(''.join(filter(str.isdigit, ref)) or 1)
    #         )
    #         for field, ref in cell_map.items() if ref
    #     }
    #
    #     if not positions:
    #         print("No target cells provided in quality point")
    #         return data
    #
    #     sheet = data.setdefault('data', {}).setdefault('sheets', [{}])[0]
    #     cells = sheet.setdefault('cells', {})
    #     row_pointer = {col: row for col, row in positions.values()}
    #
    #     target_product_id = check.product_id.id
    #
    #     for line in check.picking_id.move_line_ids.filtered(lambda l: l.product_id.id == target_product_id):
    #         values = {
    #             'Product': line.product_id.name or 'N/A',
    #             'Quantity': line.quantity or 0.0,
    #             'UOM': line.product_uom_id.name or 'N/A',
    #         }
    #
    #         for field, value in values.items():
    #             if field not in positions:
    #                 continue
    #
    #             col, _ = positions[field]
    #             row = row_pointer[col]
    #             cell_key = f"{col}{row}"
    #
    #             if not cells.get(cell_key, {}).get('content'):
    #                 cells[cell_key] = {"content": str(value)}
    #                 row_pointer[col] += 1
    #
    #     return data


    ###########################for recripts, manufacturing and internal transfers################33
    def join_spreadsheet_session(self, access_token=None):
        data = super().join_spreadsheet_session(access_token)

        check = self.env['quality.check'].search([('spreadsheet_id', '=', self.id)], limit=1)
        data.update({
            'quality_check_display_name': check.display_name,
            'quality_check_cell': self.check_cell
        })

        if not check or not check.point_id:
            return data

        cell_map = {
            'Product': check.point_id.product_cell,
            'Quantity': check.point_id.qty_cell,
            'UOM': check.point_id.uom_cell,
        }
        positions = {
            field: (
                ''.join(filter(str.isalpha, ref)).upper(),
                int(''.join(filter(str.isdigit, ref)) or 1)
            )
            for field, ref in cell_map.items() if ref
        }
        if not positions:
            return data

        sheet = data.setdefault('data', {}).setdefault('sheets', [{}])[0]
        cells = sheet.setdefault('cells', {})
        row_pointer = {col: row for col, row in positions.values()}
        target_product_id = check.product_id.id
        target_lot = check.lot_id

        lines = []
        get_values = None

        if check.picking_id and check.picking_id.picking_type_code in ('incoming', 'internal', 'outgoing'):
            lines = check.picking_id.move_line_ids.filtered(
                lambda l: l.product_id.id == target_product_id and (not target_lot or l.lot_id == target_lot)
            )
            if lines:
                get_values = lambda line: {
                    'Product': line.product_id.name or 'N/A',
                    'Quantity': line.qty_done or 0.0,
                    'UOM': line.product_uom_id.name or 'N/A',
                }
            else:
                lines = check.picking_id.move_ids_without_package.filtered(
                    lambda m: m.product_id.id == target_product_id
                )
                get_values = lambda move: {
                    'Product': move.product_id.name or 'N/A',
                    'Quantity': move.product_uom_qty or 0.0,
                    'UOM': move.product_uom.name or 'N/A',
                }

        elif check.production_id:
            prod = check.production_id

            if check.measure_on == 'lots_serial_no' and target_lot:
                raw_moves = prod.move_raw_ids.filtered(lambda m: m.product_id.id == target_product_id)
                ml = raw_moves.mapped('move_line_ids').filtered(lambda l: l.lot_id == target_lot)
                if ml:
                    lines = ml
                    print("lines ---->", lines)
                    get_values = lambda line: {
                        'Product': line.product_id.display_name or 'N/A',
                        'Quantity': line.lot_id.product_qty or 0.0,
                        'UOM': line.product_uom_id.name or 'N/A',
                        # 'Lot/Serial Number': line.lot_id.name,
                    }
                else:
                    moves = raw_moves
                    lines = moves
                    get_values = lambda move: {
                        'Product': move.product_id.display_name or 'N/A',
                        'Quantity': move.product_uom_qty or 0.0,
                        'UOM': move.product_uom.name or 'N/A',
                    }

            else:
                # *** FINISHED PRODUCT CASE (original behavior) ***
                fin_moves = prod.move_finished_ids.filtered(lambda m: m.product_id.id == target_product_id)
                # Prefer lot-specific lines if they exist
                ml = fin_moves.mapped('move_line_ids')
                if target_lot:
                    ml = ml.filtered(lambda l: l.lot_id == target_lot)
                if ml:
                    lines = ml
                    get_values = lambda line: {
                        'Product': line.product_id.display_name or 'N/A',
                        'Quantity': line.qty_done or 0.0,
                        'UOM': line.product_uom_id.name or 'N/A',
                    }
                else:
                    lines = fin_moves
                    get_values = lambda move: {
                        'Product': move.product_id.display_name or 'N/A',
                        'Quantity': move.product_uom_qty or 0.0,
                        'UOM': move.product_uom.name or 'N/A',
                    }

        if get_values:
            for line in lines:
                values = get_values(line)
                for field, value in values.items():
                    if field not in positions:
                        continue
                    col, _ = positions[field]
                    row = row_pointer[col]
                    cell_key = f"{col}{row}"
                    if not cells.get(cell_key, {}).get('content'):
                        cells[cell_key] = {"content": str(value)}
                        row_pointer[col] += 1

        return data

    # def dispatch_spreadsheet_message(self, message: CollaborationMessage, access_token=None):
    #
    #     print("dispatch_spreadsheet_message---", message)
    #
    #     self.ensure_one()
    #
    #     check = self.env['quality.check'].search([('spreadsheet_id', '=', self.id)], limit=1)
    #
    #     if message["type"] in ["REMOTE_REVISION", "REVISION_UNDONE", "REVISION_REDONE"]:
    #
    #         if check and check.is_check_done and check.approver_id != self.env.user and check.quality_state == 'pass':
    #
    #             return False
    #
    #         elif check and check.quality_state == 'pass':
    #
    #             return False
    #
    #     return super(QualityCheckSpreadsheet, self).dispatch_spreadsheet_message(message, access_token)



