# Validation và giao dịch lịch

## Lỗi đã xác minh và hành vi sau sửa

- `update_schedule` trước đây ghi thẳng, thiếu kiểm tra ngày quá khứ, nhân viên/phòng trùng, chuyên khoa và hạn mức. Tạo, sửa, đăng ký, duyệt/bật lại ca dùng chung validation: ca 1/2/3 hợp lệ, ngày/giờ tương lai, thời gian trong khung ca và ít nhất 30 phút, sức chứa nguyên dương, nhân viên/tài khoản hoạt động, phòng hoạt động đúng chuyên khoa, không trùng nhân viên/bác sĩ/phòng. Giữ hạn mức 5 người/vai trò và 3 bác sĩ/chuyên khoa/ca; ca đang chờ duyệt cũng giữ chỗ để tránh duyệt vượt hạn mức.
- Ca sáng 07:00–11:30, chiều 13:30–17:00, tối 17:30–20:30; kết thúc ca không phải giờ bắt đầu lịch hẹn. Lượt khám 30 phút phải nằm trọn trong giờ ca. Giờ thiếu/sai/ngoài giờ không còn mặc định ca sáng hoặc 08:00.
- Đặt lịch phải tìm được duy nhất ca hoạt động có `trang_thai_duyet='DA_DUYET'`, đúng chuyên khoa, phòng và giờ; bác sĩ/nhân viên/tài khoản phải hoạt động. Ca NULL approval không được coi là đã duyệt. Tự chọn bác sĩ chỉ chọn ca thỏa điều kiện còn chỗ và không trùng lịch trong vòng 30 phút của bệnh nhân, bác sĩ hoặc phòng.
- Đổi lịch kiểm tra ca cũ từ bác sĩ/ngày/ca/giờ cũ và ca mới từ thông tin mới. Cập nhật phòng theo ca mới, tính lại bộ đếm của đúng ca từ lịch hẹn chưa hủy. Đổi trong cùng ca giữ nguyên số lượt. Hủy/phân công bác sĩ và API đổi trạng thái dùng cùng quy tắc; lịch đã hủy không được phục hồi qua đổi trạng thái. Hủy lại bị từ chối và không giảm lần nữa.
- Không sửa phòng/ngày/giờ/bác sĩ, tắt/xóa/từ chối/duyệt hủy ca còn lịch hẹn; phải điều phối từng lịch hẹn trước. Không tự tháo bác sĩ khỏi tất cả lịch hẹn trong ngày như trước. Tăng sức chứa được phép; không giảm thấp hơn số hẹn hiện có.
- API đổi phòng bác sĩ không còn ghi hàng loạt bỏ qua validation. Thay đổi các ca tương lai và phòng chính là một giao dịch; có ca không thể đổi thì rollback toàn bộ.
- Nhánh CSV lịch hẹn là phụ thuộc trực tiếp vì trước đây INSERT/UPDATE bỏ qua kiểm tra. Nay dùng cùng model/giao dịch; chỉ nhận bệnh nhân có sẵn khớp duy nhất số điện thoại, không sinh bệnh nhân/thông tin giả; không đổi bệnh nhân/chuyên khoa của lịch có sẵn. Lịch lịch sử/đã kết thúc cần quy trình nhập lịch sử riêng; không tự bỏ validation. Một dòng sai làm rollback toàn bộ nhánh nhập lịch hẹn. Các module CSV khác giữ nguyên.
- API khả dụng không tự sinh sức chứa 20/ca trống khi không có ca; trang chọn bác sĩ dùng giờ thực tế và duyệt rõ ràng. Khả dụng là thông tin tham khảo; lúc ghi luôn kiểm tra lại dưới khóa.

## Chống yêu cầu đồng thời

`core/scheduling.py` mở transaction trên kết nối mới, `SET XACT_ABORT ON`, lấy khóa độc quyền `sys.sp_getapplock` tên `clinic.calendar.v1`, chủ sở hữu `Transaction`, timeout 10 giây. Mã trả về âm bị từ chối, rollback và đóng kết nối; không tiếp tục ghi khi không lấy được khóa. Đây là khóa ở SQL Server, dùng chung giữa nhiều process/Website/API, không phải mutex Python.

Mọi đường ghi lịch trong hai model và nhánh import CSV dùng khóa này. Đọc lại lịch hẹn, kiểm tra trùng/ca/sức chứa, INSERT/UPDATE, đồng bộ bộ đếm, thông báo in-app và audit dùng cùng kết nối; chỉ lớp ngoài commit. Lỗi commit trả thất bại, rollback; không báo thành công trước commit. Mã lịch dùng MAX(id)+1 cũ cũng nằm trong khóa để giữ tương thích mã hiện tại. Không thay schema hoặc cập nhật database khi import.

Khóa được giữ tới commit/rollback theo [tài liệu Microsoft](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-getapplock-transact-sql). Đổi lại, các yêu cầu ghi lịch được tuần tự hóa toàn hệ thống; tải cao có thể timeout và cần thử lại. SQL trực tiếp từ công cụ ngoài, script cũ, trigger hay dịch vụ khác không dùng khóa này vẫn có thể phá ràng buộc; không tuyên bố bảo vệ được các writer đó. Thay đổi danh mục/phòng/chuyên khoa/nhân sự đồng thời ngoài các đường lịch chưa được kiểm thử.

Database hiện không lưu FK ca trên lịch hẹn. Để chạy tương thích mà không migration, ca cũ được xác định bằng bác sĩ/ngày/ca/giờ; dữ liệu cũ trùng hoặc không còn ca bị từ chối rõ ràng để kiểm tra thủ công, không đoán ca và không sửa hàng loạt. Bộ đếm chỉ đồng bộ những ca liên quan trong giao dịch; không sửa hàng loạt dữ liệu cũ. Không chuẩn bị schema mới vì bản sửa không phụ thuộc schema mới.

## Chạy và cấu hình

Từ thư mục Website, Python/dependency hiện có:

```powershell
& C:/laragon/bin/python/python-3.13/python.exe -B -m unittest tests.test_scheduling_safety -v
$env:PYTHONPATH = 'tests'
& C:/laragon/bin/python/python-3.13/python.exe -B -m unittest test_startup_safety test_security_access test_clinical_media -q
```

Chỉ chạy các file trên, không dùng unittest discover/pytest toàn repo vì có test cũ kết nối DB thật.

Test dùng `create_test_app`, `TESTING=True`, khóa phiên test riêng và `DATABASE_CONNECTION_FACTORY` kết nối SQLite shared-memory. Mỗi kết nối được kiểm tra `PRAGMA database_list` không có file. Guard chặn pyodbc.connect, SMTP và thread ứng dụng từ trước khi import. Test HTTP dùng cổng localhost ngẫu nhiên, chỉ mở thread do test sở hữu rồi đóng server sau test. Không dùng Website đang chạy trên cổng 5000.

Website vẫn chạy bằng `python app.py` với dependency/cấu hình SQL Server và `SECRET_KEY` hiện có; không đổi lệnh khởi động. Lệnh này khởi động dịch vụ runtime thật, vì vậy chưa được chạy trong nhiệm vụ trên cấu hình vận hành. Để kiểm thử an toàn phải dùng factory test ở trên, không trỏ vào cấu hình DB thật. Kiểm tra startup không còn tự sửa schema như mô tả trong `startup_safety.md`.

## Kiểm chứng và phần chặn

- Kết quả chạy cuối: 24 test lịch đạt; 64 test hồi quy startup/bảo mật/dữ liệu và ảnh đạt; không còn test thất bại. `git diff --check` sạch, editor không báo lỗi trong các module lịch đã kiểm tra. Lỗi audit được cố ý gây ra trong một test để xác nhận rollback, không phải lỗi của lượt chạy kiểm thử.
- Test mới chạy model và SQL đọc/ghi thật trên SQLite RAM qua adapter T-SQL; không mock các nghiệp vụ đặt/đổi/hủy. Test HTTP đăng nhập → GET trang đặt lịch → API đặt lịch → đổi ca/phòng → hủy, đọc lại database quan sát bộ đếm `1/0 → 0/1 → 0/0`.
- Kiểm tra ca sai/quá khứ/trùng nhân viên/phòng/sai chuyên khoa, hạn mức nhân sự, sức chứa, ca thiếu/chưa duyệt/tắt, ngoài giờ, trùng bệnh nhân/bác sĩ, tự chọn bác sĩ, đổi cùng ca/khác ca/khác ngày, hủy lặp, phân công lặp, từ chối/tắt/xóa ca có hẹn, nhập CSV, lỗi commit rollback mọi dữ liệu liên quan.
- Riêng batch `sp_getapplock` được MOCK bằng mã trả về trong adapter. Test âm kiểm tra không ghi nghiệp vụ khi khóa lỗi. SQLite không chứng minh khóa liên process, isolation, T-SQL/ODBC, timeout/deadlock hay cạnh tranh SQL Server.
- Chưa có SQL Server test được xác nhận độc lập; chưa chạy Website với SQL Server, chưa thao tác bằng trình duyệt/Flutter thật. Đã render trang và gọi HTTP thật; chưa chạy JavaScript đặt lịch tự động trong trình duyệt.

Để nghiệm thu SQL Server cần bổ sung server/database test được xác nhận độc lập không phải DB thật, tài khoản riêng có quyền dữ liệu test và `sp_getapplock`, kết nối được phép và factory test trỏ duy nhất database đó, các tài khoản/hồ sơ/ca test được cấp phép. Không dùng dữ liệu vận hành, seed hay migration tự động. Sau khi có môi trường: chạy hai kết nối/process đồng thời đặt cùng giờ bác sĩ, cùng bệnh nhân ở hai bác sĩ, khác giờ tranh chỗ cuối ca; mỗi tình huống chỉ một yêu cầu thành công, số hẹn/bộ đếm không vượt sức chứa. Tiếp tục thử hai yêu cầu hủy cùng lịch, đổi cùng ca khi đầy, đổi chéo ca/phòng, sửa/tắt/duyệt/hủy ca cạnh tranh với đặt lịch, timeout khóa và commit thất bại; kiểm tra cả bản ghi, bộ đếm và phòng sau commit/rollback. Phải xác nhận SQL Server thật trước khi tuyên bố đạt nghiệm thu cạnh tranh.

## File thuộc nhiệm vụ

- `core/scheduling.py`: validation, phân giải ca, chống trùng/sức chứa, khóa/giao dịch.
- `core/database.py`: chia sẻ kết nối giao dịch lịch cho audit/thông báo nội bộ.
- `models/schedule_model.py`: áp dụng validation/khóa cho tạo/sửa/đăng ký/duyệt/đổi phòng/tắt/xóa.
- `models/appointment_model.py`: đặt/đổi/hủy/phân công/trạng thái/khả dụng và bộ đếm.
- `models/user_model.py`: trạng thái ca bác sĩ trên giao diện theo giờ/duyệt thực tế.
- `controllers/api_controller.py`: không mặc định ca sai, boolean duyệt, chuyển đổi phòng qua model.
- `core/csv_service.py`: nhánh lịch hẹn dùng validation/giao dịch chung.
- `tests/test_scheduling_safety.py`: test cô lập lịch, API và HTTP.
- Tài liệu này và liên kết README. Các thay đổi từ nhiệm vụ trước được giữ nguyên.
