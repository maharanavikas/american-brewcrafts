/** @odoo-module **/

/** abcl_sale/static/src/js/dispatch_checklist.js */
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

    start: function () {
        if (typeof this._super === "function") this._super.apply(this, arguments);
        this._initValidation();
        this._initHelpers();
        this._initDatePicker();
        this._initVehicleToggles();
        // this._wireSignatureSuccessHooks();
        this._injectStatusCheckAllButton();
        this._bindCheckAllHandler();
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
        const enterDiv        = this.$el.find("#enter_vehicle_details");
        const vehicleNumber   = this.$el.find("#vehicle_number_div");

        selectDiv.hide();
        enterDiv.hide();
        vehicleNumber.hide();

        vehicleType.on("change", function () {
            const val = $(this).val();
            if (val === "internal") {
                selectDiv.show();
                vehicleNumber.show();
                enterDiv.hide();
            } else if (val === "external") {
                enterDiv.show();
                selectDiv.hide().val("");
                vehicleNumber.hide().val("");
            } else {
                selectDiv.val("").hide();
                enterDiv.val("").hide();
                vehicleNumber.val("").hide();
            }
        });

        const vehicleSelect      = this.$el.find("#select_vehicle_name");
        const vehicleNumberInput = this.$el.find("#vehicle_number_div input");
        vehicleNumberInput.val("");

        vehicleSelect.on("change", () => {
            const $opt   = vehicleSelect.find("option:selected");
            const number = $opt.data("number") || "";
            vehicleNumberInput.val(number).trigger("change");
            vehicleNumberInput.valid && $(vehicleNumberInput).valid();
        });
    },

    _initValidation() {
        // class rules
        $.validator.addClassRules({
            checkrequired: { required: true },
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
                    $el.css("background", "#a70808ff");
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

            // Re-validate if needed
            $boxes.each(function () {
                const $cb = $(this);
                if (typeof $cb.valid === "function") $cb.valid();
            });
        });
    },
});

export default publicWidget.registry.DispatchChecklistWidget;