from ..common import ERROR, WARN


def decide(issues, image_stems, cfg, reviewed=frozenset()):
    stem_set = set(image_stems)
    reviewed_set = set(reviewed)
    n_images = len(stem_set)
    hold_thresh = cfg["gate"]["warn_ratio_hold"]

    errors = [i for i in issues if i.severity == ERROR]
    n_errors = len(errors)

    warn_images = {
        i.image
        for i in issues
        if i.severity == WARN and i.image in stem_set and i.image not in reviewed_set
    }
    n_warn_images = len(warn_images)
    warn_ratio = round(n_warn_images / n_images, 4) if n_images > 0 else 0.0

    reasons = []
    if n_errors > 0:
        decision = "Rework"
        reasons.append(f"Còn {n_errors} lỗi bắt buộc (ERROR) chưa được xử lý.")
    elif warn_ratio >= hold_thresh:
        decision = "Hold"
        reasons.append(
            f"Tỉ lệ ảnh còn cảnh báo chưa duyệt là {warn_ratio:.2%} ({n_warn_images}/{n_images} ảnh) >= ngưỡng {hold_thresh:.2%}."
        )
    else:
        decision = "Release"
        reasons.append(
            f"Không còn lỗi bắt buộc và tỉ lệ ảnh cảnh báo chưa duyệt là {warn_ratio:.2%} ({n_warn_images}/{n_images} ảnh) < ngưỡng {hold_thresh:.2%}."
        )

    return {
        "decision": decision,
        "n_errors": n_errors,
        "n_warn_images": n_warn_images,
        "n_images": n_images,
        "warn_ratio": warn_ratio,
        "reasons": reasons,
    }