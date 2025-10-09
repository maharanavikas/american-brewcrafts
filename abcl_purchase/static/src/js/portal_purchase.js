/** @odoo-module **/

import { loadJS } from "@web/core/assets"
import publicWidget from "@web/legacy/js/public/public_widget"
import { rpc } from "@web/core/network/rpc"
import { browser } from "@web/core/browser/browser";


publicWidget.registry.PurchaseOrderWidget = publicWidget.Widget.extend({
    selector: '#purchase_order_form',
    events: {
        'change #vendor_select': '_onVendorChange',
        'change .product-select': '_onProductChange',
        'click #send-for-approval-btn': '_onSendForApprovalClick',
    },

    willStart: async function () {
        await loadJS("/abcl_purchase/static/src/js/jquery.validate.min.js");
    },

    init: function() {
        this._super.apply(this, arguments);
        this.initializeUI();
    },

    initializeUI: ()=> $("div.o_portal_wrap .container:first").removeClass('container').addClass('container-fluid'),

    start: function () {
        this.availableVendors = []
        this.productData = []
        this.purchaseRecord = parseInt(this.$el.attr('data-id'))
        this.vendorSelect = this.$el.find('#vendor_select')
        this.categorySelect = this.$el.find('#product_category')
        this.categorySelect.prop('disabled', true);

        this.initialProductSelections = [];
        this.$el.find('.product-select').each((index, element) => {
            const $element = $(element);
            this.initialProductSelections[index] = $element.val();
        });



        this._initializeCategoriesVendors();
        this._setupValidation();

        return this._super.apply(this, arguments);
    },


    _initializeCategoriesVendors: async function() {
        this.productList = await rpc("/purchase_order/get_products_list")

        this.categoryData = await rpc("/web/dataset/call_kw/product.category/search_read", {
            model: "product.category",
            method: "search_read",
            args: [],
            kwargs: { domain: [['enable_internal_po', '=', true]], fields: ['id','name'] },
        });

        if(!this.purchaseRecord && this.categoryData.length){
            this.categoryData.forEach(item => {
                this.categorySelect.append($('<option></option>').val(item.id).text(item.name))
            })
        }

        let productMap = new Map();
        this.productList.forEach(product => {
            if (!productMap.has(product.product_id)) {
                productMap.set(product.product_id, {
                    id: product.product_id,
                    name: product.product_name,
                    uom_name: product.uom_name,
                    category_id: product.category_id,
                    category_name: this.categoryData.find(c => c.id === product.category_id)?.name || '',
                    vendors: []
                });
            }
            product.vendors.forEach(v => {
                productMap.get(product.product_id).vendors.push(v);
            });
        });
        this.productData = Array.from(productMap.values());

        this.$el.find('.product-select').each((index, element) => {
            this._updateProductSelect($(element), index);
        });
    },

    _updateProductSelect: function($productSelect, index) {
        const currentProduct = this.initialProductSelections[index] || $productSelect.val();

        $productSelect.find('option').not(':first').remove();

        this.productData.sort((a, b) => a.name.localeCompare(b.name));
        this.productData.forEach(p => {
            $productSelect.append($('<option></option>').val(p.id).text(p.name));
        });

        if (currentProduct) {
            $productSelect.val(currentProduct);

            let fakeEv = {currentTarget: $productSelect[0], target: $productSelect[0]};
            this._onProductChange(fakeEv);
        }
    },

    populateVendors: function (){
        let $vendorSelect = this.vendorSelect;
        let currentVendor = $vendorSelect.val();

        $vendorSelect.find('option').not(':first').remove()
        this.availableVendors.sort((a, b) => a.partner_name.localeCompare(b.partner_name));
        this.availableVendors.forEach(item => {
            $vendorSelect.append($('<option></option>').val(item.partner_id).text(item.partner_name))
        });
        if (currentVendor) {
            $vendorSelect.val(currentVendor);
        }
    },

    _setupValidation: function() {
        if($.validator) {
            $("#purchase_order_form").validate({
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

    _onVendorChange: function(ev) {
        const selectedVendor = parseInt(ev.target.value);

        const $productSelect = this.$el.find('.product-select');
        const selectedProductId = parseInt($productSelect.val()) || null;

        if (selectedProductId && selectedVendor) {
            const product = this.productData.find(p => p.id === selectedProductId);
            if (!product.vendors.some(v => v.partner_id === selectedVendor)) {
                alert("This vendor does not supply the selected product.");
                this.vendorSelect.val('');
                return;
            }
        }
    },

    _onProductChange: function(ev) {
        const $productSelect = $(ev.currentTarget);
        const selectedProductId = parseInt($productSelect.val());

        const product = this.productData.find(p => p.id === selectedProductId);
        if (product) {
            this.categorySelect.val(product.category_id);
            this.availableVendors = product.vendors;
            this.populateVendors();
            const currentVendor = parseInt(this.vendorSelect.val()) || null;
            if (currentVendor && !this.availableVendors.some(v => v.partner_id === currentVendor)) {
                this.vendorSelect.val('');
            }
            const $uomElement = $productSelect.closest('.order-line').find("[name^='uom_id_']");
            $uomElement.text(product.uom_name);
        }
    },

    _onSendForApprovalClick: function (ev) {
        if(this.purchaseRecord) {
            browser.location.href = `/purchase_order/${this.purchaseRecord}/send_for_approval`;
            $("#send-for-approval-btn").hide();
        }
    },

});

export default publicWidget.registry.PurchaseOrderWidget;

//publicWidget.registry.PurchaseOrderWidget = publicWidget.Widget.extend({
//    selector: '#purchase_order_form',
//    events: {
//        'change #product_category': '_onCategoryChange',
//        'change #vendor_select': '_onVendorChange',
//        'change .product-select': '_onProductChange',
//        'click .add-line-button': '_onAddLineClick',
//        'click .remove-line-button': '_onRemoveLineClick',
//        'click #send-for-approval-btn': '_onSendForApprovalClick',
//    },
//
//    willStart: async function () {
//        await loadJS("/abcl_purchase/static/src/js/jquery.validate.min.js");
//    },
//
//    init: function() {
//        this.current_id = $('.order-line').length;
//        this._super.apply(this, arguments);
//        this.initializeUI();
//    },
//
//
//    showHideButton: function (){
//        this.$el.find('.order-line').length > 1 ? $(".remove-line-button").show() :$(".remove-line-button").hide()
//        this.$el.find('.order-line').first().find('select option').length > 2 ? $(".add-line-button").show(): $(".add-line-button").hide()
//    },
//
//    initializeUI: ()=> $("div.o_portal_wrap .container:first").removeClass('container').addClass('container-fluid'),
//
//    start: function () {
//        this.showHideButton()
//        this.categoryVendors = []
//        this.vendorData = []
//        this.purchaseRecord = parseInt(this.$el.attr('data-id'))
//        this.vendorSelect = this.$el.find('#vendor_select')
//        this.categorySelect = this.$el.find('#product_category')
//
//        this._initializeCategoriesVendors();
//        this._setupValidation();
//
//        return this._super.apply(this, arguments);
//    },
//
//
//    _initializeCategoriesVendors: async function() {
//        this.productList = await rpc("/purchase_order/get_products_list")
//        this.categoryData = await rpc("/web/dataset/call_kw/product.category/search_read", {
//            model: "product.category",
//            method: "search_read",
//            args: [],
//            kwargs: { domain: [['enable_internal_po', '=', true]], fields: ['id','name'] },
//        });
//
//        if(!this.purchaseRecord && this.categoryData.length){
//            this.categoryData.forEach(item => {
//                this.categorySelect.append($('<option></option>').val(item.id).text(item.name))
//            })
//
//        }
//    },
//
//    _onCategoryChange: function(ev){
//        const productCategory = parseInt(ev.target.value);
//
//        this.categoryVendors = this.productList.filter(
//            vendor => vendor.product_ids.some(product => product.category_id === productCategory)
//        ).map(vendor => ({partner_id: vendor.partner_id, partner_name:vendor.partner_name}) );
//
//        this.populateVendors()
//    },
//
//    populateVendors: function (){
//        this.vendorSelect.find('option').not(':first').remove()
//        this.categoryVendors.forEach(item => {
//            this.vendorSelect.append($('<option></option>').val(item.partner_id).text(item.partner_name))
//        });
//        this.refreshOrderLines()
//    },
//
//    _setupValidation: function() {
//        if($.validator) {
//            $("#purchase_order_form").validate({
//                errorElement: "span",
//                errorPlacement: function(error, element) {
//                },
//                highlight: function(element) {
//                    $(element).css({'background': '#ffdddd','z-index':'999'});
//                },
//                unhighlight: function(element) {
//                    $(element).css('background', '#ffffff');
//                },
//            });
//        }
//    },
//
//
//    _onVendorChange: function(ev) {
//        const selectedVendor = ev.currentTarget.value;
//        this.vendorData = this.productList.find(obj => obj.partner_id === parseInt(selectedVendor)) || {}
//        this.refreshOrderLines()
//    },
//
//    refreshOrderLines: function(){
//        this.$el.find('.order-line').not(':first').remove();
//        var $productSelectElement = this.$el.find('.order-line').first().find('select');
//        $productSelectElement.find('option').not(':first').remove()
//
//        if(Object.keys(this.vendorData).length){
//            this.vendorData.product_ids.forEach(item => {
//                $productSelectElement.append($('<option></option>').val(item.product_id).text(item.name))
//            })
//        }
//        this.showHideButton();
//    },
//
//    _onProductChange: function(ev) {
//        const $productSelect = $(ev.currentTarget);
//        const selectedProductId = parseInt($productSelect.val());
//
//        const $uomElement = $productSelect.closest('.order-line').find("[name^='uom_id_']");
//        const uomName = this.vendorData?.product_ids?.find(p => p.product_id === selectedProductId)?.uom_name || '';
//        $uomElement.text(uomName);
//    },
//
//
//    _onAddLineClick: function(ev) {
//        var self = this;
//        var newElement = self.$el.find("#order_line_body .order-line:first").clone();
//        self.current_id += 1;
//        newElement.find("input,select").val("");
//        newElement.find("span").text("");
//
//        newElement.find('input,select,span').each(function() {
//            var name = $(this).attr('name');
//            if(name) {
//                var newName = name.replace(/\d+/, self.current_id);
//                $(this).attr('name', newName);
//            }
//        });
//
//        self.$el.find("#order_line_body").append(newElement);
//        self.showHideButton();
//    },
//
//    _onRemoveLineClick: function(ev) {
//        $(ev.currentTarget).closest(".order-line").remove();
//        this.showHideButton();
//    },
//
//    _onSendForApprovalClick: function (ev) {
//        if(this.purchaseRecord) {
//            browser.location.href = `/purchase_order/${this.purchaseRecord}/send_for_approval`;
//            $("#send-for-approval-btn").hide();
//        }
//    },
//
//});
//
//export default publicWidget.registry.PurchaseOrderWidget;
//
