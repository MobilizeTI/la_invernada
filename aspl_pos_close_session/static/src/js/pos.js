odoo.define('aspl_pos_close_session.pos', function (require) {
"use strict";

var models = require('point_of_sale.models');
var DB = require('point_of_sale.DB');
var chrome = require('point_of_sale.chrome');
var screens = require('point_of_sale.screens');
var PopupWidget = require('point_of_sale.popups');
var gui = require('point_of_sale.gui');
var format = require('web.field_utils').format;
var core = require('web.core');
var rpc = require('web.rpc');
var utils = require('web.utils');
require('pos_base.popup');

var lpad = utils.lpad;
var _t = core._t;
var QWeb = core.qweb;
var framework = require('web.framework');

models.load_fields("pos.session", ['opening_balance']);
models.load_fields("res.users", ['login_with_pos_screen', 'has_group_see_cash_values']);

models.load_models([{
    model:  'account.cashbox.line',
    domain: function(self){ return [['default_pos_id','=',self.config.id]]; },
    fields: ['coin_value', 'number'],
    loaded: function(self, default_cashbox_lines){
			self.default_cashbox_lines = default_cashbox_lines;
		}
	}
]);

chrome.HeaderButtonWidget.include({
    renderElement: function(){
        var self = this;
        this._super();
        if(this.action){
            this.$el.click(function(){
                var draft_orders = _.filter(self.pos.db.get_unpaid_orders(), function(order) {
                	return order.pos_session_id === self.pos.pos_session.id && order.lines.length > 0;
                }).length;
                if (draft_orders){
            		self.gui.show_popup('confirm', {
                        'title': _t('Pedidos no Validados'),
                        'body':  _t(['Hay Pedidos en los que aun no ha registrado pagos,',
                                     'si cierra session se podrian perder, se recomienda pagarlos antes de cerrar session.',
                                     'De todas maneras puede cerrar el POS, pero procure no cerrar session antes de validar esos pedidos.',
                                     'Desea continuar?',
                                     ].join(' ')),
                        'confirm': function() {
                        	self.gui.show_popup('confirm_close_session_wizard');
                        },
                    });
            		return;
            	}else{
            		self.gui.show_popup('confirm_close_session_wizard');
            	}
            });
        }
    },
});

chrome.Chrome.include({
      build_widgets:function(){
            var self = this;
            this._super(arguments);
            if(self.pos.pos_session.opening_balance){
                self.gui.show_screen('openingbalancescreen');
            } else{
                self.gui.show_screen('products');
            }
      },
 });

var ConfirmCloseSessionPopupWizard = PopupWidget.extend({
    template: 'ConfirmCloseSessionPopupWizard',
    show: function(options){
        options = options || {};
        this._super(options);
        this.statement_id = options.statement_id;
        var self = this;
        $("#close_session").click(function(){
        	var pending = self.pos.db.get_orders().length;
        	self.pos.push_order().always(function() {
                var pending = self.pos.db.get_orders().length;
                if (pending) {
                    var reason = self.pos.get('failed') ? 
                    			'errores de configuracion' : 
                                'problemas con el internet';
                    self.gui.show_popup('error',{
                    	'title': _t('Offline Orders'),
                    	'body':  _t(['Algunos pedidos no se pudieron enviar al servidor',
	                            'debido a ' + reason + '.',
	                            'Puede cerrar el POS, pero no cierre session hasta que el problema se haya solucionado',
	                            ].join(' ')),
    	            });
                    return false;
                }else{
                	self.button_close_session();
                }
            });
        });
        $("#cash_deposit").click(function(){
        	if(self.pos.config.cash_control){
                self.gui.show_popup('create_deposit_popup',{
                    title: _t('Crear Deposito de Efectivo'),
                });
            }
        });
    },
    button_close_session: function(){
    	var self = this;
    	if(self.pos.config.cash_control){
            self.gui.show_popup('cash_control',{
                title: _t('Closing Cash Control'),
                statement_id:self.statement_id,
            });
        } else{
            var params = {
                model: 'pos.session',
                method: 'custom_close_pos_session',
                args:[self.pos.pos_session.id]
            }
            framework.blockUI();
            rpc.query(params).then(function(res){
                if(res){
                    if(self.pos.config.z_report_pdf){
                        var pos_session_id = [self.pos.pos_session.id];
                        self.pos.chrome.do_action('aspl_pos_close_session.pos_z_report',{additional_context:{
                           active_ids:pos_session_id,
                        }});
                    }
                    if(self.pos.config.iface_print_via_proxy){
                        var pos_session_id = [self.pos.pos_session.id];
                        var report_name = "aspl_pos_close_session.pos_z_thermal_report_template";
                        var params = {
                            model: 'ir.actions.report',
                            method: 'get_html_report',
                            args: [pos_session_id, report_name],
                        }
                        rpc.query(params, {async: false})
                        .then(function(report_html){
                            if(report_html && report_html[0]){
                                self.pos.proxy.print_receipt(report_html[0]);
                            }
                        });
                    }
                    if(self.pos.config.email_close_session_report){
                        var pos_session_id = self.pos.pos_session.id;
                        var params = {
                            model: 'pos.session',
                            method: 'send_email_z_report',
                            args: [pos_session_id]
                        }
                        rpc.query(params, {async: false})
                        .then(function(res){
                            if(res){}
                        }).fail(function(){
                        	self.pos.chrome.pos_notify("Error de Conexion", "No se puede conectar con el servidor, verifique su conexion a internet");
                        });
                    }
                    setTimeout(function(){
                        var cashier = self.pos.user || false;
                        if(cashier && cashier.login_with_pos_screen){
                            framework.redirect('/web/session/logout');
                        } else{
                            self.pos.gui.close();
                        }
                    }, 5000);
                }
            }).always(function(){
            	self.gui.close_popup();
            	framework.unblockUI();
            });
        }
    },
    click_confirm: function(){
        var self = this;
        var pending = self.pos.db.get_orders().length;
    	self.pos.push_order().always(function() {
            var pending = self.pos.db.get_orders().length;
            if (pending) {
                var reason = self.pos.get('failed') ? 
                             'errores de configuracion' : 
                             'problemas con el internet';  

                self.gui.show_popup('confirm', {
                    'title': _t('Offline Orders'),
                    'body':  _t(['Algunos pedidos no se pudieron enviar al servidor',
                                 'debido a ' + reason + '.',
                                 'Puede salir del POS, pero no cierre session hasta que el problema se haya solucionado.',
                                 'Desea salir del POS?.',
                                 ].join(' ')),
                    'confirm': function() {
                    	if (self.pos.user.login_with_pos_screen){
                        	framework.redirect('/web/session/logout');	
                        }else{
                        	self.gui.close_popup();
                        	return self.pos.gui._close();
                        }
                    },
                });
            }else {
            	if (self.pos.user.login_with_pos_screen){
                	framework.redirect('/web/session/logout');	
                }else{
                	self.gui.close_popup();
                	return self.pos.gui._close();
                }
            }
        });
        
    },
});
gui.define_popup({name:'confirm_close_session_wizard', widget: ConfirmCloseSessionPopupWizard});

var CreateDepositPopupWidget = PopupWidget.extend({
    template: 'CreateDepositPopupWidget',

    show: function(options){
        var self = this;
        if (self.pos.bank_journals === undefined){
        	var params = {
            	model: "pos.deposit",
            	method: "action_get_journal_for_deposit",
            	args: [],
            };
            rpc.query(params, {async: false}).then(function(bank_journals){
            	self.pos.bank_journals = bank_journals;
            }).fail(function(){
            	self.chrome.pos_warning(_t("Depositos"), _t('Connection lost'));
            });
        }
        var res = this._super(options);
        var date = new Date();
    	var new_date = date.getFullYear()+ "/" +(lpad(date.getMonth()+1, 2))+ "/" +date.getDate();
    	self.$('#deposit_date').val(new_date);
    	return res;
    },
    click_confirm: function(){
        var self = this;
        var fields_warnings = self.validate_fields_aditional();
        if (fields_warnings.length > 0){
        	return;
        }
        var deposit_values = self.get_fields_aditional();
        var params = {
        	model: "wizard.pos.deposit",
        	method: "action_deposit_from_pos",
        	args: [self.pos.pos_session.id, deposit_values]
        };
        rpc.query(params).then(function (new_deposit){
        	self.gui.show_popup('url_popup',{
                title: _t('Deposito de Efectivo'),
                description: _t('Aqui esta su Deposito de Efectivo:'),
                name: new_deposit.name,
                url: self.build_url_backend('pos.deposit', new_deposit.id),
            });
        }).fail(function(err, event){
        	event.preventDefault();
            var error_body = _t('Your Internet connection is probably down.');
            if (err.data) {
                var except = err.data;
                error_body = except.arguments && except.arguments[0] || except.message || error_body;
            }
        	self.chrome.pos_warning(_t("Depositos"), error_body);
        });
    },
    renderElement: function() {
        var self = this;
        this._super();
        $("#amount_cash").keypress(function (e) {
            if (e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57) && e.which != 46) {
                return false;
           }
        });
        $('.datetime').datepicker({
        	minDate: 0,
        	dateFormat:'yy/mm/dd',
        });
    },
});
gui.define_popup({name:'create_deposit_popup', widget: CreateDepositPopupWidget});

var CashControlWizardPopup = PopupWidget.extend({
    template : 'CashControlWizardPopup',
    show : function(options) {
        var self = this;
        options = options || {};
        this.title = options.title || ' ';
        this.statement_id = options.statement_id || false;
        var selectedOrder = self.pos.get_order();
        this._super();
        this.renderElement();
        var self = this;
        $(self.$el).keypress(function (e) {
            if (e.which != 8 && e.which != 46 && e.which != 0 && (e.which < 48 || e.which > 57)) {
                return false;
            }
        });
        var session_data = {
            model: 'pos.session',
            method: 'search_read',
            domain: [['id', '=', self.pos.pos_session.id]],
            fields: [
            	'cash_register_balance_start', 
            	'cash_register_total_entry_encoding',
            	'cash_register_balance_end',
            	'cash_register_balance_end_real',
            	'cash_register_difference',
            ]
        }
        rpc.query(session_data, {async: false}).then(function(data){
            if(data){
                 _.each(data, function(value){
                    $("#open_bal").text(self.format_currency(value.cash_register_balance_start));
                    $("#transaction").text(self.format_currency(value.cash_register_total_entry_encoding));
                    $("#theo_close_bal").text(self.format_currency(value.cash_register_balance_end));
                    $("#real_close_bal").text(self.format_currency(value.cash_register_balance_end_real));
                    $("#differ").text(self.format_currency(value.cash_register_difference));
                    $('.button.close_session').show();
                 });
            }
        });
        $("#cash_details").show();
        this.$('.button.close_session').hide();
        this.$('.button.ok').click(function() {
            var cash_values = [];
            var items = [];
            var cash_details = [];
            var total_close_balance = 0.00;
            $(".cashcontrol_td").each(function(){
                items.push($(this).val());
            });
            while (items.length > 0) {
              cash_details.push(items.splice(0,3))
            }
            _.each(cash_details, function(cashDetails){
            	total_close_balance += Number(cashDetails[2]);
                cash_values.push({
                   'coin_value':Number(cashDetails[0]),
                   'number':Number(cashDetails[1]),
                })
            });
            if(cash_values.length > 0){
                var params = {
                    model: 'pos.session',
                    method: 'set_close_balance',
                    args:[self.pos.pos_session.id, total_close_balance, cash_values]
                 }
                rpc.query(params, {async: false}).then(function(res){
                        if(res){
                        }
                }).fail(function (type, error){
                    if(error.code === 200 ){    // Business Logic Error, not a connection problem
                       self.gui.show_popup('error-traceback',{
                            'title': error.data.message,
                            'body':  error.data.debug
                       });
                    }
                });
            }
            var session_data = {
                model: 'pos.session',
                method: 'search_read',
                domain: [['id', '=', self.pos.pos_session.id]],
                fields: [
                	'cash_register_balance_start', 
                	'cash_register_total_entry_encoding',
                	'cash_register_balance_end',
                	'cash_register_balance_end_real',
                	'cash_register_difference',
                ]
            }
            rpc.query(session_data, {async: false}).then(function(data){
                if(data){
                     _.each(data, function(value){
                        $("#open_bal").text(self.format_currency(value.cash_register_balance_start));
                        $("#transaction").text(self.format_currency(value.cash_register_total_entry_encoding));
                        $("#theo_close_bal").text(self.format_currency(value.cash_register_balance_end));
                        $("#real_close_bal").text(self.format_currency(value.cash_register_balance_end_real));
                        $("#differ").text(self.format_currency(value.cash_register_difference));
                        $('.button.close_session').show();
                     });
                }
            });
		});
        this.$('.button.close_session').click(function() {
            var params = {
                model: 'pos.session',
                method: 'custom_close_pos_session',
                args:[self.pos.pos_session.id]
            }
            framework.blockUI();
            rpc.query(params).then(function(res){
                if(res){
                    if(self.pos.config.z_report_pdf){
                        var pos_session_id = [self.pos.pos_session.id];
                        self.pos.chrome.do_action('aspl_pos_close_session.pos_z_report',{additional_context:{
                                   active_ids:pos_session_id,
                        }});
                    }
                    if(self.pos.config.iface_print_via_proxy){
                        var pos_session_id = [self.pos.pos_session.id];
                        var report_name = "aspl_pos_close_session.pos_z_thermal_report_template";
                        var params = {
                            model: 'ir.actions.report',
                            method: 'get_html_report',
                            args: [pos_session_id, report_name],
                        }
                        rpc.query(params, {async: false})
                        .then(function(report_html){
                            if(report_html && report_html[0]){
                                self.pos.proxy.print_receipt(report_html[0]);
                            }
                        });
                    }
                    if(self.pos.config.email_close_session_report){
                        var pos_session_id = self.pos.pos_session.id;
                        var params = {
                            model: 'pos.session',
                            method: 'send_email_z_report',
                            args: [pos_session_id]
                        }
                        rpc.query(params, {async: false})
                        .then(function(res){
                            if(res){}
                        }).fail(function(){
                        	self.chrome.pos_notify("Error de Conexion", "No se puede conectar con el servidor, verifique su conexion a internet");
                        });
                    }
                    setTimeout(function(){
                        var cashier = self.pos.user || false;
                        if(cashier && cashier.login_with_pos_screen){
                            framework.redirect('/web/session/logout');
                        } else{
                            self.pos.gui.close();
                        }
                    }, 5000);
                }
            }).fail(function (type, error){
                if(error.code === 200 ){    // Business Logic Error, not a connection problem
                   self.gui.show_popup('error-traceback',{
                        'title': error.data.message,
                        'body':  error.data.debug
                   });
                }
            }).always(function(){
            	self.gui.close_popup();
            	framework.unblockUI();
            });
        });
        this.$('.button.cancel').click(function() {
              self.gui.close_popup();
        });
    },
    renderElement: function() {
        var self = this;
        this._super();
        var selectedOrder = self.pos.get_order();
        var table_row = "<tr id='cashcontrol_row'>" +
                        "<td><input type='text'  class='cashcontrol_td coin' id='value' value='%(value)s' /></td>" + "<span id='errmsg'/>"+
                        "<td><input type='text' class='cashcontrol_td no_of_coin' id='no_of_values' value='%(no_of_values)s' /></td>" +
                        "<td><input type='text' class='cashcontrol_td subtotal' id='subtotal' disabled='true' value='0.00' /></td>" +
                        "<td id='delete_row'><span class='fa fa-trash-o'></span></td>" +
                        "</tr>";
        if (_.isEmpty(self.pos.default_cashbox_lines)){
			$('#cashbox_data_table tbody').append(_.str.sprintf(table_row, {value: 0.0, no_of_values: 0.0}));
		} else {
			_.each(self.pos.default_cashbox_lines, function(cashbox){
				$('#cashbox_data_table tbody').append(_.str.sprintf(table_row, {value: cashbox.coin_value, no_of_values: cashbox.number}));
			});
		}
        $('#add_new_item').click(function(){
            $('#cashbox_data_table tbody').append(_.str.sprintf(table_row, {value: 0.0, no_of_values: 0.0}));
        });
        $('#cashbox_data_table tbody').on('click', 'tr#cashcontrol_row td#delete_row',function(){
			$(this).parent().remove();
			self.compute_subtotal();
		});
        $('#cashbox_data_table tbody').on('change focusout', 'tr#cashcontrol_row td',function(){
            var no_of_value, value;
            if($(this).children().attr('id') === "value"){
                value = Number($(this).find('#value').val());
                no_of_value = Number($(this).parent().find('td #no_of_values').val());
            }else if($(this).children().attr('id') === "no_of_values"){
                no_of_value = Number($(this).find('#no_of_values').val());
                value = Number($(this).parent().find('td #value').val());
            }
            $(this).parent().find('td #subtotal').val(value * no_of_value);
            self.compute_subtotal();
        });
        this.compute_subtotal = function(event){
            var subtotal = 0;
            _.each($('#cashcontrol_row td #subtotal'), function(input){
                if(Number(input.value) && Number(input.value) > 0){
                    subtotal += Number(input.value);
                }
            });
            $('.subtotal_end').text(self.format_currency(subtotal));
        }
    }
});
gui.define_popup({name:'cash_control', widget: CashControlWizardPopup});

var OpeningBalanceScreenWidget = screens.ScreenWidget.extend({
	events: {
		'click #validate_open_balance': 'validate_open_balance',
		'click #skip': 'skip_open_balance',
	},
    template: 'OpeningBalanceScreenWidget',
    show: function() {
    	this._super();
    	var self = this;
    	this.renderElement();
    	$(document).keypress(function (e) {
            if (e.which != 8 && e.which != 46 && e.which != 0 && (e.which < 48 || e.which > 57)) {
                return false;
            }
        });
    },
    renderElement:function(){
        this._super();
        var self = this;
    	self.open_form();
    },
    open_form: function() {
    	var self = this;
        var open_table_row = "<tr id='open_balance_row'>" +
                        "<td><input type='text'  class='openbalance_td' id='value' value='%(value)s' /></td>" +
                        "<td><input type='text' class='openbalance_td' id='no_of_values' value='%(no_of_values)s' /></td>" +
                        "<td><input type='text' class='openbalance_td' id='subtotal' disabled='true' value='0.00' /></td>" +
                        "<td id='delete_row'><span class='fa fa-trash-o' style='font-size: 20px;'></span></td>" +
                        "</tr>";
        if (_.isEmpty(self.pos.default_cashbox_lines)){
        	$('#opening_cash_table tbody').append(_.str.sprintf(open_table_row, {value: 0.0, no_of_values: 0.0}));
        } else {
        	_.each(self.pos.default_cashbox_lines, function(cashbox){
        		$('#opening_cash_table tbody').append(_.str.sprintf(open_table_row, {value: cashbox.coin_value, no_of_values: cashbox.number}));
             });
        }
        $('#add_open_balance').click(function(){
            $('#opening_cash_table tbody').append(_.str.sprintf(open_table_row, {value: 0.0, no_of_values: 0.0}));
        });
        $('#opening_cash_table tbody').on('click', 'tr#open_balance_row td#delete_row',function(){
            $(this).parent().remove();
            self.compute_subtotal();
		});
        $('#opening_cash_table tbody').on('change focusout', 'tr#open_balance_row td',function(){
            var no_of_value, value;
            if($(this).children().attr('id') === "value"){
                value = Number($(this).find('#value').val());
                no_of_value = Number($(this).parent().find('td #no_of_values').val());
            }else if($(this).children().attr('id') === "no_of_values"){
                no_of_value = Number($(this).find('#no_of_values').val());
                value = Number($(this).parent().find('td #value').val());
            }
            $(this).parent().find('td #subtotal').val(value * no_of_value);
            self.compute_subtotal();
        });
        this.compute_subtotal = function(event){
            var subtotal = 0;
            _.each($('#open_balance_row td #subtotal'), function(input){
                if(Number(input.value) && Number(input.value) > 0){
                    subtotal += Number(input.value);
                }
            });
            $('.open_subtotal').text(format.float(subtotal));
        }
    },
    skip_open_balance: function(){
    	var self = this;
    	self.gui.show_screen('products');
        var params = {
    		model: 'pos.session',
    		method: 'close_open_balance',
    		args:[self.pos.pos_session.id]
        }
        rpc.query(params, {async: false})
    },
    validate_open_balance: function(){
    	var self = this;
    	var cash_values = [];
    	var items = [];
        var cash_details = [];
        var total_open_balance = 0.00;
        $(".openbalance_td").each(function(){
            items.push($(this).val());
        });
        while (items.length > 0) {
          cash_details.push(items.splice(0,3))
        }
        _.each(cash_details, function(cashDetails){
            total_open_balance += Number(cashDetails[2]);
        	cash_values.push({
               'coin_value':Number(cashDetails[0]),
               'number':Number(cashDetails[1]),
            })
        });
        if(total_open_balance <= 0 && !self.pos.config.allow_with_zero_amount){
        	self.chrome.pos_notify("Control de Efectivo", "Por favor especifique el saldo de apertura.");
        	return;
        }
    	var params = {
        	model: 'pos.session',
        	method: 'set_open_balance',
        	args:[self.pos.pos_session.id, total_open_balance, cash_values]
        }
        rpc.query(params, {async: false}).then(function(res){
        	if(res){
        		self.gui.show_screen('products');
        	}
        }).fail(function (type, error){
            if(error.code === 200 ){    // Business Logic Error, not a connection problem
               self.gui.show_popup('error-traceback',{
                    'title': error.data.message,
                    'body':  error.data.debug
               });
            }
        });
    },
});
gui.define_screen({name:'openingbalancescreen', widget: OpeningBalanceScreenWidget});

return {
	ConfirmCloseSessionPopupWizard: ConfirmCloseSessionPopupWizard,
	CashControlWizardPopup: CashControlWizardPopup,
	OpeningBalanceScreenWidget: OpeningBalanceScreenWidget,
	CreateDepositPopupWidget: CreateDepositPopupWidget,
};

});