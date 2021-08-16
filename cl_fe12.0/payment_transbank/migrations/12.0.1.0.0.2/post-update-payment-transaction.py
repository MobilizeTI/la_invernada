
def migrate(cr, installed_version):
    cr.execute("""UPDATE payment_transaction pt
            SET transbank_commerce_id = pa.commerce_id
            FROM payment_acquirer pa
            WHERE pa.provider = 'transbank' AND pt.state IN ('authorized', 'done')
                AND pa.id = pt.acquirer_id
        """)