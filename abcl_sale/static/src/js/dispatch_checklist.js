/** @odoo-module **/

/** abcl_sale/static/src/js/dispatch_checklist.js */
import { Component } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { loadJS } from "@web/core/assets";
import publicWidget from "@web/legacy/js/public/public_widget";
import { deserializeDate, parseDate } from "@web/core/l10n/dates";
const { DateTime } = window.luxon;

publicWidget.registry.DispatchChecklistWidget = publicWidget.Widget.extend({
    selector: "#frm_dispatch_checklist",
    cssLibs: [
        "/abcl_sale/static/src/css/multi-select-tag.css",
    ],

    willStart: async function () {
        await loadJS("/abcl_sale/static/src/js/jquery.validate.min.js");
        return true;
    },
    rpc: rpc,

    start: function () {
        if (typeof this._super === "function") this._super.apply(this, arguments);
        this._initValidation();
        this._initHelpers();
        this._initDatePicker();
        this._initVehicleToggles();
        // this._wireSignatureSuccessHooks();
        this._injectStatusCheckAllButton();
        this._bindCheckAllHandler();
        this._bindModalCloseEvent();
//        this._bindModalEvents();
//        this._manageFormState();
        this._bindFormFieldValidation();
    },

    // ---------- helpers ----------
    _initHelpers() {
        this.$el.find("input[type=text]").on("blur", function () {
            $(this).val($(this).val().trim().replace(/\s+/g, " "));
        });
    },

    _initVehicleToggles() {
        const vehicleType     = this.$el.find("#vehicle_type");
        const selectDiv       = this.$el.find("#select_vehicle_div");
        const enterDiv        = this.$el.find("#enter_vehicle_details_div");
        const enterVehicleNum        = this.$el.find("#enter_vehicle_details");
        const vehicleNumber   = this.$el.find("#vehicle_number_div");
        const vehicleSelect   = this.$el.find("#select_vehicle_name");
        const vehicleNumberInput = this.$el.find("#vehicle_number_div input");

        // Hide all by default
        selectDiv.hide();
        enterDiv.hide();
        vehicleNumber.hide();

        // Function to toggle based on current value
        const toggleSections = (val) => {
            if (val === "internal") {
                selectDiv.show();
                vehicleSelect.addClass('clsrequired');
                vehicleNumber.show();
                enterDiv.hide();
                enterVehicleNum.hide();
            } else if (val === "external") {
                enterDiv.show();
                enterVehicleNum.show();
                enterVehicleNum.addClass('clsrequired');
                vehicleSelect.removeClass('clsrequired');
                selectDiv.hide();
                vehicleNumber.hide();
            } else {
                selectDiv.hide();
                enterDiv.hide();
                vehicleNumber.hide();
                enterVehicleNum.hide();
                enterDiv.removeClass('clsrequired');
                vehicleSelect.removeClass('clsrequired');
                vehicleType.addClass('clsrequired');
            }
        };

        // --- Run toggle once on load (important!) ---
        const initialVal = vehicleType.val();
        toggleSections(initialVal);

        // --- On change of vehicle type ---
        vehicleType.on("change", function () {
            const val = $(this).val();
            toggleSections(val);
        });

        // --- Vehicle selection handler ---
        vehicleSelect.on("change", () => {
            const $opt = vehicleSelect.find("option:selected");
            const number = $opt.data("number") || "";
            vehicleNumberInput.val(number).trigger("change");
            vehicleNumberInput.valid && $(vehicleNumberInput).valid();
        });
    },
//    _bindModalCloseEvent() {
        // Bind for Accountant Modal Close
//        const modalAccountant = $('#modal_accountant');
//        modalAccountant.on('hidden.bs.modal', function () {
//            location.reload(); // Reload the page after modal close
//        });

        // Bind for Dispatch in Charge Modal Close
//        const modalDispatchInCharge = $('#modal_dispatch');
//        modalDispatchInCharge.on('hidden.bs.modal', function () {
//            location.reload(); // Reload the page after modal close
//        });
//    },
////////
    _bindModalCloseEvent() {
        const modalDispatch = $('#modal_dispatch');
        modalDispatch.on('hidden.bs.modal', () => {
//            this._manageFormState();
            location.reload();

        });
        const modalAccountant = $('#modal_accountant');
        modalAccountant.on('hidden.bs.modal', () => {
            console.log('Accountant modal closed');
//            this._manageFormState();

            setTimeout(() => {
                const $form = $('#frm_dispatch_checklist');
                console.log(`Form detected: ${$form.length ? 'Yes' : 'No'}`);

                if (!$form.length) return console.error('Form #frm_dispatch_checklist not found');

                const validator = $form.validate();
                if (!validator || typeof validator.settings.submitHandler !== 'function') {
                    return console.error('Invalid validator or missing submitHandler', validator);
                }

                try {
                    validator.settings.submitHandler.call(this, $form[0]);
                    console.log('submitHandler executed successfully');
                } catch (err) {
                    console.error('Error executing submitHandler:', err);
                }
            }, 10); // Allow brief DOM update
        });

    },
//     _bindModalCloseEvent() {
//        const modalDispatch = $('#modal_dispatch');
//        const modalAccountant = $('#modal_accountant');
//
//        // Dispatch modal close handler
//        modalDispatch.on('hidden.bs.modal', async () => {
//            console.log("Dispatch modal closed");
//            try {
//                await this._refreshSignatures();
//                console.log("Signatures refreshed successfully after dispatch modal close");
//            } catch (err) {
//                console.error("Error refreshing signatures:", err);
//            }
//        });
//
//        // Accountant modal close handler
//        modalAccountant.on('hidden.bs.modal', async () => {
//            console.log("Accountant modal closed");
//            try {
//                await this._refreshSignatures();
//                console.log("Signatures refreshed successfully after accountant modal close");
//            } catch (err) {
//                console.error("Error refreshing signatures:", err);
//            }
//        });
//    },
//    _bindModalEvents() {
//    // Handle signature form submission
//        $('#modal_dispatch form, #modal_accountant form').on('submit', async (ev) => {
//            ev.preventDefault();
//            const $form = $(ev.currentTarget);
//            const role = $form.closest('.modal').attr('id') === 'modal_dispatch' ? 'dispatch' : 'accountant';
//            const recordId = this.$el.data('record-id');
//            const signature = $form.find('input[name="signature"]').val(); // Base64-encoded signature
//            const signedBy = $form.find('input[name="signer_name"]').val();
//
//            if (!recordId) {
//                console.error("Missing record ID for signature submission");
//                return;
//            }
//
//            try {
//                await this.rpc({
//                    model: 'stock.picking',
//                    method: 'write',
//                    args: [
//                        [parseInt(recordId)],
//                        {
//                            [`${role}_signature`]: signature.split(',')[1], // Remove data URI prefix
//                            [`${role}_signed_by`]: signedBy,
//                            [`is_${role}_sign`]: true,
//                        },
//                    ],
//                });
//
//                console.log(`${role} signature saved successfully`);
//                $form.closest('.modal').modal('hide'); // Close modal
//            } catch (error) {
//                console.error(`Error saving ${role} signature:`, error);
//            }
//        });
//    },
//
//
//    async _refreshSignatures() {
//        const recordId = this.$el.data('record-id');
//        console.log("Record ID:", recordId); // Debug
//        if (!recordId) {
//            console.error("Missing data-record-id on form element");
//            return;
//        }
//
//        try {
//            const result = await this.rpc({
//                model: 'stock.picking',
//                method: 'read',
//                args: [[parseInt(recordId)], ['dispatch_signature', 'accountant_signature', 'dispatch_signed_by', 'accountant_signed_by']],
//            });
//            console.log("RPC Result:", result); // Debug
//
//            if (result && result.length) {
//                const record = result[0];
//
//                // Update Dispatch Signature
//                const dispatchContainer = $("#dispatch_signature_container");
//                const dispatchContent = $("#dispatch_content");
//                if (record.dispatch_signature) {
//                    dispatchContainer.html(`
//                        <h5>Dispatch In-Charge</h5>
//                        <img src="data:image/png;base64,${record.dispatch_signature}" class="img-fluid" alt="Dispatch Signature" style="max-height: 6rem; max-width: 100%;" />
//                        <p class="mt-2 mb-0">${record.dispatch_signed_by || ''}</p>
//                    `);
//                    dispatchContent.empty(); // Hide "Accept & Sign" button
//                } else {
//                    dispatchContainer.empty();
//                }
//
//                // Update Accountant Signature
//                const accountantContainer = $("#accountant_signature_container");
//                const accountantContent = $("#accountant_content");
//                if (record.accountant_signature) {
//                    accountantContainer.html(`
//                        <h5>Accountant</h5>
//                        <img src="data:image/png;base64,${record.accountant_signature}" class="img-fluid" alt="Accountant Signature" style="max-height: 6rem; max-width: 100%;" />
//                        <p class="mt-2 mb-0">${record.accountant_signed_by || ''}</p>
//                    `);
//                    accountantContent.empty(); // Hide "Accept & Sign" button
//                } else {
//                    accountantContainer.empty();
//                }
//
//                // Update form state
//                this._manageFormState();
//            } else {
//                console.error("No data returned from RPC call");
//            }
//        } catch (error) {
//            console.error("Error fetching signatures:", error.message, error.data, error.stack);
//        }
//    },
//
    _checkSignatures() {
        const hasDispatchSignature = $("#dispatch_signature_container img").length > 0;
        const hasAccountantSignature = $("#accountant_signature_container img").length > 0;
//        return hasDispatchSignature && hasAccountantSignature;
        return hasDispatchSignature;
    },

//    _manageFormState() {
//        const formFields = this.$el.find('input, select, textarea').not('[name="csrf_token"]').not('#modal_dispatch input, #modal_accountant input');
//        const signatureButtons = this.$el.find('#dispatch_content a, #accountant_content a');
//
//        if (this._checkSignatures()) {
//            formFields.prop('disabled', false);
//            formFields.css('background-color', '#ffffff');
//            signatureButtons.prop('disabled', true);
//        } else {
//            formFields.prop('disabled', true);
//            formFields.css('background-color', '#f0f0f0');
//            signatureButtons.prop('disabled', false);
//        }
//    },

    _bindFormFieldValidation() {
        const formFields = $('#frm_dispatch_checklist').find('input, select, textarea').not('[name="csrf_token"]').not('#modal_dispatch input, #modal_accountant input');
        console.log('Binding validation to form fields:', formFields.length);
        formFields.on('focus click input', (event) => {
            if (!this._checkSignatures()) {
                console.log('Dispatch signature missing, showing validation message for field:', event.target);
                swal({
                    title: "Signature Required",
                    text: "Please sign before entering the details.",
                    icon: "warning",
                    button: "OK",
                });
                $(event.target).blur();
            }
        });
    },

    _checkDispatchSignature() {
        const dispatchSignature = $('#dispatch_signature').val(); // Assuming you have an input with ID dispatch_signature
        return dispatchSignature && dispatchSignature !== "";
    },

    // Custom validation method to check if is_incharge_sign is true
    _checkInchargeSignature() {
        const isInchargeSign = $('#is_incharge_sign').prop('checked'); // Assuming is_incharge_sign is a checkbox
        return isInchargeSign;
    },

    _initValidation() {
        // class rules
        $.validator.addClassRules({
            checkrequired: { required: true },
            clsrequired: {required : true}
        });

        // custom date rule: not in the past
        $.validator.addMethod(
            "notPastDate",
            function (value) {
                if (!value) return false;
                let dt = parseDate(value);
                if (!dt || !dt.isValid) dt = DateTime.fromISO(value, { zone: "local" });
                if (!dt || !dt.isValid) return false;
                return dt.startOf("day") >= DateTime.local().startOf("day");
            },
            "Please choose today or a future date."
        );

        // main validator
        $("#frm_dispatch_checklist").validate({
            ignore: ":hidden",
            rules: {
                dispatch_date: { required: true, notPastDate: true },
                dispatch_brand: { required: true },
                quality: { required: true },
                depot: { required: true },
            },
            errorElement: "span",
            highlight: function (el) {
                const $el = $(el);
                if ($el.is(":checkbox") || $el.is(":radio")) {
                    $el.closest(".form-check").addClass("has-error");
                    $el.addClass("is-invalid");
                } else {
                    $el.css("background", "#f4c3c3");
                }
            },
            unhighlight: function (el) {
                const $el = $(el);
                if ($el.is(":checkbox") || $el.is(":radio")) {
                    $el.closest(".form-check").removeClass("has-error");
                    $el.removeClass("is-invalid");
                } else {
                    $el.css("background", "#ffffff");
                }
            },
            errorPlacement: function (error, element) {
                if (element.is(":checkbox") || element.is(":radio")) {
                    error.appendTo(element.closest(".form-check"));
                } else {
                    error.insertAfter(element);
                }
            },
            submitHandler: function (el) {
                // Check if dispatch_signature is missing or is_incharge_sign is false
                const isInchargeSign = $("#is_incharge_sign").val();
                console.log("isInchargeSign --->", isInchargeSign);
                const hasDispatchSignature = $("#dispatch_signature_container img").length > 0;

                // Check if accountant_signature is missing or is_incharge_sign is false
                const isAccountantSign = $("#is_accountant_sign").val();
                console.log("isAccountantSign --->", isAccountantSign);
                const hasAccountantSignature = $("#accountant_signature_container img").length > 0;

                console.log("Dispatch Signature Present:", hasDispatchSignature);
                console.log("Accountant Signature Present:", hasAccountantSignature);

//                if (!isInchargeSign || !isAccountantSign) {
//                if (!hasDispatchSignature || !hasAccountantSignature) {
                if (!hasDispatchSignature) {
                    // Show an error popup if the conditions are not met
                    swal({
                        title: "Error",
                        text: "You must provide a signature.",
                        icon: "error",
                        button: "OK",
                    });
                    return false;
                }
                // If everything is valid, proceed with form submission
                swal({
                    title: "Are you sure?",
                    text: "Do you want to submit the form?",
                    icon: "warning",
                    buttons: true,
                    dangerMode: true,
                    closeOnClickOutside: false,
                }).then((willSubmit) => {
                    if (willSubmit) el.submit();
                });
            },

        });
    },


    _initDatePicker() {
        const field = this.el.querySelector("#dispatch_date");
        if (!field) return;

        const todayISO = new Date().toISOString().split("T")[0];
        const parsed = parseDate(field.value);
        const defaultValue = parsed && parsed.isValid ? parsed : deserializeDate(todayISO);

        this.call("datetime_picker", "create", {
            target: field,
            onChange: this._onDateChange.bind(this, field),
            pickerProps: {
                type: "date",
                minDate: deserializeDate(todayISO), // only today+future
                value: defaultValue,
            },
        }).enable();

        field.value = defaultValue.toFormat("yyyy-LL-dd");
        $(field).valid();
    },

    _onDateChange(field, newDate) {
        const todayISO = new Date().toISOString().split("T")[0];
        if (!newDate || !newDate.isValid) {
            field.value = "";
        } else {
            const pickedISO = newDate.toFormat("yyyy-LL-dd");
            field.value = pickedISO >= todayISO ? pickedISO : todayISO;
        }
        $(field).valid();
    },

    validate: function () {
        $("#frm_dispatch_checklist").validate({
            ignore: "",
            rules: {},
            submitHandler: (frm) => {
                if (!this._checkSignatures()) return;

                swal({
                    title: "Are you sure?",
                    text: "Do you want to submit the form?",
                    icon: "warning",
                    buttons: true,
                    dangerMode: true,
                    closeOnClickOutside: false,
                }).then((willSubmit) => {
                    if (willSubmit) frm.submit();
                });
            },
            errorElement: "div",
            highlight: function (element) { $(element).css("background", "#ffdddd"); },
            unhighlight: function (element) { $(element).css("background", "#ffffff"); },
        });
    },

    _injectStatusCheckAllButton() {
        // For every card-header inside the widget
        this.$el.find(".card").each(function () {
            const $card = $(this);
            const $statusCol = $card.find(".card-header .row > div")
                .filter(function () {
                    return $(this).text().trim().toLowerCase() === "status";
                })
                .first();

            if (!$statusCol.length) return;

            // Avoid duplicates
            if ($statusCol.find(".check-all-btn").length) return;

            $statusCol.addClass("d-flex align-items-center");
            $statusCol.append(
                `<button type="button" 
                        class="btn btn-sm btn-outline-primary ms-2 check-all-btn">
                    Check All
                </button>`
            );
        });
    },

//    _bindCheckAllHandler() {
//        // Delegate: listen for clicks on any .check-all-btn inside the widget
//        this.$el.on("click", ".check-all-btn", function () {
//            const $card = $(this).closest(".card");
//            const $boxes = $card.find('.checkrequired[type="checkbox"]');
//
//            $boxes.prop("checked", true).trigger("change");
//
//            // Re-validate if needed
//            $boxes.each(function () {
//                const $cb = $(this);
//                if (typeof $cb.valid === "function") $cb.valid();
//            });
//        });
//    },
    _bindCheckAllHandler() {
        $('#frm_dispatch_checklist').on("click", ".check-all-btn", (event) => {
            if (!this._checkSignatures()) {
                console.log('Dispatch signature missing, showing validation message for Check All button');
                swal({
                    title: "Signature Required",
                    text: "Please sign before entering the details.",
                    icon: "warning",
                    button: "OK",
                });
                return;
            }
            const $card = $(event.currentTarget).closest(".card");
            const $boxes = $card.find('.checkrequired[type="checkbox"]');

            $boxes.prop("checked", true).trigger("change");
            $boxes.each(function () {
                const $cb = $(this);
                $cb[0].checked = true;
                if (typeof $cb.valid === "function") $cb.valid();
            });
        });
    },
});

export default publicWidget.registry.DispatchChecklistWidget;