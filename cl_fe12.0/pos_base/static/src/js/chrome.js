odoo.define('pos_base.chrome', function (require) {
    "use strict";
    
    var ServiceProviderMixin = require('web.ServiceProviderMixin');
    
    var chrome = require('point_of_sale.chrome');

    var StatusbarInfoWidget = chrome.StatusWidget.extend({
        template: 'StatusbarInfoWidget',
        init: function(parent, options) {
            this._super(parent, options);
            this.show = true;
        },
        start: function () {
            $('.show_hide_buttons').click(_.bind(this.show_hide_buttons, this));
            this.pos.bind('update:count_item', this.compute_count_item, this);
            this.pos.bind('change:selectedOrder', this.compute_count_item, this);
        },
        show_hide_buttons: function () {
        	var self = this;
        	if (self.show) {
                $('.buttons_pane').animate({width: 0}, 'slow');
                $('.leftpane').animate({left: 0}, 'slow');
                $('.rightpane').animate({left: 440}, 'slow');
                $('.show_hide_buttons').addClass('highlight');
                // $('.pads').slideUp(1000); // hide payment, select customer and numpad layout
                self.show = false;
            } else {
                $('.buttons_pane').animate({width: 220}, 'slow');
                $('.leftpane').animate({left: 220}, 'slow');
                $('.rightpane').animate({left: 660}, 'slow');
                $('.show_hide_buttons').removeClass('highlight');
                // $('.pads').slideDown(1000); // show payment, select customer and numpad layout
                self.show = true;
            }
        },
        set_count_item: function (count, qty_total) {
            this.$('.count_item').html(count);
            this.$('.count_qty').html(qty_total);
        },
        compute_count_item: function () {
        	var self = this;
        	var selectedOrder = self.pos.get_order();
        	var qty_total = 0;
            if (selectedOrder) {
            	_.each(selectedOrder.orderlines.models, function (line) {
            		qty_total += line.get_quantity();
                });
                self.set_count_item(selectedOrder.orderlines.length, qty_total);
            } else {
                self.set_count_item(0, qty_total);
            }
        }
    });
    
    chrome.Chrome.include({
    	init: function() { 
    		var self = this;
    		this._super.apply(this, arguments);
    		if (this.pos.is_mobile){
    			return;
    		}
    		this.ready.done(function(){
    			// cuando no hay botones, ocultar la barra para que no ocupe espacio innecesario
    			if (_.isEmpty(self.gui.screen_instances.products.action_buttons)){
    				self.widget.statusbar_info_widget.show_hide_buttons();
    			}
    		});
    	},
    	pos_notify: function (title, message, sticky, className) {
    		ServiceProviderMixin.services.notification.notify({title: title, message: message, sticky: sticky, className: className})
	    },
	    pos_warning: function (title, message, sticky, className) {
	    	ServiceProviderMixin.services.notification.notify({type: 'warning', title: title, message: message, sticky: sticky, className: className})
	    },
    	build_widgets: function () {
    		if (this.pos.is_mobile){
    			return this._super();
    		}
            this.widgets.push({
            	'name': 'statusbar_info_widget',
            	'widget': StatusbarInfoWidget,
            	'append': '.pos-branding',
            });
            this._super();
        },
        renderElement:function () {
            var self = this;
            if(self.pos.config){
                if(self.pos.config.image_url){
                    this.pos_config_image_url = self.pos.config.image_url;
                }
            }
            this._super(this);
        }
    });
    
    return {
    	StatusbarInfoWidget: StatusbarInfoWidget,
    };
});