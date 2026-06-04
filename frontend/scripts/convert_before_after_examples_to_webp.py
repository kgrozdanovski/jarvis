#!/usr/bin/env python3
from pathlib import Path

from PIL import Image


FRONTEND_ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = FRONTEND_ROOT / "public" / "images" / "before_and_after_examples"


def image_has_alpha(image: Image.Image) -> bool:
    if image.mode in ("RGBA", "LA"):
        return True

    return image.mode == "P" and "transparency" in image.info


def normalize_for_webp(image: Image.Image) -> Image.Image:
    if image_has_alpha(image):
        return image.convert("RGBA")

    if image.mode != "RGB":
        return image.convert("RGB")

    return image.copy()


def convert_png(source_path: Path) -> Path:
    target_path = source_path.with_suffix(".webp")

    with Image.open(source_path) as image:
        output = normalize_for_webp(image)
        save_options = {
            "format": "WEBP",
            "lossless": True,
            "quality": 100,
            "method": 6,
            "exact": True,
        }

        icc_profile = image.info.get("icc_profile")
        exif = image.info.get("exif")

        if icc_profile:
            save_options["icc_profile"] = icc_profile

        if exif:
            save_options["exif"] = exif

        output.save(target_path, **save_options)

    if not target_path.exists() or target_path.stat().st_size == 0:
        raise RuntimeError(f"Failed to write {target_path}")

    source_path.unlink()
    return target_path


def main() -> None:
    if not IMAGE_DIR.exists():
        raise FileNotFoundError(f"Image directory does not exist: {IMAGE_DIR}")

    png_paths = sorted(IMAGE_DIR.rglob("*.png"))

    for source_path in png_paths:
        target_path = convert_png(source_path)
        print(f"{source_path.relative_to(FRONTEND_ROOT)} -> {target_path.relative_to(FRONTEND_ROOT)}")

    print(f"Converted {len(png_paths)} PNG file(s) to lossless WebP.")


if __name__ == "__main__":
    main()
