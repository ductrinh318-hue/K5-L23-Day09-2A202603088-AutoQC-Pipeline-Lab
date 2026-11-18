from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line


def run(ds, cfg):
    lf_cfg = cfg["label_format"]
    overflow_tol = lf_cfg["overflow_tol"]
    min_box_px = lf_cfg["min_box_px"]
    max_box_frac = lf_cfg["max_box_frac"]
    dup_box_iou = lf_cfg["dup_box_iou"]
    num_classes = len(ds.classes)

    issues = []
    for p in ds.image_files():
        stem = p.stem
        lines = ds.read_label_lines(stem)
        if lines is None:
            continue

        img_size = ds.image_size(stem)
        seen_boxes = []  # lưu (cls_id, cx, cy, w, h) của các dòng hợp lệ trước đó

        for line_no, text in lines:
            try:
                cls_id, cx, cy, w, h = parse_yolo_line(text)
            except ValueError as e:
                issues.append(Issue("label_format", ERROR, "BAD_FORMAT", stem, f"dòng sai định dạng: {e}", line=line_no))
                continue

            if not (0 <= cls_id < num_classes):
                issues.append(Issue("label_format", ERROR, "BAD_CLASS_ID", stem, f"id lớp không hợp lệ: {cls_id}", line=line_no))
                continue

            if w <= 0 or h <= 0:
                issues.append(Issue("label_format", ERROR, "BOX_ZERO", stem, f"box có kích thước <= 0 (w={w}, h={h})", line=line_no))
                continue

            # Kiểm tra tràn biên
            x1, y1 = cx - w / 2.0, cy - h / 2.0
            x2, y2 = cx + w / 2.0, cy + h / 2.0
            overflow = max(0.0 - x1, 0.0 - y1, x2 - 1.0, y2 - 1.0)
            if overflow > overflow_tol:
                issues.append(
                    Issue(
                        "label_format",
                        ERROR,
                        "BOX_OUT_OF_IMAGE",
                        stem,
                        f"box tràn khỏi ảnh mức {overflow:.4f} > {overflow_tol}",
                        line=line_no,
                        extra={"overflow": round(overflow, 6)},
                    )
                )

            # Kiểm tra trùng box cùng lớp với dòng trước đó
            curr_box = (cx, cy, w, h)
            for prev_cls, prev_box in seen_boxes:
                if prev_cls == cls_id and iou_xywh(prev_box, curr_box) > dup_box_iou:
                    issues.append(
                        Issue(
                            "label_format",
                            ERROR,
                            "DUP_BOX",
                            stem,
                            f"trùng lặp box cùng lớp {cls_id} (IoU > {dup_box_iou})",
                            line=line_no,
                        )
                    )
                    break
            seen_boxes.append((cls_id, curr_box))

            # Cảnh báo kích thước
            if img_size is not None:
                img_w, img_h = img_size
                short_side_px = min(w * img_w, h * img_h)
                if short_side_px < min_box_px:
                    issues.append(
                        Issue(
                            "label_format",
                            WARN,
                            "BOX_TINY",
                            stem,
                            f"cạnh ngắn box {short_side_px:.1f}px < {min_box_px}px",
                            line=line_no,
                        )
                    )

            if w * h > max_box_frac:
                issues.append(
                    Issue(
                        "label_format",
                        WARN,
                        "BOX_HUGE",
                        stem,
                        f"diện tích box {w * h:.3f} > {max_box_frac}",
                        line=line_no,
                    )
                )

    return issues