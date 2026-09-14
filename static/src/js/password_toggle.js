/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class PasswordToggleField extends Component {

    static template = "asset_management.PasswordToggleField";

    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.state = useState({
            showPassword: false,
        });
    }

    togglePassword() {
        this.state.showPassword = !this.state.showPassword;
    }

    get inputType() {
        return this.state.showPassword ? "text" : "password";
    }

    get iconClass() {
        return this.state.showPassword
            ? "fa fa-eye-slash"
            : "fa fa-eye";
    }
}

export const passwordToggleField = {
    component: PasswordToggleField,
    supportedTypes: ["char"],
};

registry.category("fields").add(
    "password_toggle",
    passwordToggleField
);