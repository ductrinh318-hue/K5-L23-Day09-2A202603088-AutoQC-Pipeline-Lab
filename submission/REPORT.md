# Báo cáo Day 09 — Ngọ Đức Trinh, 2A202603088

## 1. Kết luận trước
Pipeline kết luận **HOLD** (mã thoát `10`, xuất bản nháp vào `submission/export/clean_v1/`): từ **224** ảnh thô đầu vào, bước nhận dữ liệu loại **21** ảnh lỗi/trùng/rò rỉ và giữ lại **203** ảnh sạch đưa vào dataset[cite: 25, 26, 27]. Sau khi máy tự sửa toàn bộ lỗi cú pháp (`0` lỗi bắt buộc còn lại) và người duyệt xử lý tối đa ngân sách **80/125** ảnh trong hàng đợi, vẫn còn **38/203** ảnh (**18,72%**) mang cảnh báo chưa được duyệt — vượt ngưỡng cho phép **10,00%** của cổng kiểm soát[cite: 25, 26, 30].

## 2. Lỗi và phân việc
Tổng hợp từ `02_error_list_v1` (21 lỗi cửa vào trên 224 ảnh thô; 36 lỗi bắt buộc và 153 cảnh báo trên 203 ảnh đã nhận)[cite: 26, 27, 28]:

| Mã lỗi | Số ảnh/dòng | Ai sửa (máy/người) | Vì sao |
|---|---:|---|---|
| `DUP_IMAGE_EXACT` | 8 ảnh (/224) | Máy (`remove_image`) | Trùng mã MD5 từng byte với ảnh khác, loại bỏ tự động hoàn toàn chính xác[cite: 8, 16, 27]. |
| `LEAK_TEST` | 5 ảnh (/224) | Máy (`remove_image`) | Trùng với tập `test`, bắt buộc loại để tránh rò rỉ dữ liệu làm sai lệch đánh giá[cite: 8, 16, 27]. |
| `BAD_SIZE` | 3 ảnh (/224) | Máy (`remove_image`) | Cạnh ngắn nhỏ hơn 250px (`img_0107`, `img_0113`, `img_0122`), không đạt chuẩn độ phân giải[cite: 27]. |
| `DUP_IMAGE_NEAR` | 3 ảnh (/224) | Máy (`remove_image`) | Trùng gần đúng theo pHash (`phash <= 6`), loại để tránh trùng lặp nội dung[cite: 16, 27]. |
| `CORRUPT_IMAGE` | 2 ảnh (/224) | Máy (`remove_image`) | File ảnh hỏng (`img_0010`, `img_0136`), không thể giải mã khi đọc[cite: 27]. |
| `BOX_OUT_OF_IMAGE` | 8 dòng (/203 ảnh) | Máy (`clip_box`) | Lỗi hình học rõ ràng, cắt tọa độ box về biên `[0, 1]` an toàn và giữ nguyên nhãn[cite: 16, 28]. |
| `DUP_BOX` | 7 dòng (/203 ảnh) | Máy (`drop_line`) | Hai box cùng lớp chồng lấn IoU > 0.9, xóa dòng lặp phía sau không làm mất thông tin[cite: 12, 16, 28]. |
| `BAD_CLASS_ID` | 6 dòng (/203 ảnh) | Máy (`drop_line`) | ID lớp ngoài phạm vi `0..3` (`93`, `7`, `4`, `-1`), không thể tự đoán lớp đúng nên xóa dòng[cite: 12, 16, 28]. |
| `BOX_ZERO` | 4 dòng (/203 ảnh) | Máy (`drop_line`) | Box có chiều rộng hoặc chiều cao bằng `0`, không có giá trị huấn luyện[cite: 12, 16, 28]. |
| `BAD_FORMAT` | 3 dòng (/203 ảnh) | Máy (`drop_line`) | Dòng thiếu cột hoặc chứa `nan`, lỗi cú pháp không thể khôi phục[cite: 16, 28]. |
| `BAD_CLASS_NAME` | 2 dòng (`data.yaml`) | Máy (`rename_classes`) | Viết hoa sai quy ước (`Person`, `Bus`), chuẩn hóa lại theo `cfg["classes"]`[cite: 16, 28]. |
| `MISSING_LABEL_FILE` | 6 ảnh (/203) | Người (`needs_label`) | Máy không được tự bịa nhãn hay tạo file rỗng (tránh nhầm thành ảnh nền), chuyển người gán mới[cite: 8, 16, 28]. |
| `POSSIBLE_MISSING` | 53 dòng (/203 ảnh) | Người (hàng đợi) | Model lớn nghi sót vật thể, nhưng có thể là báo động giả nên cần người xác nhận[cite: 8, 17, 28]. |
| `POSSIBLE_FALSE_POS` | 29 dòng (/203 ảnh) | Người (hàng đợi) | Box nhãn không khớp dự đoán của model, cần người kiểm tra xem là nhãn thừa hay model bỏ sót[cite: 8, 17, 28]. |
| `POSSIBLE_LOOSE_BOX` | 28 dòng (/203 ảnh) | Người (hàng đợi) | Box khớp cùng lớp nhưng IoU thấp (`0.30..0.48 < 0.5`), cần người căn chỉnh lại khung[cite: 8, 28]. |
| `POSSIBLE_WRONG_CLASS` | 18 dòng (/203 ảnh) | Người (hàng đợi) | Model dự đoán khác lớp với độ tin cậy cao, lỗi ngữ nghĩa cần mắt người phân biệt[cite: 8, 28]. |
| `EMPTY_LABEL` | 12 ảnh (/203) | Người (hàng đợi) | File nhãn rỗng (tăng lên 15 ảnh ở v2 sau khi xóa dòng lỗi), cần người phân biệt ảnh nền thật với ảnh bị xóa sạch nhãn[cite: 28, 29]. |
| `BOX_TINY` | 6 dòng (/203 ảnh) | Người (hàng đợi) | Cạnh ngắn < 12px (7 dòng ở v2), cần người quyết định giữ vật ở xa hay lọc bỏ theo guideline[cite: 28, 29]. |
| `CLASS_RARE` | 4 dòng (`<dataset>`) | Báo cáo thống kê | Xuất hiện ở v1 do các ID lớp rác (`-1, 4, 7, 93`); tự biến mất ở v2 sau khi `autofix` xóa các dòng sai ID[cite: 28, 29]. |
| `BOX_HUGE` | 3 dòng (/203 ảnh) | Người (hàng đợi) | Box chiếm > 95% diện tích ảnh, cần người kiểm tra xem vật thể chiếm toàn khung hình hay box bị kéo nhầm[cite: 28]. |

* **Cơ chế xếp ưu tiên hàng đợi (`05_review_queue.csv`) & hiệu quả ngân sách 80 ảnh:** Hàng đợi tính điểm ưu tiên theo trọng số mức độ nghiêm trọng của từng mã lỗi (`NEEDS_LABEL: 10`, `POSSIBLE_WRONG_CLASS: 3`, `POSSIBLE_MISSING: 2`, `POSSIBLE_FALSE_POS: 2`, `POSSIBLE_LOOSE_BOX: 1.5`, các lỗi hình học nhẹ `0.3–1.0`) kết hợp độ tự tin (`conf`) của model[cite: 7, 17]. Nhờ đó, toàn bộ **6** ảnh thiếu file nhãn bắt buộc và các ca nghi nhầm lớp nghiêm trọng được đẩy lên đầu hàng[cite: 7, 29, 30]. Với ngân sách **80/125** ảnh, người duyệt đã xử lý được **66/123** cảnh báo ngữ nghĩa thuộc nhóm `second_opinion` (giảm `POSSIBLE_WRONG_CLASS` từ 18 xuống 3, `POSSIBLE_MISSING` từ 53 xuống 13, `POSSIBLE_LOOSE_BOX` từ 28 xuống 20 và `POSSIBLE_FALSE_POS` từ 24 xuống 21) cùng **11/15** cảnh báo `EMPTY_LABEL`[cite: 29, 30].

## 3. Calibration (2 ngưỡng)
| Tham số | Khởi đầu | Đã chọn | Precision / Recall (trước → sau) | Lý do (đánh đổi) |
|---|---|---|---|---|
| `duplicates.phash_dist` | 2 | **6** | `DUP_IMAGE_NEAR`: `1.00 / 0.50` → `1.00 / 0.67` (F1 `0.67 → 0.80`)[cite: 22] | Tăng recall bắt ảnh trùng biến đổi mà vẫn giữ precision `1.00`, tránh xóa oan ảnh tốt ở bước tự động[cite: 22, 23]. |
| `second_opinion.conf` | 0.25 | **0.6** | `POSSIBLE_MISSING`: `0.50 / 1.00` → `0.57 / 1.00`<br>`POSSIBLE_WRONG_CLASS`: `0.56 / 0.83` → `0.62 / 0.83`[cite: 22] | Giữ nguyên toàn bộ recall bắt lỗi thiếu nhãn (`1.00`) và nhầm lớp (`0.83`), đồng thời tăng precision để giảm báo động giả cho hàng đợi 80 ảnh[cite: 22, 23]. |

* **Điểm calibration có thể đánh lừa:** Tập `data/calib/` chỉ có **39 ảnh** (6 ca `DUP_IMAGE_NEAR`), khiến điểm F1 đạt đỉnh tại `phash_dist = 16` (`P = 1.00, R = 0.83`)[cite: 22, 23]. Nếu tin theo F1 cao nhất trên `calib` và đặt `phash_dist = 16`, ngưỡng Hamming 25% số bit quá lỏng sẽ xóa nhầm hàng loạt ảnh đường phố có bố cục tương tự nhau trên tập `raw` 224 ảnh[cite: 2, 23]. Khi kiểm tra thực tế `01_intake.txt` với ngưỡng `6`, pipeline chỉ loại đúng **3** cặp ảnh gần trùng thực sự (`img_0076`–`img_0042` phash 0, `img_0143`–`img_0037` phash 0, `img_0223`–`img_0077` phash 6) và **8** ảnh trùng byte, không xóa nhầm ảnh khác cảnh[cite: 27].

## 4. Cửa chặn và điều pipeline KHÔNG bắt được
* **(a) Chứng minh cửa chặn hoạt động đúng:** Khi chạy `python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb`, không có ngân sách người duyệt nên **6** ảnh `MISSING_LABEL_FILE` (`img_0031`, `img_0053`, `img_0126`, `img_0135`, `img_0170`, `img_0219`) vẫn còn nguyên lỗi bắt buộc sau bước sửa tự động[cite: 26, 29]. Cửa chặn lập tức kết luận **`REWORK`**, trả về mã thoát **`20`**, và **không xuất** thư mục dataset `work/exp_nb`[cite: 26].
* **(b) Các điểm mù pipeline không bắt được:**
  1. **Ảnh trùng bị cắt cúp mạnh hoặc lật/xoay sâu (`phash_dist > 6`):** Trên `calib`, `phash_dist = 6` chỉ đạt recall `0.67` (bỏ sót 2/6 ảnh trùng biến đổi mạnh)[cite: 22]; trên `raw`, các ảnh bị crop sát vật thể hoặc thay đổi góc nhìn mạnh sẽ vượt qua ngưỡng `phash_dist = 6` mà không bị phát hiện.
  2. **Lỗi ngữ nghĩa nằm ngoài ngưỡng IoU hoặc cùng điểm mù với model `yolo26l`:** Ví dụ, các box lệch nhẹ có `IoU >= 0.5` (như `img_0021` sau duyệt còn `IoU = 0.49`) hoặc các vật thể bị che khuất một phần mà cả nhãn gốc lẫn `yolo26l` đều nhận diện nhầm giữa các lớp xe tương đồng (`car` / `truck` / `bus`) sẽ không phát sinh cảnh báo[cite: 23, 30].
  3. **Ảnh nền thật (`EMPTY_LABEL`) chưa được duyệt hết:** Trong 4 ảnh `EMPTY_LABEL` còn lại ở v3 (`img_0013`, `img_0097`, `img_0129`, `img_0192`), máy không thể tự phân biệt đó là ảnh không có đối tượng hay ảnh bị xóa mất toàn bộ box ở bước `autofix`[cite: 29, 30].

## 5. Train: raw vs clean (tùy chọn, chấm riêng)
Thí nghiệm huấn luyện công bằng trên Google Colab (T4 GPU) với cùng kiến trúc **`yolo26n.pt`**, `20` epochs, `batch=16`, `imgsz=640`, cùng tập validation `gold_val` (40 ảnh) và đánh giá trên cùng tập `test` (100 ảnh) qua `2` seed (`0` và `1`):

| biến thể | #ảnh train | số seed | map50 (TB ± độ lệch) | map50_95 (TB ± độ lệch) | precision (TB ± độ lệch) | recall (TB ± độ lệch) |
|---|---|---|---|---|---|---|
| raw | 224 | 2 | 0.726 ± 0.000 | 0.512 ± 0.004 | 0.764 ± 0.061 | 0.649 ± 0.028 |
| clean | 203 | 2 | 0.699 ± 0.025 | 0.486 ± 0.013 | 0.796 ± 0.050 | 0.596 ± 0.049 |

Chênh mAP50 (clean − raw) = **-0.027**.

* **So sánh chênh lệch với độ nhiễu & kết luận trung thực:**
  * Chênh lệch `mAP50 (clean − raw) = -0.027` (`0.6988` so với `0.7258`) xấp xỉ **độ lệch chuẩn giữa 2 seed của tập `clean` (`±0.0247` — trong đó `seed 0` đạt `0.6813` còn `seed 1` đạt `0.7163`)**.
  * Do đó, **không thể kết luận `clean` tốt hơn `raw` trên thang đo mAP50 tổng thể** (mức chênh nằm sát biên độ dao động ngẫu nhiên giữa các seed và theo hướng giảm); tuy nhiên `clean` giúp cải thiện **Precision trung bình từ `0.764` lên `0.796` (+0.032)** nhờ làm sạch nhãn nhiễu, đánh đổi bằng việc **Recall giảm từ `0.649` xuống `0.596`**.
* **Giả thuyết giải thích & cách kiểm chứng:**
  1. **Rò rỉ dữ liệu test (`LEAK_TEST`) tạo "metric đẹp giả" cho `raw`:** Bước `intake` phát hiện và loại bỏ **5 ảnh trong `raw` trùng trực tiếp với tập `test`** (`img_0049`, `img_0101`, `img_0167`, `img_0174`, `img_0221`). Khi huấn luyện trên `raw`, model học thuộc lòng 5 ảnh này nên điểm trên `test` bị thổi phồng giả tạo, trong khi `clean` đã loại bỏ rò rỉ nên phản ánh đúng năng lực tổng quát hóa thực tế. *Cách kiểm chứng:* Đánh giá lại cả hai model trên 95 ảnh `test` còn lại sau khi loại 5 ảnh bị rò rỉ.
  2. **Lớp `truck` ít mẫu & dataset `clean` vẫn đang ở trạng thái `HOLD`:** Số ảnh train của `clean` giảm từ 224 xuống 203 ảnh (mất 21 ảnh), và vẫn còn **38/203 ảnh chưa qua người duyệt** (gồm 13 cảnh báo `POSSIBLE_MISSING` và 20 `POSSIBLE_LOOSE_BOX`). Sự thiếu hụt mẫu thể hiện rõ nhất ở lớp ít dữ liệu là **`truck`** (`AP50` của `clean` giảm từ `0.648` ở `raw` xuống `0.536`, kéo tụt Recall chung). *Cách kiểm chứng:* Duyệt nốt 38 ảnh còn cảnh báo để đạt chuẩn `Release`, bổ sung thêm dữ liệu lớp `truck`, và train với nhiều seed hơn (`3–5` seed) ở 50 epochs để giảm phương sai.

## 6. Quyết định và ghi chú AI
* **(a) Quyết định cuối & điều kiện chuyển sang Release:** Chấp nhận kết luận **`HOLD`** (`18,72%` ảnh còn cảnh báo chưa duyệt, vượt ngưỡng `10,00%`)[cite: 25]. Để lô dữ liệu đạt **`Release`**, cần bổ sung ngân sách duyệt thêm tối thiểu **18 ảnh** ưu tiên cao nhất trong số 38 ảnh còn cảnh báo (đưa số ảnh chưa duyệt xuống còn `<= 20/203` ảnh, tức `<= 9,85% < 10,00%`)[cite: 25].
* **(b) Ghi chú sử dụng AI:**
  * *Prompt chính:* Yêu cầu viết 4 module (`label_format.py`, `gate.py`, `autofix.py`, `second_opinion.py`) tuân thủ đúng signature, đọc ngưỡng từ `cfg`, giữ nguyên chỉ số dòng gốc khi xóa/cắt box và xử lý đầy đủ các ca biên trong bộ `pytest`[cite: 12, 16, 17, 19].
  * *Cách kiểm code AI:* Đọc đối chiếu từng dòng với docstring và `common.py`, chạy toàn bộ 79 unit test (`python -m pytest -q`), chạy `make calibrate` và kiểm tra chéo báo cáo `01_intake.txt`, `03_fixes.csv`, `07_error_list_v3.txt` trên dữ liệu `raw`[cite: 21, 22, 27, 30].
  * *1 lần AI sai/cần chỉnh:* Ở bản nháp đầu của `autofix.py`, việc ghi lại file nhãn sau khi `clip_box` có thể làm thay đổi định dạng số thập phân dù tọa độ không tràn, dễ vi phạm tính idempotent ở lần chạy thứ 2; đã sửa bằng cách chỉ ghi lại dòng khi tọa độ thực sự thay đổi sau khi cắt biên[cite: 16].