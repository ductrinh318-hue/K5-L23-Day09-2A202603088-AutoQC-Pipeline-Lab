from ..common import WARN, Issue, iou_xywh, parse_yolo_line
from ..model_cache import get_preds


def run(ds, cfg, preds=None):
    if preds is None:
        preds = get_preds(ds, cfg, "checker")

    so_cfg = cfg["second_opinion"]
    conf_thresh = so_cfg["conf"]
    min_area_px = so_cfg["min_area_px"]
    fp_conf = so_cfg["fp_conf"]
    iou_missing = so_cfg["iou_missing"]
    iou_match = so_cfg["iou_match"]
    iou_loose = so_cfg["iou_loose"]
    num_classes = len(ds.classes)

    issues = []
    for p in ds.image_files():
        stem = p.stem
        if stem not in preds:
            continue
        raw_lines = ds.read_label_lines(stem)
        if raw_lines is None:
            continue

        img_size = ds.image_size(stem)
        img_w, img_h = img_size if img_size is not None else (0, 0)

        # Lấy danh sách nhãn hợp lệ kèm số dòng gốc
        valid_labels = []  # (line_no, cls_id, (cx, cy, w, h))
        for line_no, text in raw_lines:
            try:
                cls_id, cx, cy, w, h = parse_yolo_line(text)
            except ValueError:
                continue
            if 0 <= cls_id < num_classes:
                valid_labels.append((line_no, cls_id, (cx, cy, w, h)))

        img_preds = preds[stem]

        # 1. Duyệt từng dự đoán đủ conf và diện tích
        for pred_item in img_preds:
            p_cls, p_conf, px, py, pw, ph = pred_item
            if p_conf < conf_thresh:
                continue
            if img_size is not None and (pw * img_w) * (ph * img_h) < min_area_px:
                continue

            p_box = (px, py, pw, ph)
            cands = []
            for _, l_cls, l_box in valid_labels:
                iou = iou_xywh(p_box, l_box)
                if iou >= iou_missing:
                    cands.append((iou, l_cls))

            if not cands:
                issues.append(
                    Issue(
                        "second_opinion",
                        WARN,
                        "POSSIBLE_MISSING",
                        stem,
                        f"model phát hiện lớp {p_cls} (conf={p_conf:.2f}) nhưng thiếu nhãn",
                        extra={"conf": round(float(p_conf), 4), "pred_class": int(p_cls)},
                    )
                )
                continue

            same_cls_ious = [iou for iou, l_cls in cands if l_cls == p_cls]
            if same_cls_ious:
                best_same_iou = max(same_cls_ious)
                if best_same_iou < iou_loose:
                    issues.append(
                        Issue(
                            "second_opinion",
                            WARN,
                            "POSSIBLE_LOOSE_BOX",
                            stem,
                            f"box lớp {p_cls} khớp lỏng với model (IoU={best_same_iou:.2f} < {iou_loose})",
                            extra={"conf": round(float(p_conf), 4), "iou": round(float(best_same_iou), 4)},
                        )
                    )
            else:
                best_diff_iou = max(iou for iou, _ in cands)
                if best_diff_iou >= iou_match:
                    issues.append(
                        Issue(
                            "second_opinion",
                            WARN,
                            "POSSIBLE_WRONG_CLASS",
                            stem,
                            f"nghi nhầm lớp: model dự đoán lớp {p_cls} (conf={p_conf:.2f}, IoU={best_diff_iou:.2f})",
                            extra={"conf": round(float(p_conf), 4), "iou": round(float(best_diff_iou), 4), "pred_class": int(p_cls)},
                        )
                    )

        # 2. Kiểm tra nhãn thừa (POSSIBLE_FALSE_POS) đối với mọi dự đoán có conf >= fp_conf (không lọc diện tích)
        fp_preds = [(item[2], item[3], item[4], item[5]) for item in img_preds if item[1] >= fp_conf]
        for line_no, l_cls, l_box in valid_labels:
            max_iou = max((iou_xywh(l_box, pb) for pb in fp_preds), default=0.0)
            if max_iou < iou_missing:
                issues.append(
                    Issue(
                        "second_opinion",
                        WARN,
                        "POSSIBLE_FALSE_POS",
                        stem,
                        f"box nhãn lớp {l_cls} không khớp dự đoán nào của model (max IoU={max_iou:.2f})",
                        line=line_no,
                        extra={"iou": round(float(max_iou), 4)},
                    )
                )

    return issues