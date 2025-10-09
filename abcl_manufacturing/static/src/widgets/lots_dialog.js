/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { GenerateDialog } from "@stock/widgets/generate_serial";
import { Component, useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";


patch(GenerateDialog.prototype, {
    setup() {
        super.setup(...arguments);

        this.orm = useService("orm");
        this.mfgDate = useRef("mfgDate");

        onMounted(async () => {
            const productId = this.props.move.data.product_id?.[0];
            if (productId) {
                const [product] = await this.orm.read("product.product", [productId], ["manufacturing_date"]);
                if (product?.manufacturing_date && this.mfgDate.el) {
                    this.mfgDate.el.value = product.manufacturing_date;
                }
                console.log("Default product manufacturing date:", product?.manufacturing_date);
            }
        });
    },

    async _onGenerate() {
        const value = this.mfgDate?.el?.value || false;

        this.props.move.context.default_manufacturing_date = value;

        console.log("mfgDate value:", value);
        console.log("Move context:", this.props.move.context);

        return super._onGenerate(...arguments);
    },
});