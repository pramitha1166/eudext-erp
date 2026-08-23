frappe.ui.form.on("LK Bulk Payment Batch", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status !== "File Generated") {
			frm.add_custom_button(__("Generate File"), () => {
				frappe.call({
					method: "generate_file",
					doc: frm.doc,
					freeze: true,
					freeze_message: __("Generating bank payment file..."),
					callback: (r) => {
						if (!r.exc) {
							frm.reload_doc();
							frappe.show_alert({
								message: __("Bank payment file generated"),
								indicator: "green",
							});
						}
					},
				});
			}).addClass("btn-primary");
		}

		if (frm.doc.status === "File Generated" && frm.doc.generated_file) {
			frm.add_custom_button(__("Download File"), () => {
				window.open(frm.doc.generated_file);
			});
		}
	},
});
