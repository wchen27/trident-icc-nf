#!/usr/bin/env python
import sys

import numpy as np
from PIL import ImageCms
from trident.cli import main
from trident.wsi_objects.OpenSlideWSI import OpenSlideWSI

SRGB = ImageCms.createProfile("sRGB")
original_read_region = OpenSlideWSI.read_region
original_get_thumbnail = OpenSlideWSI.get_thumbnail


def to_srgb(wsi, img):
    if not hasattr(wsi, "icc"):
        profile = wsi.img.color_profile
        wsi.icc = None
        if profile is not None:
            wsi.icc = ImageCms.buildTransform(profile, SRGB, "RGB", "RGB", ImageCms.getDefaultIntent(profile))
            print(f"{wsi.name}: applying ICC profile {profile.profile.profile_description}", file=sys.stderr)
    return ImageCms.applyTransform(img, wsi.icc) if wsi.icc else img


def read_region(self, location, level, size, read_as="pil"):
    img = to_srgb(self, original_read_region(self, location, level, size, read_as="pil"))
    return np.array(img) if read_as == "numpy" else img


def get_thumbnail(self, size):
    return to_srgb(self, original_get_thumbnail(self, size))


OpenSlideWSI.read_region = read_region
OpenSlideWSI.get_thumbnail = get_thumbnail
sys.argv[0] = "trident"
sys.exit(main())
