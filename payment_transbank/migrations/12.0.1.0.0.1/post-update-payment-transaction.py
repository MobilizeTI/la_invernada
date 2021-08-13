
def migrate(cr, installed_version):
    cr.execute("""UPDATE payment_transaction pt
            SET transbank_auth_transaction = ptr.auth_transaction,
                transbank_payment_type = ptr.payment_type,
                transbank_fee_type = ptr.fee_type,
                transbank_amount_fee = ptr.amount_fee,
                transbank_last_digits = ptr.last_digits
            FROM payment_acquirer pa, 
                sale_order_transaction_rel m2m_payment,
                sale_order s, payment_transbank ptr
            WHERE pa.provider = 'transbank' AND pt.state IN ('authorized', 'done')
                AND pa.id = pt.acquirer_id
                AND m2m_payment.transaction_id = pt.id
                AND s.id = m2m_payment.sale_order_id 
                AND ptr.order_id = s.id
        """)