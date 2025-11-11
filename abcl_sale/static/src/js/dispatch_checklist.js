/** @odoo-module **/
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
        // await loadJS("/abcl_sale/static/src/js/multi-select-tag.js");
        return true;
    },
    rpc: rpc,

    start: function () {
        if (typeof this._super === "function") this._super.apply(this, arguments);
        // this._initMultiSelect();
        this._initValidation();
        this._initHelpers();
        this._initDatePicker();
        this._initVehicleToggles();
        this._injectStatusCheckAllButton();
        this._bindCheckAllHandler();
        this._bindModalCloseEvent();
        this._restoreFormDataFromLocalStorage();
        // this._restoreMultiSelectFromSelect();
        this._checkAccessTokenChange();
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
        const enterVehicleNum = this.$el.find("#enter_vehicle_details");
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

    // Get a unique key for this specific form instance
    _getFormStorageKey() {
        return `dispatch_checklist/${this.access_token}`;
    },

    // Save all current form data to localStorage
    _saveFormDataToLocalStorage() {
        const data = {};
        this.$el.find('input, select, textarea').each(function () {
            const $field = $(this);
            const name = $field.attr('name');
            if (!name) return;

            if ($field.attr('type') === 'checkbox') {
                data[name] = $field.prop('checked');
            } else if ($field.attr('type') === 'file') {
                // Binary field - skip or handle separately if needed
            } else {
                data[name] = $field.val();
            }
        });

        const key = this._getFormStorageKey();
        localStorage.setItem(key, JSON.stringify(data));
    },

    // Restore previously saved form data
    _restoreFormDataFromLocalStorage() {
        const key = this._getFormStorageKey();
        const json = localStorage.getItem(key);
        if (!json) return;

        const data = JSON.parse(json);
        this.$el.find('input, select, textarea').each(function () {
            const $field = $(this);
            const name = $field.attr('name');
            if (!name || !(name in data)) return;

            if ($field.attr('type') === 'checkbox') {
                $field.prop('checked', !!data[name]);
            } else {
                $field.val(data[name]);
            }
        });
    },

    // _restoreMultiSelectFromSelect: function () {
    //     // After localStorage restore the native <select> already has the correct
    //     this.$el.find('select[multiple]').each((i, el) => {
    //         const $select = $(el);
    //         if ($select.data('multiselect-initialized')) {
    //             // Force a refresh of the tags
    //             const current = $select.val() || [];
    //             const instance = $select[0].multiselectInstance; // we store it below
    //             if (instance && typeof instance.modifyDomain === 'function') {
    //                 // Build a domain that contains *all* options with the correct .selected
    //                 const allOpts = Array.from(el.options).map(o => ({
    //                     value: o.value,
    //                     label: o.textContent.trim(),
    //                     selected: current.includes(o.value),
    //                 }));
    //                 instance.modifyDomain(allOpts);
    //             }
    //         }
    //     });
    // },

    // _initMultiSelect: function () {
    //     // Wait a tick – Odoo’s assets are loaded asynchronously in willStart()
    //     this.$el.find('select[multiple]').each((i, el) => {
    //         const $select = $(el);
    //         // Prevent double-initialisation (e.g. when the widget is re-started)
    //         if ($select.data('multiselect-initialized')) return;
    //         const opts = {
    //             rounded: true,
    //             shadow: true,
    //             placeholder: 'Search…',
    //             // optional custom colours – keep the ones you already defined
    //             tagColor: {
    //                 textColor: '#f0f0f1ff',
    //                 borderColor: '#6930C3',
    //                 bgColor: '#6930C3',
    //             },
    //             onChange: (selected) => {
    //                 const values = selected.map(o => o.value);
    //                 $select.val(values).trigger('change');
    //             },
    //         };
    //         new MultiSelectTag(el.id, opts);
    //         $select.data('multiselect-initialized', true);
    //     });
    // },

    // Clear localStorage after form submission (optional)
    _checkAccessTokenChange() {
        const currentToken = this.access_token;
        const lastToken = localStorage.getItem('dispatch_form_last_token');

        if (lastToken && lastToken !== currentToken) {
            // The user switched to a new form -> clear old data
            const oldKey = `dispatch_checklist/${lastToken}`;
            localStorage.removeItem(oldKey);
        }

        // Update last token reference
        localStorage.setItem('dispatch_form_last_token', currentToken);
    },

    // Bind modal close event and preserve form data
    _bindModalCloseEvent() {
        const modalAccountant = $('#modal_accountant');
        const modalDispatchInCharge = $('#modal_dispatch');

        // Use arrow function so `this` stays bound correctly
        const handleModalClose = () => {
            this._saveFormDataToLocalStorage();
            location.reload(); // Reload the page to reflect new changes
        };

        modalAccountant.on('hidden.bs.modal', handleModalClose);
        modalDispatchInCharge.on('hidden.bs.modal', handleModalClose);
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
                // Check if dispatch_signature is missing or false
                const hasDispatchSignature = $("#dispatch_signature_container img").length > 0;
                const isInchargeSign = $("#frm_dispatch_checklist").data("is_incharge_sign");

                // Check if accountant_signature is missing or false
                const hasAccountantSignature = $("#accountant_signature_container img").length > 0;
                const isAccountantSign =$("#frm_dispatch_checklist").data("is_accountant_sign");

                if (isInchargeSign && !hasDispatchSignature) {
                    // Show an error popup if the conditions are not met
                    swal({
                        title: "Signature is missing",
                        text: "You must provide dispatch inchange signature.",
                        icon: "error",
                        button: "OK",
                    });
                    return false;
                }
                if (isAccountantSign && !hasAccountantSignature) {
                    // Show an error popup if the conditions are not met
                    swal({
                        title: "Signature is missing",
                        text: "You must provide accountant signature.",
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

    _bindCheckAllHandler() {
        // Delegate: listen for clicks on any .check-all-btn inside the widget
        this.$el.on("click", ".check-all-btn", function () {
            const $card = $(this).closest(".card");
            const $boxes = $card.find('.checkrequired[type="checkbox"]');

            $boxes.prop("checked", true).trigger("change");
            $boxes.each(function () {
                const $cb = $(this);
                if (typeof $cb.valid === "function") $cb.valid();
            });
        });
    },
});