from collections import defaultdict

import yaml

from ..common import ERROR, parse_yolo_line

DROP_CODES = {"BAD_FORMAT", "BAD_CLASS_ID", "BOX_ZERO", "DUP_BOX"}
REMOVE_IMAGE_CODES = {"DUP_IMAGE_EXACT", "DUP_IMAGE_NEAR", "LEAK_TEST", "CORRUPT_IMAGE", "BAD_SIZE"}


def fix(ds, issues, cfg):
    fixes = []
    errors = [i for i in issues if i.severity == ERROR]

    # 1. Xử lý lỗi cấp dataset (BAD_CLASS_NAME)
    if any(i.code == "BAD_CLASS_NAME" for i in errors):
        before_names = ds.yaml_names()
        target_classes = list(cfg["classes"])
        yaml_data = {}
        if ds.yaml_path.exists():
            yaml_data = yaml.safe_load(ds.yaml_path.read_text(encoding="utf-8")) or {}
        yaml_data["nc"] = len(target_classes)
        yaml_data["names"] = target_classes
        ds.yaml_path.parent.mkdir(parents=True, exist_ok=True)
        ds.yaml_path.write_text(yaml.safe_dump(yaml_data, sort_keys=False, allow_unicode=True), encoding="utf-8")
        fixes.append(
            {
                "image": "data.yaml",
                "line": "",
                "action": "rename_classes",
                "before": str(before_names),
                "after": str(target_classes),
            }
        )

    # 2. Xử lý xoá ảnh hỏng / trùng / rò rỉ
    removed_stems = set()
    for i in errors:
        if i.code in REMOVE_IMAGE_CODES and i.image not in removed_stems:
            img_p = ds.image_path(i.image)
            lbl_p = ds.label_path(i.image)
            existed = False
            if img_p and img_p.exists():
                img_p.unlink()
                existed = True
            if lbl_p.exists():
                lbl_p.unlink()
                existed = True
            if existed:
                removed_stems.add(i.image)
                fixes.append(
                    {
                        "image": i.image,
                        "line": "",
                        "action": "remove_image",
                        "before": i.code,
                        "after": "(đã xoá ảnh và nhãn)",
                    }
                )

    # 3. Ghi nhận ảnh thiếu file nhãn (chuyển người gán, không tạo file rỗng)
    needs_label_seen = set()
    for i in errors:
        if i.code == "MISSING_LABEL_FILE" and i.image not in removed_stems and i.image not in needs_label_seen:
            needs_label_seen.add(i.image)
            fixes.append(
                {
                    "image": i.image,
                    "line": "",
                    "action": "needs_label",
                    "before": "(không có file)",
                    "after": "chuyển người gán",
                }
            )

    # 4. Gom lỗi theo từng file nhãn và sửa một lần để giữ nguyên số dòng gốc
    file_ops = defaultdict(lambda: {"drop": set(), "clip": set()})
    for i in errors:
        if i.image in removed_stems or i.line is None:
            continue
        if i.code in DROP_CODES:
            file_ops[i.image]["drop"].add(i.line)
        elif i.code == "BOX_OUT_OF_IMAGE":
            file_ops[i.image]["clip"].add(i.line)

    for stem, ops in file_ops.items():
        lbl_p = ds.label_path(stem)
        if not lbl_p.exists():
            continue

        raw_lines = lbl_p.read_text(encoding="utf-8", errors="replace").splitlines()
        new_lines = []
        changed = False

        for line_no, text in enumerate(raw_lines, 1):
            if line_no in ops["drop"]:
                changed = True
                fixes.append(
                    {
                        "image": stem,
                        "line": line_no,
                        "action": "drop_line",
                        "before": text,
                        "after": "",
                    }
                )
                continue

            if line_no in ops["clip"]:
                try:
                    cls_id, cx, cy, w, h = parse_yolo_line(text)
                    x1 = max(0.0, min(1.0, cx - w / 2.0))
                    y1 = max(0.0, min(1.0, cy - h / 2.0))
                    x2 = max(0.0, min(1.0, cx + w / 2.0))
                    y2 = max(0.0, min(1.0, cy + h / 2.0))
                    nw, nh = x2 - x1, y2 - y1
                    if nw <= 1e-6 or nh <= 1e-6:
                        changed = True
                        fixes.append(
                            {
                                "image": stem,
                                "line": line_no,
                                "action": "drop_line",
                                "before": text,
                                "after": "",
                            }
                        )
                        continue
                    ncx, ncy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                    new_text = f"{cls_id} {ncx:.6f} {ncy:.6f} {nw:.6f} {nh:.6f}"
                    if new_text != text:
                        changed = True
                        fixes.append(
                            {
                                "image": stem,
                                "line": line_no,
                                "action": "clip_box",
                                "before": text,
                                "after": new_text,
                            }
                        )
                    new_lines.append(new_text)
                    continue
                except ValueError:
                    pass

            new_lines.append(text)

        if changed:
            content = "\n".join(new_lines) + ("\n" if new_lines else "")
            lbl_p.write_text(content, encoding="utf-8")

    return fixes