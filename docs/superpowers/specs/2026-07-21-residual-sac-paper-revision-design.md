# Đặc tả chỉnh sửa paper về Residual SAC

## Mục tiêu

Viết lại `sn-article.tex` để bài báo chỉ trình bày hệ thống hiện tại: bài toán
giới hạn sức chứa cố định, hai lần giao hàng mỗi tuần và thuật toán Residual
SAC-AutoAlpha. Loại bỏ toàn bộ thí nghiệm một lần giao hàng trước đây, các phép
so sánh chính sách, số liệu, diễn giải và kết luận liên quan vì thiết kế thí
nghiệm đó không còn hợp lệ đối với phiên bản paper mới.

## Nguồn thông tin chính

- `ref_paper_v4_update.md` cung cấp nội dung kỹ thuật, số liệu, quy trình thí
  nghiệm, các điểm cần lưu ý và ánh xạ tài liệu tham khảo đã được kiểm tra.
- Mã nguồn hiện tại và các tệp kết quả thí nghiệm được trích dẫn trong tài liệu
  trên là nguồn gốc của các tuyên bố kỹ thuật và số liệu.
- Paper sẽ sử dụng ba hình: `figures/fig_mdp_architecture.png`,
  `figures/fig_service_inventory_frontier.png` và
  `figures/fig_residual_weight_ablation.png`.
- Không sử dụng `figures/fig_before_after_service.png` vì phần “Before” thuộc
  thiết kế cũ không hợp lệ.

## Phạm vi biên tập

Giữ nguyên mẫu LaTeX Springer Nature, thông tin tác giả, phần tuyên bố và cơ chế
quản lý tài liệu tham khảo. Chỉ giữ lại nội dung tổng quan nghiên cứu nếu nội
dung đó vẫn hỗ trợ đúng cho bài toán và phương pháp mới. Viết lại tiêu đề, tóm
tắt, giới thiệu, phương pháp, thiết lập thí nghiệm, kết quả, thảo luận, hạn chế,
kết luận, bảng biểu, công thức, chú thích hình, tham chiếu chéo và tuyên bố về
khả năng tái lập ở tất cả những nơi đang phụ thuộc vào thiết kế cũ.

Xóa mọi tuyên bố xem Random, Q-learning, SARSA, SAC một lần giao hàng hoặc
checkpoint SAC-AutoAlpha cũ là kết quả thực nghiệm hiện tại. Paper chỉ được
nhắc đến các phương pháp dạng bảng hoặc vanilla SAC trong phần tổng quan hay
bối cảnh kiến trúc; không được dùng phép so sánh cũ không hợp lệ làm bằng chứng.

## Câu chuyện khoa học mới

Vấn đề trung tâm là tính bất khả thi về mặt vật lý: lượng hàng đáp ứng nhu cầu
bảy ngày trong một tuần đại diện cần khoảng 50,39 m², trong khi diện tích bán
lẻ bị giới hạn ở 25 m². Can thiệp mang tính cấu trúc là tổ chức hai lần bổ sung
hàng mỗi tuần, vào ngày 0 và ngày 3. Cùng một action năm chiều biểu diễn lượng
bổ sung cho mỗi chuyến được sử dụng lại sau khi hoạt động bán hàng giữa tuần đã
giải phóng một phần diện tích.

Chính sách điều khiển là Residual SAC-AutoAlpha, không phải vanilla SAC. Action
đề xuất cuối cùng kết hợp một baseline đảm bảo mức độ phục vụ và đầu ra của
actor học được:

`a_final(s) = (1 - w) baseline(s) + w pi_theta(s)`,

với hệ số bao phủ bằng 1,20 và trọng số residual `w = 0,10`. Paper sẽ giải thích
phép chia hai trong baseline, hiệu chỉnh Jacobian cho log-probability của chính
sách affine, cơ chế co giãn action để tuân thủ giới hạn diện tích, cơ chế tự
động điều chỉnh entropy temperature, và sự khác biệt giữa lợi nhuận kế toán với
các penalty chỉ dùng để định hướng quá trình huấn luyện.

## Bằng chứng và hình minh họa

Phần phương pháp sử dụng hình kiến trúc MDP. Phần lựa chọn siêu tham số sử dụng
hình biên service–inventory và hình ablation trọng số residual để giải thích vì
sao hệ số bao phủ 1,20 và trọng số residual 0,10 được chọn. Hình before/after
không được đưa vào hoặc trích dẫn trong paper.

Bảng kết quả chính chỉ báo cáo đánh giá cuối trong 52 tuần với seed 42:

| Chỉ số | Kết quả hiện tại |
|---|---:|
| Thiếu hụt trung bình mỗi tuần | 4,75 đơn vị |
| Tổng thiếu hụt trong 52 tuần | 247 đơn vị |
| P95 thiếu hụt hằng tuần | 11,30 đơn vị |
| Thiếu hụt lớn nhất trong một tuần | 121 đơn vị |
| Số tuần vượt ngưỡng thiếu hụt 30 đơn vị | 2/52 |
| Fill rate tổng thể | 97,81% |
| Fill rate thấp nhất trong các SKU | 96,46% |
| Tồn kho trung bình cuối tuần | 1,60 ngày nhu cầu |
| Lợi nhuận kế toán trong 52 tuần | 72,216 tỷ VND |
| Diện tích cực đại sau mỗi lần giao hàng | Nhỏ hơn giới hạn cứng 25 m² |

Nội dung không được tự tạo các phép so sánh còn thiếu, khoảng bất định hoặc
tuyên bố quan hệ nhân quả mà thí nghiệm chưa chứng minh.

## Quy trình thí nghiệm và giới hạn của các tuyên bố

Mô tả rõ cách triển khai hiện tại tách seed huấn luyện 7201, các seed chọn
checkpoint 7301–7303 và seed báo cáo kết quả cuối 42. Phân biệt quy trình này
với các thế hệ thí nghiệm trước. Các seed 6201–6205 dùng để chọn hệ số bao phủ
và các seed 7601–7605 dùng để kiểm định trọng số residual phải được mô tả là
các tập seed hiệu chỉnh thực nghiệm, không phải hằng số lấy từ tài liệu bên
ngoài.

Kết quả cuối phải được trình bày như một kịch bản holdout duy nhất, không phải
ước lượng độ tin cậy đa seed. Paper phải nêu rõ hai tuần vẫn vượt ngưỡng thiếu
hụt; cùng một action được dùng cho cả hai lần giao hàng; một số đầu vào kinh tế
là giả định mô hình; forecast là tín hiệu có nhiễu; và môi trường 365 ngày được
đánh giá trên 52 tuần hoàn chỉnh.

## Kiểm chứng sau chỉnh sửa

Sau khi cập nhật paper, cần kiểm tra:

1. Không còn số liệu cũ hoặc tuyên bố thực chất nào dựa trên thiết kế một lần
   giao hàng.
2. Tên thuật toán được dùng nhất quán là Residual SAC-AutoAlpha.
3. Các đường dẫn hình tồn tại và hình before/after không xuất hiện trong mã
   nguồn LaTeX.
4. Các số liệu khớp với `ref_paper_v4_update.md`.
5. Các tham chiếu chéo LaTeX và khóa bibliography được phân giải đúng.
6. Tài liệu biên dịch thành công bằng bộ công cụ LaTeX có sẵn trong repository;
   nếu không có bộ công cụ phù hợp thì phải báo rõ giới hạn này.

## Ngoài phạm vi

Không chạy lại thí nghiệm, không thay đổi mã nguồn mô hình, không tạo số liệu
đa seed không có thật, không bổ sung baseline chưa được kiểm chứng và không
chỉnh sửa các tệp hình đã cung cấp.
