"""Real MSSQL only. Same independent database and fixture opt-in as EMR tests."""
import threading
import unittest
from uuid import uuid4
from tests import test_emr_workflow as emr


class PharmacyMssqlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        emr.EmrWorkflowTests.setUpClass.__func__(cls)
        from models.pharmacy_model import PharmacyModel
        from models.billing_model import BillingModel
        cls.pharmacy, cls.billing = PharmacyModel, BillingModel

    connection = emr.EmrWorkflowTests.connection
    login = emr.EmrWorkflowTests.login
    tearDown = emr.EmrWorkflowTests.tearDown

    def setUp(self):
        emr.EmrWorkflowTests.setUp(self)
        self.keeper.executescript('''
            ALTER TABLE don_thuoc ADD ly_do_huy NVARCHAR(MAX),nguoi_huy NVARCHAR(MAX),
                thoi_gian_huy DATETIME2,nguoi_duyet NVARCHAR(MAX),ngay_duyet DATETIME2;
            ALTER TABLE hoa_don ADD trang_thai_nhan_thuoc NVARCHAR(MAX),
                hinh_thuc_thanh_toan NVARCHAR(MAX),nhan_vien_thu NVARCHAR(MAX),thoi_gian_thanh_toan DATETIME2;
            INSERT INTO phieu_kham(ma_phieu,benh_nhan_id,bac_si_id,phong_kham_id,trang_thai)
                VALUES('PHARMACY_TEST',101,203,1,N'Hoàn thành');
            INSERT INTO don_thuoc(ma_don_thuoc,phieu_kham_id,bac_si_id,trang_thai,hinh_thuc_mua)
                SELECT 'DT_TEST',id,203,N'Chờ bệnh nhân xác nhận mua',N'Chưa chọn' FROM phieu_kham;
            INSERT INTO chi_tiet_don_thuoc(don_thuoc_id,thuoc_id,so_luong) SELECT id,1,3 FROM don_thuoc;
        ''')
        self.order = self.keeper.execute('SELECT id FROM don_thuoc').fetchone()[0]
        self.keeper.commit()
        self.actor = {'id': 7, 'vai_tro': 'ADMIN'}

    def call(self, name, *args, **kwargs):
        with self.app.app_context():
            return getattr(self.pharmacy, name)(*args, **kwargs)

    def prepare_paid(self):
        result = self.call('choose_medicine_purchase_option', self.order)
        self.assertTrue(result[0], result)
        result = self.call('approve_prescription', self.order, reviewer_user=self.actor)
        self.assertTrue(result[0], result)
        bill = self.keeper.execute("SELECT id FROM hoa_don WHERE ma_hoa_don LIKE 'HDT%'").fetchone()[0]
        self.keeper.rollback()
        with self.app.app_context():
            result = self.billing.pay_invoice(bill, audit_user=self.actor)
        self.assertTrue(result[0], result)

    def stock(self):
        row = self.keeper.execute('SELECT so_luong_ton FROM thuoc WHERE id=1').fetchone()[0]
        self.keeper.rollback()
        return row

    def test_purchase_approve_payment_dispense_and_repeat(self):
        self.prepare_paid()
        self.assertTrue(self.call('dispense_prescription', self.order, audit_user=self.actor)[0])
        self.assertEqual(self.stock(), 7)
        self.assertFalse(self.call('dispense_prescription', self.order)[0])
        for _ in range(2):
            self.assertFalse(self.call('cancel_or_adjust_prescription', self.order, 'return', restore_stock=True)[0])
        self.assertEqual(self.stock(), 7)

    def test_concurrent_dispense_deducts_only_once(self):
        self.prepare_paid()
        barrier = threading.Barrier(2)
        def dispense():
            barrier.wait(timeout=10)
            return self.call('dispense_prescription', self.order, audit_user=self.actor)
        results = []
        def worker():
            results.append(dispense())
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            self.start_test_thread(thread)
        for thread in threads:
            thread.join(timeout=20)
            self.assertFalse(thread.is_alive())
        self.assertEqual(sum(bool(result[0]) for result in results), 1, results)
        self.assertEqual(self.stock(), 7)

    def test_stock_shortage_and_audit_failure_rollback(self):
        self.prepare_paid()
        self.keeper.execute('UPDATE thuoc SET so_luong_ton=2 WHERE id=1')
        self.keeper.commit()
        self.assertFalse(self.call('dispense_prescription', self.order)[0])
        self.assertEqual(self.stock(), 2)
        self.keeper.execute('UPDATE thuoc SET so_luong_ton=10 WHERE id=1')
        self.keeper.execute("CREATE TRIGGER test_stock_audit_failure ON audit_log AFTER INSERT AS BEGIN THROW 51001, 'Test audit failure', 1; END")
        self.keeper.commit()
        self.assertFalse(self.call('dispense_prescription', self.order)[0])
        self.assertEqual(self.stock(), 10)

    def test_two_orders_compete_for_last_stock(self):
        self.prepare_paid()
        self.keeper.executescript('''
            UPDATE thuoc SET so_luong_ton=5 WHERE id=1;
            INSERT INTO phieu_kham(ma_phieu,benh_nhan_id,bac_si_id,phong_kham_id,trang_thai)
                VALUES('PHARMACY_TEST_2',101,203,1,N'Hoàn thành');
            INSERT INTO don_thuoc(ma_don_thuoc,phieu_kham_id,bac_si_id,trang_thai,hinh_thuc_mua)
                SELECT 'DT_TEST_2',id,203,N'Chờ nhận thuốc',N'Mua tại bệnh viện'
                FROM phieu_kham WHERE ma_phieu='PHARMACY_TEST_2';
            INSERT INTO chi_tiet_don_thuoc(don_thuoc_id,thuoc_id,so_luong)
                SELECT id,1,3 FROM don_thuoc WHERE ma_don_thuoc='DT_TEST_2';
            INSERT INTO hoa_don(ma_hoa_don,benh_nhan_id,phieu_kham_id,tong_tien,tien_bhyt,thanh_tien,trang_thai)
                SELECT 'HDT_TEST_2',101,id,3000,0,3000,N'Đã thanh toán'
                FROM phieu_kham WHERE ma_phieu='PHARMACY_TEST_2';
            INSERT INTO chi_tiet_hoa_don(hoa_don_id,loai_khoan_thu,ten_khoan_thu,tham_chieu_id,so_luong,don_gia,thanh_tien)
                SELECT id,N'Thuốc','MSSQL test drug',1,3,1000,3000 FROM hoa_don WHERE ma_hoa_don='HDT_TEST_2';
        ''')
        second = self.keeper.execute("SELECT id FROM don_thuoc WHERE ma_don_thuoc='DT_TEST_2'").fetchone()[0]
        self.keeper.commit()
        barrier, results = threading.Barrier(2), []
        def worker(order):
            barrier.wait(timeout=10)
            results.append(self.call('dispense_prescription', order, audit_user=self.actor))
        threads = [threading.Thread(target=worker, args=(order,)) for order in (self.order, second)]
        for thread in threads:
            self.start_test_thread(thread)
        for thread in threads:
            thread.join(timeout=20)
            self.assertFalse(thread.is_alive())
        self.assertEqual(sum(bool(result[0]) for result in results), 1, results)
        self.assertEqual(self.stock(), 2)

    def test_receive_api_and_history_with_authenticated_pharmacist(self):
        self.login(4)
        payload = {'medicine_id': 1, 'quantity': 4, 'reason': 'MSSQL fixture receipt', 'receipt_id': str(uuid4())}
        for _ in range(2):
            response = self.client.post('/api/pharmacy/receive-stock', json=payload)
            self.assertEqual(response.status_code, 200, response.get_json())
            self.assertTrue(response.get_json()['success'])
        self.assertEqual(self.stock(), 14)
        response = self.client.get('/api/pharmacy/stock-history/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()['items']), 1)

    def test_unpaid_invoice_blocks_edit_and_cancel_cancels_invoice(self):
        self.assertTrue(self.call('choose_medicine_purchase_option', self.order)[0])
        self.assertFalse(self.call('update_prescription', self.order, [{'thuoc_id': 1, 'so_luong': 2}])[0])
        self.assertTrue(self.call('cancel_or_adjust_prescription', self.order, 'MSSQL test cancel')[0])
        row = self.keeper.execute('SELECT trang_thai FROM hoa_don').fetchone()[0]
        self.keeper.rollback()
        self.assertEqual(row, 'Đã hủy')
        self.assertEqual(self.stock(), 10)

    def test_receive_receipt_replay_and_history(self):
        receipt = str(uuid4())
        for _ in range(2):
            self.assertTrue(self.call('receive_stock', 1, 4, 'MSSQL fixture receipt', receipt, self.actor)[0])
        self.assertEqual(self.stock(), 14)
        self.assertEqual(len(self.call('stock_history', 1)), 1)


if __name__ == '__main__':
    unittest.main()
