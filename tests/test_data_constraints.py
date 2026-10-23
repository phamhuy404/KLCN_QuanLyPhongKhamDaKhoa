# -*- coding: utf-8 -*-
import unittest
from datetime import date, timedelta
from core.validators import (
    validate_name,
    validate_bhyt,
    validate_cccd,
    validate_phone,
    validate_birth_date,
    validate_email,
    validate_address,
    validate_vital_signs,
    validate_medicine_data,
    validate_service_data,
    validate_patient_profile
)

class TestDataConstraints(unittest.TestCase):
    """Kiem thu toan dien cac rang buoc du lieu nghiep vu va bao mat."""

    def test_name_constraints(self):
        """Kiem tra rang buoc ho ten: khong so, khong ky tu la, dung chuan tieng Viet."""
        # 1. Ho ten chua so -> That bai
        ok, msg = validate_name('Nguyen Van 123', 'Họ và tên')
        self.assertFalse(ok)
        self.assertIn('chữ số', msg)

        # 2. Ho ten chua ky tu dac biet / la -> That bai
        for bad_name in ['Tran Thi @#$', 'Le Van <script>', 'Pham-Duc!']:
            ok, msg = validate_name(bad_name, 'Họ và tên')
            self.assertFalse(ok, f"Ten '{bad_name}' khong duoc phep hop le")

        # 3. Ho ten qua ngan hoac rong -> That bai
        ok, _ = validate_name('', 'Họ và tên')
        self.assertFalse(ok)
        ok, _ = validate_name('A', 'Họ và tên')
        self.assertFalse(ok)

        # 4. Ho ten chuan tieng Viet co dau -> Thanh cong
        valid_names = ['Nguyễn Văn An', 'Trần Thị Thu Hà', 'Đỗ Thành Vinh', 'Lê Hoàng Đức Đạt']
        for v_name in valid_names:
            ok, clean = validate_name(v_name, 'Họ và tên')
            self.assertTrue(ok, f"Ten hop le '{v_name}' phai thanh cong")
            self.assertEqual(clean, v_name)

    def test_bhyt_constraints(self):
        """Kiem tra rang buoc the BHYT: dung 10 chu so va tuyet doi khong co chu."""
        # 1. BHYT chua chu cai -> That bai
        for bad_bhyt in ['GD47979311', 'DN4791950003011', 'SV12345678', '479195030A']:
            ok, msg = validate_bhyt(bad_bhyt)
            self.assertFalse(ok, f"BHYT '{bad_bhyt}' chua chu phai that bai")
            self.assertIn('không có chữ', msg.lower())

        # 2. BHYT sai so luong chu so (khac 10 so) -> That bai
        for wrong_len in ['123456789', '12345678901', '479195']:
            ok, msg = validate_bhyt(wrong_len)
            self.assertFalse(ok)
            self.assertIn('đúng 10 chữ số', msg.lower())

        # 3. BHYT chuoi so 0 -> That bai
        ok, msg = validate_bhyt('0000000000')
        self.assertFalse(ok)

        # 4. BHYT hop le dung 10 chu so -> Thanh cong
        valid_bhyts = ['0790900001', '0791950002', '4791950301']
        for v_bhyt in valid_bhyts:
            ok, clean = validate_bhyt(v_bhyt)
            self.assertTrue(ok, f"BHYT 10 so '{v_bhyt}' phai thanh cong")
            self.assertEqual(clean, v_bhyt)

    def test_cccd_constraints(self):
        """Kiem tra rang buoc CCCD: dung 12 chu so, khong chu, khong lap lai vo ly."""
        # 1. CCCD chua chu -> That bai
        ok, msg = validate_cccd('07909000000A')
        self.assertFalse(ok)
        self.assertIn('chữ cái', msg.lower())

        # 2. CCCD khac 12 chu so -> That bai
        ok, _ = validate_cccd('07909000000')
        self.assertFalse(ok)
        ok, _ = validate_cccd('0790900000001')
        self.assertFalse(ok)

        # 3. CCCD chuoi so lap lai -> That bai
        ok, _ = validate_cccd('000000000000')
        self.assertFalse(ok)
        ok, _ = validate_cccd('111111111111')
        self.assertFalse(ok)

        # 4. CCCD hop le 12 so -> Thanh cong
        ok, clean = validate_cccd('079090000001')
        self.assertTrue(ok)
        self.assertEqual(clean, '079090000001')

    def test_phone_constraints(self):
        """Kiem tra rang buoc so dien thoai di dong Viet Nam."""
        # 1. Sai do dai hoac dau so khong phai nha mang VN -> That bai
        for bad_p in ['0123456789', '0283812345', '090123456', '09012345678', '090123456a']:
            ok, _ = validate_phone(bad_p)
            self.assertFalse(ok, f"SDT '{bad_p}' phai that bai")

        # 2. SDT di dong hop le 10 so (03, 05, 07, 08, 09) -> Thanh cong
        for v_p in ['0901234561', '0381234567', '0791234567', '0861234567', '0581234567']:
            ok, clean = validate_phone(v_p)
            self.assertTrue(ok, f"SDT hop le '{v_p}' phai thanh cong")
            self.assertEqual(clean, v_p)

    def test_birth_date_and_age_constraints(self):
        """Kiem tra rang buoc ngay sinh va do tuoi cho benh nhan va nhan su y te."""
        today = date.today()

        # 1. Ngay sinh tuong lai -> That bai
        future_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        ok, msg = validate_birth_date(future_date)
        self.assertFalse(ok)
        self.assertIn('ngày hiện tại', msg)

        # 2. Nhan su y te phai tu du 18 tuoi tro len
        underage_staff = (today - timedelta(days=365 * 16)).strftime('%Y-%m-%d')
        ok, msg = validate_birth_date(underage_staff, is_staff=True)
        self.assertFalse(ok)
        self.assertIn('18 tuổi', msg)

        # 3. Nhan su y te tren 18 tuoi hop le -> Thanh cong
        valid_staff = '1985-05-15'
        ok, _ = validate_birth_date(valid_staff, is_staff=True)
        self.assertTrue(ok)

    def test_vital_signs_constraints(self):
        """Kiem tra rang buoc chi so sinh ton y khoa trong benh an EMR."""
        # 1. Tam thu <= tam truong -> That bai
        ok, errs = validate_vital_signs({'huyet_ap_tam_thu': 100, 'huyet_ap_tam_truong': 110})
        self.assertFalse(ok)
        self.assertIn('huyet_ap', errs)

        # 2. Nhiet do bat thuong ngoai khoang 34 - 43 -> That bai
        ok, errs = validate_vital_signs({'nhiet_do': 50.0})
        self.assertFalse(ok)
        self.assertIn('nhiet_do', errs)

        # 3. Chi so sinh ton chuan -> Thanh cong
        ok, errs = validate_vital_signs({
            'mach': 75,
            'nhiet_do': 36.8,
            'huyet_ap_tam_thu': 120,
            'huyet_ap_tam_truong': 80,
            'spo2': 98,
            'nhip_tho': 18,
            'can_nang': 65,
            'chieu_cao': 170
        })
        self.assertTrue(ok)
        self.assertEqual(len(errs), 0)

    def test_medicine_and_service_constraints(self):
        """Kiem tra rang buoc gia thuoc va dich vu y te."""
        # 1. Gia thuoc <= 0 hoac ton kho am -> That bai
        ok, errs = validate_medicine_data({'ten_thuoc': 'Thuoc A', 'gia_ban': -500, 'so_luong_ton': -10})
        self.assertFalse(ok)

        # 2. Dich vu kham ty le BHYT ngoai 0 - 100% -> That bai
        ok, errs = validate_service_data({'ten_dich_vu': 'Sieu am', 'don_gia': 200000, 'bhyt_chi_tra_pt': 150})
        self.assertFalse(ok)
        self.assertIn('bhyt_chi_tra_pt', errs)

    def test_full_patient_profile_validation(self):
        """Kiem tra tong hop ho so benh nhan day du."""
        profile_data = {
            'ho_ten': 'Hoàng Bảo Nam',
            'sdt': '0901234561',
            'ngay_sinh': '1990-05-12',
            'gioi_tinh': 'Nam',
            'cccd': '079090000001',
            'bhyt': '0790900001',
            'email': 'baonam@gmail.com',
            'dia_chi': '120 Hai Bà Trưng, Phường Bến Nghé, Quận 1, TP.HCM',
            'nguoi_than_ho_ten': 'Hoàng Văn Bảy',
            'nguoi_than_sdt': '0901999881'
        }
        ok, errs = validate_patient_profile(profile_data)
        self.assertTrue(ok, f"Ho so hop le bi loi: {errs}")

if __name__ == '__main__':
    unittest.main()
