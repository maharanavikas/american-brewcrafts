/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";

export class PurchaseOrderListController extends ListController {
    setup() {
        super.setup();
    }

    generateDraftPO() {
        this.actionService.doAction({
        type: 'ir.actions.act_window',
        res_model: 'generate.draft.po.wizard',
        name: 'Create Draft PO',
        view_mode: 'form',
        views: [[false, 'form']],
        target: 'new',
    });

    }
}

const viewRegistry = registry.category("views");
export const CustomPOListController = {
    ...listView,
    Controller: PurchaseOrderListController,
};
viewRegistry.add("custom_po_list_controller", CustomPOListController);
