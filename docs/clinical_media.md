# Dữ liệu lâm sàng và ảnh bệnh án

> Cấu hình test hiện tại chỉ dùng MSSQL: xem [môi trường kiểm thử MSSQL](mssql_test_environment.md).
> Các đoạn SQLite/RAM và số test đạt bên dưới là ghi chép lịch sử trước khi điều chỉnh, không phải hướng dẫn chạy hiện tại hay bằng chứng MSSQL đã chạy thành công.


Các file thay đổi trong nhiệm vụ này:

- Model: [patient_model.py](../models/patient_model.py),
  [medical_record_model.py](../models/medical_record_model.py),
  [user_model.py](../models/user_model.py) (ghi NULL khi tạo sinh hiệu).
- Hạ tầng/API: [image_service.py](../core/image_service.py),
  [clinical_data.py](../core/clinical_data.py), [medical_media.py](../core/medical_media.py),
  [api_controller.py](../controllers/api_controller.py), [app.py](../app.py),
  [config.py](../config.py), [.gitignore](../.gitignore).
- Giao diện: [lab_results.html](../templates/patient/lab_results.html),
  [records.html](../templates/patient/records.html), [profile.html](../templates/patient/profile.html),
  [complete_profile.html](../templates/patient/complete_profile.html),
  [patient_detail.html](../templates/admin/patient_detail.html),
  [patient_details.html](../templates/admin/patient_details.html),
  [patients.html](../templates/admin/patients.html), [emr.html](../templates/admin/emr.html),
  [main.js](../static/js/main.js).
- Kiểm thử/tài liệu: [test_clinical_media.py](../tests/test_clinical_media.py),
  [test_startup_safety.py](../tests/test_startup_safety.py),
  [README.md](../README.md), tài liệu này và
  [review_vital_defaults.sql](../database/migrations/review_vital_defaults.sql).

## Dữ liệu chưa ghi nhận

Sinh hiệu thiếu giữ `null`, không thay bằng số đo bình thường. Giá trị 0 được
giữ nguyên. Tuổi không thể tính khi thiếu/ngày sinh sai thì để trống. Website
hiển thị “Chưa đo” hoặc “Chưa có dữ liệu”; không gắn nhãn bình thường, ổn định
hay thời gian đo cố định. Form EMR không điền sẵn triệu chứng/chẩn đoán/điều trị
mẫu, và xóa giá trị của bệnh nhân trước khi chuyển hồ sơ. Luồng lưu/hoàn tất
thông thường yêu cầu chẩn đoán do nhân viên ghi nhận.

Nút kết thúc khám bình thường có xác nhận riêng của bác sĩ vẫn giữ hành vi
hiện có: đây là kết luận được người dùng chọn rõ ràng, không phải fallback
cho trường trống. Dị ứng/bệnh nền chưa khai báo không tự biến thành “Không có”.

Tạo bệnh nhân và đăng ký tài khoản ghi NULL rõ ràng cho sinh hiệu chưa đo,
tránh DEFAULT của SQL Server tự điền chỉ số. Không cập nhật bản ghi hiện hữu.
Không thể suy luận các số “bình thường” đã lưu từ trước là số đo thật hay giá
trị mặc định. Cần người phụ trách dữ liệu đối chiếu nguồn ghi nhận trước khi
quyết định chỉnh sửa.

[review_vital_defaults.sql](../database/migrations/review_vital_defaults.sql)
chỉ SELECT ra DDL đề xuất bỏ DEFAULT sinh hiệu; không thực thi DDL/DML. Chưa
chạy script trên database nào. Không sửa schema hay seed trong nhiệm vụ này.

## Quy tắc công bố kết quả

Quy tắc chung là `trang_thai == 'Đã duyệt'`, được dùng cho lịch sử khám mà
bệnh nhân đọc, trang kết quả, danh sách API, API chi tiết và endpoint ảnh CLS.
Trạng thái hoàn thành kỹ thuật hoặc có tên người duyệt không thay thế trạng
thái công bố. Kết quả đã duyệt nhưng rỗng vẫn là chưa có dữ liệu; không suy
luận thành kết luận bình thường. Kết quả chưa duyệt và ảnh của nó không được
đưa vào nội dung HTML/JSON bệnh nhân.

Nhân viên có quyền hiện hành vẫn xem được dữ liệu để xử lý/duyệt. Phạm vi
nhân viên chưa rõ nghiệp vụ vẫn theo các giới hạn đã ghi trong
[security_access.md](security_access.md); không tự mở rộng quyền nhân viên.

## Lưu và phục vụ ảnh

- Ảnh khám/CLS mới lưu trong `private_uploads/kham_benh/` hoặc
  `private_uploads/can_lam_sang/`, ngoài static. Có thể cấu hình đường dẫn tuyệt
  đối `MEDICAL_UPLOAD_DIR`; app từ chối nếu đường dẫn này nằm trong static.
  Thư mục chỉ được tạo khi có thao tác lưu ảnh, không phải lúc import.
- Database lưu URL `/medical-images/<category>/<filename>`. Endpoint xác thực
  lại tài khoản, tìm tham chiếu ảnh trong bệnh án/CLS, kiểm tra quyền bệnh nhân
  và trạng thái công bố trước khi trả file. File không có tham chiếu chưa được
  phục vụ, kể cả đoán đúng tên.
- Ảnh trả `Cache-Control: private, no-store`, `Vary: Cookie`, `nosniff` và MIME
  raster được kiểm tra từ nội dung. Không phục vụ SVG/HTML qua endpoint này.
- Không di chuyển, xóa, hoặc viết lại ảnh/bản ghi hiện hữu. Đường cũ
  `/static/uploads/...` được kiểm tra cả tham chiếu bệnh án lẫn CLS. Điều này
  cần thiết vì ảnh khám cũ có thể nằm lẫn trong `bai_viet` do lỗi category.
  Dữ liệu đọc ra được đổi URL sang `/medical-images/legacy/...`; URL cũ vẫn
  đi qua cùng kiểm tra quyền trong Flask. File bài viết thật không liên quan
  bệnh án vẫn giữ đường public.
- Nếu không thể tra cứu database để phân loại ảnh cũ nằm lẫn, Flask từ chối
  phục vụ thay vì trả file có thể chứa dữ liệu bệnh nhân. SVG cũ, URL bên ngoài,
  đường dẫn lạ hoặc ảnh vượt giới hạn cần được rà soát thủ công; không tự tải,
  chuyển đổi hoặc xóa chúng. Một thao tác upload nhiều ảnh bị lỗi giữa chừng
  có thể để lại file riêng tư chưa được tham chiếu; file này không được phục vụ.
  Tham chiếu URL tuyệt đối/encoded có thể trỏ tới cùng file local bị cách ly,
  không coi là ảnh public và cũng không tự suy đoán chủ sở hữu theo hostname cũ.

**Điều kiện triển khai:** Nginx/IIS/CDN không được phục vụ trực tiếp
`/static/uploads/` hoặc thư mục private, bỏ qua Flask. Cần chuyển toàn bộ URL
uploads về ứng dụng, kiểm tra các alias/static mapping khác và xử lý cache cũ
trước khi tuyên bố ảnh cũ đã được bảo vệ trên hệ thống triển khai. Chưa thay
cấu hình proxy/CDN hoặc xóa cache thật. Không thể thu hồi bản ảnh đã được tải
trước đây. Việc tra cứu ảnh legacy dùng truy vấn LIKE rồi so khớp đường dẫn
chính xác; cần đánh giá hiệu năng với quy mô dữ liệu thật.

## Giới hạn đầu vào ảnh

- Tối đa 8 MiB mỗi ảnh, 24 triệu pixel và tối đa 96 MiB request khi chưa cấu
  hình giới hạn nhỏ hơn; tối đa 10 ảnh trong luồng CLS. Ảnh hợp lệ được giải mã,
  xoay EXIF, giảm kích thước và ghi lại WebP, không lưu nguyên nội dung tải lên.
- SVG mới bị từ chối cho mọi category. Base64 được kiểm tra định dạng và giới
  hạn trước giải mã. Chuỗi tùy ý, `file:`, URL tương đối ngoài vùng cho phép,
  traversal hoặc ảnh không thuộc bệnh nhân đích bị từ chối.
- Tải ảnh ngoài mặc định tắt. Để bật, đặt `IMAGE_DOWNLOAD_ALLOWED_HOSTS` thành
  danh sách hostname HTTPS chính xác, phân cách bằng dấu phẩy. Không dùng wildcard.
  Chỉ cổng 443; không userinfo; không tự theo redirect; chỉ MIME raster được hỗ trợ.
  DNS phải trả toàn địa chỉ public, sau đó kết nối được ghim vào địa chỉ đã kiểm
  tra, giữ Host/SNI và xác minh chứng chỉ TLS theo hostname. Không dùng proxy môi
  trường hoặc `CERT_NONE`. Lỗi tải/TLS trả lỗi, không lưu URL gốc làm fallback.
- CA nội bộ hoặc host redirect cần cấu hình tin cậy/nguồn URL phù hợp; không
  khắc phục bằng cách tắt kiểm tra TLS. Chưa thử tải ảnh từ host Internet thật.

## Chạy và kiểm thử

Python và dependency dùng môi trường đã có, không cài thêm. Cấu hình khóa phiên
và cách chạy Website vẫn theo [startup_safety.md](startup_safety.md) và
[security_access.md](security_access.md). Chạy từ thư mục Website:

```powershell
python -B -m unittest discover -s tests -p test_clinical_media.py -v
python -B -m unittest discover -s tests -p test_security_access.py -v
python -B -m unittest discover -s tests -p test_startup_safety.py -v
```

Chỉ chạy các file này, không chạy discovery toàn bộ test cũ. Test dùng SQLite
chỉ trong RAM (xác minh từng connection), ảnh trong thư mục tạm, chặn pyodbc,
SMTP và worker ứng dụng. Network image import dùng mock, không tải Internet.
Luồng HTTP loopback kiểm tra đăng nhập, trang kết quả, API, file ảnh được phép
và việc từ chối ảnh sau khi rút trạng thái duyệt trong DB test.

Chưa nghiệm thu với SQL Server test, dữ liệu/đường ảnh legacy thực tế, proxy/CDN,
trình duyệt/thiết bị Flutter và host tải ảnh thật. Cần các môi trường đó được
xác nhận riêng trước khi chạy tích hợp; không dùng DB vận hành thay thế.
