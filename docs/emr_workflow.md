# Liên kết lịch hẹn và giao dịch phiếu khám EMR

> Cấu hình test hiện tại chỉ dùng MSSQL: xem [môi trường kiểm thử MSSQL](mssql_test_environment.md).
> Các đoạn SQLite/RAM và số test đạt bên dưới là ghi chép lịch sử trước khi điều chỉnh, không phải hướng dẫn chạy hiện tại hay bằng chứng MSSQL đã chạy thành công.


## Lỗi đã xác minh

- `save_examination` và `finish_examination` cập nhật `UPDATE TOP (1) lich_hen` chỉ theo bệnh nhân, không lưu `phieu_kham.lich_hen_id`. Khi một người có nhiều lịch, có thể đổi trạng thái sai lịch.
- `/emr/save-step` tìm phiếu mở mới nhất chỉ theo bệnh nhân, có thể trộn hai lần khám hoặc tạo draft rồi `/emr/save` lại sinh phiếu khác.
- Thiếu kiểm tra bác sĩ phụ trách/trạng thái trước khi ghi; bác sĩ và phòng có fallback ID 1. Hoàn tất lặp có thể tạo thêm đơn thuốc; lưu lại có thể tạo thêm hóa đơn.
- Giao diện tự chọn phiếu mở đầu tiên trong lịch sử, tự thêm hai thuốc mẫu; sau khi đổi lần khám có thể giữ trạng thái khóa và hiển thị CLS của lần khác.

## Quy tắc sau sửa

### Có lịch hẹn

Gửi `appointment_id` hoặc `lich_hen_id` chính xác. Nếu gửi cả hai thì chúng phải giống nhau. Backend kiểm tra bệnh nhân, bác sĩ, phòng, chuyên khoa, tài khoản/nhân viên còn hoạt động, lịch đã tiếp nhận và chưa kết thúc/hủy; không khám lịch của ngày tương lai. BACSI chỉ ghi phiếu do chính mình phụ trách; ADMIN dùng bác sĩ thực tế được chỉ định. Policy phạm vi bệnh nhân hiện có vẫn được áp dụng tại API.

Draft lưu `lich_hen_id` ngay từ lần đầu. Các lần lưu bước trả `record_id`, `ma_phieu`, `step`; giao diện giữ và gửi lại `record_id`. Lưu/hoàn tất cập nhật chính xác lịch gắn trên phiếu, không cập nhật theo bệnh nhân và không chọn TOP 1. Nếu lịch có nhiều phiếu liên kết sẵn thì từ chối để kiểm tra thủ công, không chọn ngẫu nhiên.

### Khám trực tiếp

Chọn “Khám trực tiếp mới”, chọn bác sĩ/phòng thật, gửi `walk_in: true` cùng `encounter_key` UUID riêng cho lần khám. Key được mã hóa base32 chữ hoa đầy đủ 128 bit vào `ma_phieu` dạng `PKW...` dài 29 ký tự, vừa cột hiện có và không phụ thuộc phân biệt hoa/thường của SQL Server. Gửi lại cùng key khi draft còn mở trả lại đúng phiếu; key mới là lần khám mới. Không gửi đồng thời key khám trực tiếp với một lịch hẹn.

`lich_hen_id` của khám trực tiếp luôn NULL. Không tự chọn một lịch khác của bệnh nhân. Không sinh thêm bệnh nhân hoặc dùng bác sĩ/phòng dự phòng. Quyền truy cập bệnh nhân vẫn như trước; không mở rộng phạm vi bác sĩ với bệnh nhân chưa được tiếp nhận vào chuyên khoa.

### Hồ sơ cũ không có liên kết

Không backfill, ghép theo ngày/bệnh nhân hay sửa dữ liệu cũ. Người dùng phải chọn rõ `record_id` của phiếu đang mở nếu tiếp tục hồ sơ cũ. Phiếu NULL liên kết giữ NULL; cố gán thêm lịch hẹn bị từ chối. Phiếu không còn bác sĩ/phòng hợp lệ, nhiều hóa đơn không rõ ràng hoặc dữ liệu không nhất quán cần được kiểm tra thủ công, không tự sửa dữ liệu vận hành.

### Lưu bước, chuyển CLS và hoàn tất

- `save-step` chỉ tạo/cập nhật draft được định danh; không tạo đơn, chỉ định hoặc hóa đơn. Không tự báo “Chờ kết quả CLS” chỉ vì chuyển bước, khi chưa có chỉ định thật. Bước 4 bị chặn nếu còn CLS chưa đủ kết quả/duyệt.
- `save` tái sử dụng draft, lưu phiếu, chỉ định, đơn nếu có và hóa đơn trong một giao dịch. Phiếu đã có chỉ định/đơn/hóa đơn không được gọi lưu lại để sinh thêm; dùng `finish` sau CLS.
- `finish` kiểm tra lại phiếu, bác sĩ và lịch liên kết trong giao dịch. Mọi CLS của đúng phiếu phải được duyệt và có nội dung kết quả hoặc ảnh. CLS thuộc phiếu khác không được dùng để qua kiểm tra.
- Hoàn tất draft chưa sinh viện phí dùng lại đường lưu chung để có đúng hóa đơn ban đầu. Sau CLS, giữ hóa đơn ban đầu, không sinh thêm. Phiếu đã có đơn không được yêu cầu tạo thêm đơn qua finish; có thể hoàn tất không gửi đơn mới. Chỉnh sửa đơn đã có thuộc quy trình riêng.
- Lưu/hoàn tất phiếu đã kết thúc bị từ chối, kể cả gửi lại cùng yêu cầu. Đây là chống trùng bằng từ chối lặp, không trả thành công giả cho yêu cầu bị từ chối.
- Không tự điền thuốc mẫu. Thông báo thành công phản ánh trạng thái phiếu thật, không báo đã chuyển CLS/đơn khi không có các mục đó. Khi đổi lượt khám, reset thuốc/ảnh/trạng thái khóa và chỉ hiển thị CLS của phiếu đang chọn. Không đổi bác sĩ sở hữu phiếu bằng lựa chọn bác sĩ chuyển CLS.

## Giao dịch và dữ liệu lưu một phần

Dùng khóa transaction `clinic.calendar.v1` hiện có của SQL Server để các thao tác EMR và lịch hẹn cùng phối hợp. Đọc lại định danh/trạng thái, ghi phiếu, lịch hẹn, chỉ định, đơn, hóa đơn, thông báo in-app và audit dùng chung kết nối. Chỉ lớp ngoài commit; lỗi SQL hoặc commit trả thất bại và rollback. Cả nhập/duyệt CLS tham gia khóa chung để tránh thay đổi kết quả trong lúc hoàn tất.

Các API EMR giữ transaction tới khi xây dựng xong response. Ảnh được tạo bằng mở file độc quyền, không ghi đè file có sẵn. Theo dõi chỉ file mới của yêu cầu này; khi yêu cầu lỗi/rollback thì dọn các file đó. Không di chuyển/xóa ảnh hiện hữu. Lỗi dọn file được ghi log; cần kiểm tra thủ công nếu hệ điều hành không cho xóa. Không có giao dịch phân tán giữa SQL Server và filesystem: mất kết nối đúng lúc commit hoặc process/máy bị tắt cần đối soát, chưa được kiểm thử trong nhiệm vụ.

Không thay schema, không migration/seed. Cột `phieu_kham.lich_hen_id` và FK đã có trong schema dự án. Không tự sửa các bản ghi trùng/cũ. Khóa bảo vệ các writer ứng dụng có phối hợp; SQL/script ngoài không dùng khóa chung vẫn cần kiểm soát riêng. Khóa chung có thể làm các yêu cầu ghi phải đợi/timeout khi tải cao.

## Chạy kiểm thử và Website

Từ thư mục Website, dùng interpreter/dependency đã có, không cài thêm:

```powershell
& C:/laragon/bin/python/python-3.13/python.exe -B -m unittest tests.test_emr_workflow -v
$env:PYTHONPATH = 'tests'
& C:/laragon/bin/python/python-3.13/python.exe -B -m unittest test_startup_safety test_security_access test_clinical_media tests.test_scheduling_safety -q
```

Không chạy discovery toàn repo hoặc các test cũ vì có test dùng DB thật. Test mới dùng `create_test_app`, `TESTING=True`, khóa phiên test và `DATABASE_CONNECTION_FACTORY` SQLite RAM. Mỗi kết nối được xác minh `PRAGMA database_list` không có file. Chặn `pyodbc.connect`, SMTP và thread ứng dụng từ trước khi import. HTTP test chỉ mở thread do test sở hữu trên localhost/cổng ngẫu nhiên và đóng sau test. Các dữ liệu fixture chỉ tồn tại trong RAM của test.

Website vẫn khởi động bằng `python app.py` với cấu hình SQL Server/`SECRET_KEY` hiện có. Lệnh này dùng runtime vận hành, không phải cấu hình test; không được chạy trên cấu hình DB thật trong nhiệm vụ. Không dùng Website cổng 5000 để ghi thử. Chưa cung cấp server test dài hạn; test HTTP tự khởi động/dừng server tạm an toàn.

## Luồng đã kiểm chứng

- Kết quả cuối: 16 test EMR đạt và 88 test hồi quy cô lập đạt; không còn test thất bại. JavaScript đã render qua kiểm tra cú pháp và bài chạy DOM mô phỏng; editor không báo lỗi ở các file Python đã sửa. Cả diff staged và chưa staged qua `git diff --check`/`git diff --cached --check`; chỉ có cảnh báo chuẩn hóa LF/CRLF của Git, không thay đổi staging để xử lý cảnh báo này.
- Model/API thật trên DB RAM: cùng bệnh nhân có nhiều lịch, hai lần khám khác nhau, draft rồi lưu chung một phiếu, khám trực tiếp và gửi lại key, hồ sơ cũ NULL không tự ghép.
- HTTP: đăng nhập bác sĩ → GET trang EMR có lịch hẹn cụ thể → save-step → save có CLS → finish bị chặn → đăng nhập KTV và nhập kết quả → bác sĩ duyệt → finish thành công → finish lặp trả 400. Đọc lại DB: đúng 1 phiếu, 1 đơn, 1 hóa đơn; lịch được chọn “Đã khám”, lịch còn lại giữ “Đã tiếp nhận”.
- Gây lỗi sau khi cập nhật draft/hồ sơ bệnh nhân, khi ghi chi tiết hóa đơn, khi hoàn tất đang ghi đơn, và lỗi commit: dữ liệu liên quan rollback, không có bản ghi lưu một phần. Ảnh mới được dọn khi lỗi commit; ảnh fixture hiện hữu giữ nguyên.
- JavaScript thật đã render được kiểm tra cú pháp bằng Node và thực thi với DOM mô phỏng: khởi tạo không lỗi TDZ, chọn đúng lịch từ URL, payload chứa đúng lịch/phiếu, không có thuốc tự thêm, đổi lượt reset draft/khóa và giữ key khi gửi lại.
- Trình duyệt thật trên server RAM riêng: đăng nhập bác sĩ, mở EMR với `appointment_id=2`, thấy đúng lượt được chọn, nhập triệu chứng/chẩn đoán, bỏ qua CLS đến kê đơn (toa rỗng), bấm hoàn tất và nhận thông báo lưu phiếu thành công. Phiên bị gián đoạn ngay tại hộp thông báo; chưa quan sát tiếp phần reload/đọc DB của chính phiên trình duyệt này. Database sau giao dịch đã được đối chiếu trong test HTTP tự động độc lập ở trên. Server RAM của lượt trình duyệt đã dừng sau gián đoạn.
- Lượt trình duyệt đăng nhập điều hướng mặc định tới dashboard bị 500 do fixture không dựng đầy đủ bảng dashboard; đã điều hướng trực tiếp sang EMR và trang EMR chạy được. Không kết luận đó là lỗi dashboard vận hành và không sửa module dashboard.

## Chưa kiểm chứng / điều kiện còn thiếu

SQLite chạy SQL đọc/ghi nghiệp vụ thật nhưng adapter dịch một số cú pháp T-SQL và MOCK `sp_getapplock`. Chưa chứng minh T-SQL/ODBC, khóa liên process, deadlock, timeout hoặc hai yêu cầu hoàn tất đồng thời trên SQL Server. Chưa chạy luồng CLS đầy đủ bằng thao tác trình duyệt thật (đã chạy HTTP), chưa thử Flutter và mất kết nối/crash tại commit.

Cần SQL Server test được xác nhận độc lập không phải database vận hành, cấu hình kết nối/factory riêng, tài khoản và dữ liệu test được cho phép, quyền `sp_getapplock` để nghiệm thu thực tế. Khi có môi trường, thử hai process hoàn tất cùng phiếu, lưu/hoàn tất/nhập-duyệt CLS cạnh tranh, commit thất bại, rồi kiểm tra phiếu/lịch/đơn/hóa đơn và rollback. Không tự trỏ vào DB thật hoặc tạo môi trường bằng seed/migration.

## File thuộc nhiệm vụ

- `core/emr_workflow.py`: policy định danh, xác thực bác sĩ, kết quả CLS, thuốc và transaction API/ảnh.
- `models/medical_record_model.py`: draft, save, finish và transaction đồng bộ CLS.
- `controllers/api_controller.py`: truyền định danh/chế độ khám trực tiếp, validation, response trạng thái thật.
- `models/patient_model.py`: lịch sử mang định danh lịch hẹn/bác sĩ/phòng để chọn đúng phiếu.
- `controllers/admin_controller.py`: cấp danh sách lịch/phòng đã lọc policy cho EMR.
- `templates/admin/emr.html`: chọn lần khám, định danh payload, reset trạng thái và bỏ thuốc mẫu.
- `templates/admin/appointments.html`, `templates/admin/reception.html`: link EMR mang ID lịch hẹn.
- `core/image_service.py`: tạo file độc quyền và theo dõi ảnh mới để rollback.
- `tests/test_emr_workflow.py`: test EMR mới; `tests/test_clinical_media.py`: bổ sung cột liên kết cho schema fixture RAM cũ.
- Tài liệu này và README. Giữ nguyên các thay đổi của những nhiệm vụ trước.
