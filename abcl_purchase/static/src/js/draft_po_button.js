/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";

patch(ListController.prototype, {
    generateDraftPO() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "generate.draft.po.wizard",
            name: "Create Draft PO",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    },
});

