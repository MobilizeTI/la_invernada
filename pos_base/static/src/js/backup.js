odoo.define('pos_base.pos_kanban', function (require) {
"use strict";

var core = require('web.core');
var KanbanRenderer = require('web.KanbanRenderer');
var KanbanView = require('web.KanbanView');
var Session = require('web.session');
var view_registry = require('web.view_registry');

var QWeb = core.qweb;

var _t = core._t;
var _lt = core._lt;

var PosRenderer = KanbanRenderer.extend({
	events:_.extend({}, KanbanRenderer.prototype.events || {}, {
        'click .js_backup' : '_onBackupClick',
        'click .js_download' : '_onDownloadClick'
    }),
    willStart: function () {
    	var self = this;
        var def = this._rpc({
            model: 'ir.config_parameter',
            method: 'get_param',
            args: ['pos.local.storage']
        }).then(function (result) {
            self.pos_key = result;
        });
    	return $.when(this._super.apply(this, arguments), def);
    },
    /**
     * @override
     * @private
     * @returns {Deferred}
     */
    _render: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            var backup_render = QWeb.render('pos_base.Backup', {
                widget: self,
            });
            self.$el.prepend(backup_render);
        });
    },
    _onBackupClick: function(){
    	var self = this;
    	var data = localStorage[self.pos_key];
    	if(data !== undefined && data !== ""){
            data = JSON.parse(data);
            var content = JSON.stringify({
                'paid_orders':  data,
            },null,2);
            var URL = window.URL || window.webkitURL;
            var blob = new Blob([content]);

            var href_params = {
            	download: 'Pedidos POS.json',
                href: URL.createObjectURL(blob)
            }
            $(".js_download").attr(href_params);
            self._toggle_class();
        }
    },
    _toggle_class(){
    	$(".js_backup").toggleClass('o_hidden');
        $(".js_download").toggleClass('o_hidden');
    },
    _onDownloadClick: function(){
    	var self = this;
    	self._toggle_class();
    }
});

var PosKanbanView = KanbanView.extend({
    config: _.extend({}, KanbanView.prototype.config, {
        Renderer: PosRenderer,
    }),
});

view_registry.add('pos_kanban', PosKanbanView);

return {
    Renderer: PosKanbanView,
};

});