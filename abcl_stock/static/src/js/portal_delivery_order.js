/** @odoo-module **/

import { loadJS } from "@web/core/assets"
import publicWidget from "@web/legacy/js/public/public_widget"
import { rpc } from "@web/core/network/rpc"
import { browser } from "@web/core/browser/browser";

publicWidget.registry.DeliveryOrderWidget = publicWidget.Widget.extend({
    selector: '#delivery_order_form',
    events: {
        'change .product-select': '_onProductChange',
        'click .add-line-button': '_onAddLineClick',
        'click .remove-line-button': '_onRemoveLineClick'
    },

    willStart: async function () {
        await loadJS("/abcl_purchase/static/src/js/jquery.validate.min.js");
        try {
        const response = await rpc("/delivery_order/get_product_data");
        this.productList = response|| [];
    } catch (error) {
        console.error("Error loading product data during willStart:", error);
        this.productList = [];
    }
    },

    init: function() {
        this.current_id = $('.order-line').length;
        this._super.apply(this, arguments);
        this._initializeUI();
        this.showHideButton();
    },



    showHideButton: function(){
        $('.order-line').length > 1 ? $(".remove-line-button").show() :$(".remove-line-button").hide();
    },

    start: function () {
        this._setupValidation()
        return this._super.apply(this, arguments);
    },

    _initializeUI: function() {
        $("div.o_portal_wrap .container:first").removeClass('container').addClass('container-fluid');
    },


    _setupValidation: function() {
        if ($.validator) {
            $("#delivery_order_form").validate({
                errorElement: "span",
                errorPlacement: function(error, element) {
                },
                highlight: function(element) {
                    $(element).css({'background': '#ffdddd','z-index':'999'});
                },
                unhighlight: function(element) {
                    $(element).css('background', '#ffffff');
                },
            });
        }
    },

    _onProductChange: function (ev) {
        const $productSelect = $(ev.currentTarget);
        const selectedProductId = parseInt($productSelect.val());

        const $uomElement = $productSelect.closest('.order-line').find("[name^='uom_id_']");

        const matchedProduct = this.productList.find(p => p && p.id === selectedProductId);
        const uomName = matchedProduct?.uom_name || '';

        $uomElement.text(uomName);
    },

    _onAddLineClick: function(ev) {
        var self = this;
        var newElement = self.$el.find("#order_line_body .order-line:first").clone();
        self.current_id += 1;
        newElement.find("input,select").val("");
        newElement.find("span").text("");

        newElement.find('input,select,span').each(function() {
            var name = $(this).attr('name');
            if (name) {
                var newName = name.replace(/\d+/, self.current_id);
                $(this).attr('name', newName);
            }
        });

        self.$el.find("#order_line_body").append(newElement);
        self.showHideButton();
    },

    _onRemoveLineClick: function(ev) {
        $(ev.currentTarget).closest(".order-line").remove();
        this.showHideButton();
    },

});

export default publicWidget.registry.DeliveryOrderWidget;





