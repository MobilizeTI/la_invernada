odoo.define('generic_purchase.PurchasePortalSidebar.instance', function (require) {
"use strict";

require('web.dom_ready');
var PurchasePortalSidebar = require('generic_purchase.PurchasePortalSidebar');

if (!$('.o_portal_purchase_sidebar').length) {
    return $.Deferred().reject("DOM doesn't contain '.o_portal_purchase_sidebar'");
}

var generic_purchase_portal_sidebar = new PurchasePortalSidebar();
return generic_purchase_portal_sidebar.attachTo($('.o_portal_purchase_sidebar')).then(function () {
    return generic_purchase_portal_sidebar;
});
});

//==============================================================================

odoo.define('generic_purchase.PurchasePortalSidebar', function (require) {
"use strict";

var PortalSidebar = require('portal.PortalSidebar');

var PurchasePortalSidebar = PortalSidebar.extend({
    events: {
        'click .o_portal_purchase_print': '_onPrintPurchase',
    },
    /**
     * @override
     */
    start: function () {
        var self = this;
        this._super.apply(this, arguments);
        var $purchaseHtml = this.$el.find('iframe#purchase_html');
        var updateIframeSize = self._updateIframeSize.bind(self, $purchaseHtml);
        $purchaseHtml.on('load', updateIframeSize);
        $(window).on('resize', updateIframeSize);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Called when the iframe is loaded or the window is resized on customer portal.
     * The goal is to expand the iframe height to display the full report without scrollbar.
     *
     * @private
     * @param {object} $el: the iframe
     */
    _updateIframeSize: function ($el) {
        var $wrapwrap = $el.contents().find('div#wrapwrap');
        // Set it to 0 first to handle the case where scrollHeight is too big for its content.
        $el.height(0);
        $el.height($wrapwrap[0].scrollHeight);
    },
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onPrintPurchase: function (ev) {
        ev.preventDefault();
        var href = $(ev.currentTarget).attr('href');
        this._printIframeContent(href);
    },
});


return PurchasePortalSidebar;
});
