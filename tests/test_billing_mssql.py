"""MSSQL integration only; independent database/fixture opt-in required before setup."""
import unittest
import threading
from tests import test_pharmacy_mssql as pharmacy


class BillingMssqlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pharmacy.PharmacyMssqlTests.setUpClass.__func__(cls)

    connection = pharmacy.PharmacyMssqlTests.connection
    login = pharmacy.PharmacyMssqlTests.login
    tearDown = pharmacy.PharmacyMssqlTests.tearDown
    call = pharmacy.PharmacyMssqlTests.call
    prepare_paid = pharmacy.PharmacyMssqlTests.prepare_paid

    def setUp(self):
        pharmacy.PharmacyMssqlTests.setUp(self)
        # All data below belongs solely to the opt-in disposable MSSQL fixture.
        self.keeper.execute('''INSERT INTO hoa_don(ma_hoa_don,benh_nhan_id,phieu_kham_id,
            tong_tien,tien_bhyt,thanh_tien,trang_thai)
            SELECT 'HD_BILLING_TEST',101,id,150000,0,150000,N'Chưa thanh toán' FROM phieu_kham''')
        self.bill = self.keeper.execute("SELECT id FROM hoa_don WHERE ma_hoa_don='HD_BILLING_TEST'").fetchone()[0]
        self.keeper.execute('''INSERT INTO chi_tiet_hoa_don(hoa_don_id,loai_khoan_thu,ten_khoan_thu,
            tham_chieu_id,so_luong,don_gia,thanh_tien)
            SELECT ?,N'Khám bệnh','MSSQL test consultation',id,1,150000,150000 FROM phieu_kham''', (self.bill,))
        self.keeper.commit()

    def pay(self):
        return self.client.post('/api/billing/pay', json=dict(invoice_id=self.bill,
            expected_amount=150000,confirm_received=True,hinh_thuc_thanh_toan='Tiền mặt'))

    def test_owner_other_patient_and_no_patient_collection(self):
        self.login(1)
        self.assertEqual(self.client.get('/api/billing/invoice/'+str(self.bill)).status_code,200)
        response = self.client.post('/api/billing/request',json={'invoice_id':self.bill})
        self.assertEqual(response.status_code,200,response.get_json())
        self.assertFalse(response.get_json()['payment_confirmed'])
        self.assertEqual(self.pay().status_code,403)
        self.login(2)
        self.assertEqual(self.client.get('/api/billing/invoice/'+str(self.bill)).status_code,403)
        self.assertEqual(self.client.post('/api/billing/request',json={'invoice_id':self.bill}).status_code,403)
        self.assertEqual(self.client.get('/api/billing/invoice/9999999').status_code,404)

    def test_cashier_collection_replay_and_canceled_invoice(self):
        self.login(6)
        response = self.pay()
        self.assertEqual(response.status_code,200,response.get_json())
        self.assertEqual(self.pay().status_code,409)
        self.keeper.execute('UPDATE hoa_don SET trang_thai=? WHERE id=?',('Đã hủy',self.bill))
        self.keeper.commit()
        self.assertEqual(self.pay().status_code,409)

    def test_total_or_configured_price_mismatch_is_not_collected(self):
        self.login(7)
        self.keeper.execute('UPDATE hoa_don SET thanh_tien=149999 WHERE id=?',(self.bill,))
        self.keeper.commit()
        self.assertEqual(self.pay().status_code,409)
        self.keeper.execute('UPDATE hoa_don SET thanh_tien=150000 WHERE id=?',(self.bill,))
        self.keeper.execute('UPDATE chuyen_khoa SET gia_kham_mac_dinh=170000 WHERE id=10')
        self.keeper.commit()
        self.assertEqual(self.pay().status_code,409)

    def test_drug_invoice_replay_does_not_reset_dispensed_order(self):
        self.prepare_paid()
        result = self.call('dispense_prescription',self.order,audit_user=self.actor)
        self.assertTrue(result[0],result)
        bill = self.keeper.execute("SELECT id FROM hoa_don WHERE ma_hoa_don LIKE 'HDT%'").fetchone()[0]
        self.keeper.rollback()
        self.login(6)
        response = self.client.post('/api/billing/pay',json=dict(invoice_id=bill,
            expected_amount=3000,confirm_received=True))
        self.assertEqual(response.status_code,409)
        state = self.keeper.execute('SELECT trang_thai FROM don_thuoc WHERE id=?',(self.order,)).fetchone()[0]
        self.keeper.rollback()
        self.assertEqual(state,'Đã nhận thuốc')

    def test_concurrent_collection_records_once(self):
        barrier, results = threading.Barrier(2), []
        def collect():
            barrier.wait(timeout=10)
            with self.app.app_context():
                results.append(self.billing.pay_invoice(self.bill,audit_user=self.actor,expected_amount=150000))
        threads = [threading.Thread(target=collect) for _ in range(2)]
        for thread in threads:
            self.start_test_thread(thread)
        for thread in threads:
            thread.join(timeout=20)
            self.assertFalse(thread.is_alive())
        self.assertEqual(sum(bool(result[0]) for result in results),1,results)


if __name__ == '__main__':
    unittest.main()
