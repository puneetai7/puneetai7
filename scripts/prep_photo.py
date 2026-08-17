"""Turn a raw photo into a high-contrast, white-backed portrait for ASCII conversion.

    python scripts/prep_photo.py source-photo.jpg [--crop L,T,R,B]

--crop takes fractions of the original frame (default is a head-and-torso crop
tuned for a centered standing shot). Steps: crop, drop the background to pure
white, boost local contrast (CLAHE when OpenCV is present, autocontrast
otherwise), then composite onto white and save data/prepped-photo.png.
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "prepped-photo.png"
OUT_MASK = ROOT / "data" / "prepped-alpha.png"

# Portrait target: tall-ish, matching the 370px README column.
TARGET = (900, 1160)


def remove_background(img):
    """Return (subject on white, alpha matte).

    The matte is kept, not just applied: make_ascii_svg.py needs to know which
    pixels are subject so it can stretch the tonal range over the subject alone.
    A photo shot on a light backdrop otherwise leaves skin crammed into the top
    fifth of the range, and the face renders hollow.
    """
    try:
        from rembg import remove
    except ImportError:
        arr = np.asarray(img.convert("RGB")).astype(np.float32)
        lum = arr.mean(axis=2)
        bg = lum > 200
        arr[bg] = 255.0
        mask = Image.fromarray(((~bg) * 255).astype(np.uint8), mode="L")
        return Image.fromarray(arr.astype(np.uint8)), mask

    cut = remove(img)  # RGBA with the subject isolated
    mask = cut.getchannel("A")
    white = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    return Image.alpha_composite(white, cut).convert("RGB"), mask


def boost_contrast(img):
    try:
        import cv2
    except ImportError:
        return ImageOps.autocontrast(img, cutoff=1)

    lab = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(l)
    return Image.fromarray(cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2RGB))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    # Head-and-shoulders by default: at README size the art is only ~84 columns
    # wide, so a full-torso crop leaves too few characters for the face.
    ap.add_argument("--crop", default="0.38,0.04,0.62,0.56",
                    help="L,T,R,B as fractions of the source frame")
    args = ap.parse_args()

    img = Image.open(args.photo).convert("RGB")
    w, h = img.size
    l, t, r, b = (float(v) for v in args.crop.split(","))
    img = img.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    img = ImageOps.fit(img, TARGET, method=Image.LANCZOS)

    img, mask = remove_background(img)
    img = boost_contrast(img)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    mask.save(OUT_MASK)
    print(f"wrote {OUT.relative_to(ROOT)} and {OUT_MASK.name} "
          f"({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
