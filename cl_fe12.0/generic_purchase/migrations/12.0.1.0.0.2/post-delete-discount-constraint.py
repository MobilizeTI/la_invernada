import logging
_logger = logging.getLogger(__name__)


def migrate(cr, installed_version):
    cr.execute("ALTER TABLE purchase_order_line DROP CONSTRAINT IF EXISTS purchase_order_line_discount_value_limit")