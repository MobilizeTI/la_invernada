
odoo.define('field_image_preview.image_widget_extend', function (require) {
"use strict";

    var base_f = require('web.basic_fields')
	var imageWidget = base_f.FieldBinaryImage
    var DocumentViewer = require('mail.DocumentViewer');

imageWidget.include({

    _render: function () {
        this._super.apply(this, arguments);
        var self = this;
        this.$("img").click(function(e) {
            var name_field = self.name;
            if (name_field == "image_medium" || name_field == "image_small"){
            	name_field = "image";	
            }
            var attachments = [];
            var main_id = self.model + "/" + JSON.stringify(self.res_id) + "/" + name_field;
            var source_id = "";
            var fields_attachments = [];
            if (self.nodeOptions.fields_to_preview){
            	fields_attachments = fields_attachments.concat(self.nodeOptions.fields_to_preview);
            }
            if (!_.contains(fields_attachments, name_field)) {
            	fields_attachments.push(name_field);
            }
            _.each(fields_attachments, function (field_name) {
            	source_id = self.model + "/" + JSON.stringify(self.res_id) + "/" + field_name;
                attachments.push({
                    "filename": self.recordData.display_name ,
                    "id": source_id,
                    "is_main": true,
                    "mimetype": "image/jpeg",
                    "name": self.recordData.display_name + " " + self.value,
                    "type": "image",
                });
            });
            var attachmentViewer = new DocumentViewer(self, attachments, main_id);
            attachmentViewer.appendTo($('body'));
        });
    },
});
});

