frappe.ui.form.on('Employee', {
    setup: function(frm) {
        // Whenever the Employee form is set up, apply a filter on the custom_state field
        frm.set_query('custom_state', function() {
            return {
                filters: [
                    ['State', 'docstatus', '=', 1]
                ]
            }
        });
    }
});
