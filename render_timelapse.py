import os
import argparse
from argparse import RawTextHelpFormatter
import subprocess
import tempfile
from datetime import datetime

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    Image = None




# ============================================================
# DEFAULT VALUES
# ============================================================
WATERMARK_DEFAULT_POSITION = "bottom-left" # SEE: WATERMARK_POSITIONS
WATERMARK_DEFAULT_SIZE = 0.12 # SEE: WATERMARK_SIZES
WATERMARK_DEFAULT_ALPHA = 0.6 # SEE: WATERMARK_TRANSPARENCY
# ============================================================
# IMAGE DATA EXTRACTION
# ============================================================
def get_exif_date_from_filelist(filelist_path, verbose_flag = False):
    """
    Reads the first 'file' entry in an FFmpeg concat list
    and extracts DateTimeOriginal from EXIF.

    Returns YYYY-MM-DD or None.
    """
    # if Image is None:
        # return None

    first_image = None

    with open(filelist_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("file"):
                first_image = line.split("'", 2)[1]
                break

    if not first_image or not os.path.exists(first_image):
        if verbose_flag:
            print("Can't find first image! (get_exif_date_from_filelist)")
        return None

    try:
        img = Image.open(first_image)
        exif = img._getexif()
        if not exif:
            if verbose_flag:
                print("No exif data! (get_exif_date_from_filelist)")
            return None

        for tag, value in exif.items():
            if TAGS.get(tag) == "DateTimeOriginal":
                dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                return dt.strftime("%Y-%m-%d")
    except Exception as e:
        if verbose_flag:
            print("get_exif_date_from_filelist failed:")
            print(type(e).__name__, e)
        return None

# def get_first_image_size_from_filelist(filelist_path):
    # first_image = None
    # with open(filelist_path, "r", encoding="utf-8") as f:
        # for line in f:
            # if line.startswith("file"):
                # first_image = line.split("'", 2)[1]
                # break
    # if not first_image or not os.path.exists(first_image) or Image is None:
        # return None
    # try:
        # im = Image.open(first_image)
        # return im.size  # (w,h)
    # except Exception:
        # return None
        
def get_first_image_size_from_filelist(filelist_path, verbose_flag = False):
    first_image = None

    with open(filelist_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("file"):
                first_image = line.split("'", 2)[1]
                break

    if not first_image or not os.path.exists(first_image) or Image is None:
        return None

    try:
        im = Image.open(first_image)
        w, h = im.size

        exif = im._getexif()
        if exif:
            orientation = exif.get(274)  # EXIF Orientation tag

            # Orientations that imply 90° or 270° rotation
            if orientation in (5, 6, 7, 8):
                w, h = h, w
        
        if verbose_flag:
            print(f"Image dimensions found: w = {w},h = {h}")
        return w, h

    except Exception:
        return None        

# ============================================================
# LOOK PRESETS
# ============================================================
LOOK_PRESETS = {
    # Clean, natural Milky Way look
    # Good starting point for most astro landscapes
    "milkyway": {
        "gamma": 1.30,       # Midtone lift (≈ +0.3 EV)
        "contrast": 1.15,    # Restores punch after gamma
        "saturation": 1.10,  # Gentle color boost
        "clarity": 0.30      # Subtle micro-contrast (safe)
    },

    # Aurora-friendly look
    # Preserves color gradients and motion
    "aurora": {
        "gamma": 1.35,       # Slightly brighter midtones
        "contrast": 1.15,    # Softer contrast for glow
        "saturation": 1.15,  # Aurora colors benefit here
        "clarity": 0.30
    },
    # Aurora-booster look
    # Preserves color gradients and motion
    "aurora-boosted": {
        "gamma": 1.42,        # brighter midtones
        "contrast": 1.35,    # Softer contrast for glow
        "saturation": 1.3,   # Powerful colours
        "clarity": 0.35
    }
}


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Render timelapse video from FFmpeg concat file list",
        formatter_class=RawTextHelpFormatter
    )

    # --- Required ---
    parser.add_argument("filelist", help="FFmpeg concat file list (.txt)")

    # --- Output ---
    parser.add_argument("--name", help="Base output name (default: file list name)")
    parser.add_argument("--outdir", default="Timelapses", help="Output directory")

    # --- Video basics ---
    parser.add_argument("--orientation", choices=["landscape", "vertical"], default="landscape",
                        help="Output orientation: landscape (16:9) or vertical (9:16)")

    parser.add_argument("--resolution", choices=["1080p", "2160p", "HD", "4k"], default="1080p",
                        help="Resolution tier. Landscape: HD = 1080p = 1920x1080, 4k = 2160p = 3840x2160. "
                             "Vertical: HD= 1080p = 1080x1920, 4k= 2160p = 2160x3840.")

    parser.add_argument("--aspect-mode", choices=["auto", "scale", "crop", "pad"], default="auto",
                        help="How to fit source into output frame. "
                             "auto: landscape->scale, vertical->crop. "
                             "scale: force exact WxH (distorts if AR differs). "
                             "crop: preserve AR, fill frame by cropping. "
                             "pad: preserve AR, fit inside frame with bars.")

    parser.add_argument("--crop-bias", choices=["upper", "center", "lower"], default="center",
                        help="Crop bias for crop mode: upper/center/lower")

    parser.add_argument("--debug-overlay", action="store_true",
                        help="Burn frame number + filename on video (for debugging)")

    parser.add_argument("--fps", type=int, default=24)    
    

    # --- Timing ---
    parser.add_argument(
        "--slowdown", type=float, default=1.0,
        help="Playback slowdown (1.5 = 50%% slower). Use 1.2–1.6 for astro."
    )

    # --- Watermark ---
    parser.add_argument("--watermark", help="Path to watermark PNG")
    parser.add_argument("--wm-position", default = WATERMARK_DEFAULT_POSITION, type = str, help="Watermark position (top-left, top-right, bottom-left, bottom-right, center, center-bottom)")
    parser.add_argument("--wm-size", default = WATERMARK_DEFAULT_SIZE, help="Watermark sizes (small, default, large)")
    parser.add_argument("--wm-alpha", default = WATERMARK_DEFAULT_ALPHA, help="Watermark alpha / transparency (weak, default, strong)")
    
    
    
    # --- Look / Color ---
    parser.add_argument(
        "--look", choices=["milkyway", "aurora", "aurora-boosted"],
        help="Apply recommended astro look preset. \n"
        "PRESET DETAILS: \n"
        "\n"
        "'milkyway': \n"
        "    gamma = 1.30,       # Midtone lift (≈ +0.3 EV) \n"
        "    contrast = 1.15,    # Restores punch after gamma \n"
        "    saturation = 1.10,  # Gentle color boost \n"
        "    clarity = 0.30      # Subtle micro-contrast (safe) \n"
        " \n"
        "'aurora':               # Aurora-friendly look: Preserves color gradients and motion \n"      
        "    gamma = 1.35,       # Slightly brighter midtones \n"
        "    contrast = 1.15,    # Softer contrast for glow \n"
        "    saturation = 1.15,  # Aurora colors benefit here \n"
        "    clarity = 0.30 \n"
        "\n"
        "'aurora-boosted': \n" 
        "    gamma = 1.42,        # brighter midtones \n"
        "    contrast = 1.35,    # Softer contrast for glow \n"
        "    saturation = 1.3,   # Powerful colours \n"
        "    clarity = 0.35 \n"
        "\n"
    )






    parser.add_argument(
        "--gamma", type=float, default=1.0,
        help="Gamma lift (1.2–1.25 recommended for astro)"
    )
    parser.add_argument(
        "--contrast", type=float, default=1.0,
        help="Contrast multiplier (1.1–1.25 recommended)"
    )
    parser.add_argument(
        "--saturation", type=float, default=1.0,
        help="Color saturation (1.05–1.15 recommended)"
    )
    parser.add_argument(
        "--clarity", type=float, default=0.0,
        help="Micro-contrast via unsharp mask (0.2–0.4 safe)"
    )

    # --- Extras ---
    parser.add_argument("--boomerang", action="store_true")

    parser.add_argument(
        "--use-exif-date", action="store_true", default=False,
        help="Prefix output filename with EXIF date (YYYY-MM-DD)"
    )

    # --- Encoding ---
    parser.add_argument("--crf", type=int, default=20, help="ffmpeg encoding eption - see ffmpeg docs for more")
    parser.add_argument("--preset", default="slow", help="ffmpeg encoding eption - see ffmpeg docs for more")

    # --- Debug ---
    parser.add_argument("--dry-run", action="store_true", help="Print the final ffmpeg comand without executing")
    parser.add_argument("--verbose", action="store_true", help="For debugging perposes")


    args = parser.parse_args()
    
    
    
    VERBOSE = args.verbose
    if VERBOSE:
        print(
        "\n\n"
        "Verbose flag enabled! \n\n"
        "Printing `args`: \n"
        f"{args}"
        " \n"
        )


    # Default aspect-mode behavior:
    # - landscape: scale is fine (minimal AR mismatch)
    # - vertical: crop is usually wanted for social (no bars, no distortion)
    if args.aspect_mode == "auto":
        args.aspect_mode = "crop" if args.orientation == "vertical" else "scale"


    # ============================================================
    # Warn of Orientation Mismatch
    # ============================================================    
    src_size = get_first_image_size_from_filelist(args.filelist, verbose_flag = VERBOSE)
    if src_size:
        src_w, src_h = src_size
        src_is_vertical = src_h > src_w
        out_is_vertical = (args.orientation == "vertical")

        if out_is_vertical and not src_is_vertical:
            print("WARNING: Output is vertical but source images are landscape. "
                  "This is allowed (will crop/pad/scale per --aspect-mode), but edges may be lost.")
        if (not out_is_vertical) and src_is_vertical:
            print("WARNING: Output is landscape but source images are vertical. "
                  "This is allowed, but edges may be lost depending on --aspect-mode.")


    # ============================================================
    # Apply look preset (unless user overrides values)
    # ============================================================
    if args.look:
        preset = LOOK_PRESETS[args.look]
        if args.gamma == 1.0:
            args.gamma = preset["gamma"]
        if args.contrast == 1.0:
            args.contrast = preset["contrast"]
        if args.saturation == 1.0:
            args.saturation = preset["saturation"]
        if args.clarity == 0.0:
            args.clarity = preset["clarity"]

  
    # ============================================================
    # Output naming
    # ============================================================
    base_name = args.name or os.path.splitext(os.path.basename(args.filelist))[0]

    if args.use_exif_date:
        date_str = get_exif_date_from_filelist(args.filelist, verbose_flag = VERBOSE)
        if date_str:
            base_name = f"{date_str}_{base_name}"
            if VERBOSE:
                print(f"Date found: {date_str}")
                print(f"Base name: {base_name}")

    suffix = [args.resolution]

    if args.look:
        suffix.append(args.look)

    if args.slowdown != 1.0:
        suffix.append(f"slow{args.slowdown}x")

    if args.boomerang:
        suffix.append("boom")

    # if args.watermark:
        # suffix.append("wm")
        
    if args.orientation == "vertical":
        suffix.append("vertical")

    if args.wm_position:
        if VERBOSE:
            print(f"Watermark position: {args.wm_position}") 
        suffix.append(f"WM-{args.wm_position}")
    elif args.watermark:
        suffix.append("wm")
        print("ELSE IF ACTIVATED!") # !DEL
    


    suffix_str = "_".join(suffix)

    os.makedirs(args.outdir, exist_ok=True)

    output_path = os.path.join(
        args.outdir,
        f"{base_name}_{suffix_str}.mp4"
    )

    # ============================================================
    # Resolution
    # ============================================================
    
    # scale = "1920:1080" if args.resolution in ("1080p", "HD") else "3840:2160"
    
    # if args.orientation == "landscape":
        # if args.resolution in ["1080p", "HD"):
            # scale = "1920:1080"
        # else:  # 4k
            # scale = "3840:2160"

    # else:  # vertical
        # if args.resolution in ["1080p", "HD"):
            # scale = "1080:1920"      # Full HD vertical (Reels / Shorts)
        # else:  # 4k vertical
            # scale = "2160:3840"      # 4K vertical

    # ============================================================
    # Resolution targets (W,H)
    # ============================================================
    if args.orientation == "landscape":
        W, H = (1920, 1080) if args.resolution in ["1080p", "HD"] else (3840, 2160)
    else:
        W, H = (1080, 1920) if args.resolution in ["1080p", "HD"] else (2160, 3840)


    # ============================================================
    # Filters (ORDER MATTERS)
    # ============================================================
    
    # filters = [
        # f"scale={scale}:flags=lanczos"
    # ]
 
    filters = []

    if args.aspect_mode == "scale":
        # WARNING: This forces exact WxH and will distort if source AR doesn't match target AR.
        filters.append(f"scale={W}:{H}:flags=lanczos")

    elif args.aspect_mode == "pad":
        # Fit inside WxH while preserving AR, add bars to fill.
        # Uses min() scale so both dimensions fit, then pads.
        filters.append(
            f"scale=iw*min({W}/iw\\,{H}/ih):ih*min({W}/iw\\,{H}/ih),"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2"
        )

    elif args.aspect_mode == "crop":
        # Fill WxH while preserving AR, cropping overflow.
        # Uses max() scale so both dimensions cover, then crops.
        y_expr = {
            "upper": "0",
            "center": "(ih-oh)/2",
            "lower": "ih-oh"
        }[args.crop_bias]

        filters.append(
            f"scale=iw*max({W}/iw\\,{H}/ih):ih*max({W}/iw\\,{H}/ih),"
            f"crop={W}:{H}:(iw-ow)/2:{y_expr}"
        )
    else:
        # Should not happen due to argparse choices, but safe fallback
        filters.append(f"scale={W}:{H}:flags=lanczos") 
    
    

    # Tonal & color shaping
    if any([
        args.gamma != 1.0,
        args.contrast != 1.0,
        args.saturation != 1.0
    ]):
        filters.append(
            f"eq=gamma={args.gamma}:contrast={args.contrast}:saturation={args.saturation}"
        )

    # Clarity / micro-contrast
    if args.clarity > 0:
        filters.append(f"unsharp=3:3:{args.clarity}")

    # Speed
    if args.slowdown != 1.0:
        filters.append(f"setpts={args.slowdown}*PTS")

    if args.debug_overlay:
        # Shows frame number and filename. %{filename} should be basename for file inputs.
        # If it shows full paths in your build, we can strip in Python by generating a debug filelist.
        filters.append(
            "drawtext=fontcolor=white:fontsize=24:"
            "text='%{n} %{filename}':"
            "x=20:y=20:box=1:boxcolor=black@0.5"
        )


    # Lock FPS last
    filters.append(f"fps={args.fps}")

    vf = ",".join(filters)

    # ============================================================
    # Boomerang handling
    # ============================================================
    input_filelist = args.filelist
    temp_file = None

    if args.boomerang:
        with open(args.filelist, "r", encoding="utf-8") as f:
            lines = [l for l in f if l.startswith("file")]

        reversed_lines = lines[::-1][1:]  # avoid duplicating last frame

        temp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        temp_file = temp.name

        for l in lines:
            temp.write(l)
        for l in reversed_lines:
            temp.write(l)

        temp.close()
        input_filelist = temp_file



    # ============================================================
    # Watermark options
    # ============================================================
    WATERMARK_POSITIONS = {
        "top-left":     "0.02*W:0.02*H",
        "top-right":    "W-w-0.02*W:0.02*H",
        "bottom-left":  "0.02*W:H-h-0.02*H",
        "bottom-right": "W-w-0.02*W:H-h-0.02*H",
        "center":       "(W-w)/2:(H-h)/2",
        "center-bottom":"(W-w)/2:H-h-0.04*H",
        }
        
    WATERMARK_SIZES = {
        "small":        0.08,
        "default":      WATERMARK_DEFAULT_SIZE, # 0.12
        "large":          0.15
    }
 
    WATERMARK_TRANSPARENCY = {
        "weak":        0.8,
        "default":     WATERMARK_DEFAULT_ALPHA, # 0.6
        "strong":      0.35
    }
    
    WATERMARK_VERTICAL_MULTIPLIER = 1.35 # 1.25–1.4 is the usual sweet spot; 1.35 is a good starting value.

    watermark_position = WATERMARK_POSITIONS[WATERMARK_DEFAULT_POSITION]
    watermark_size = WATERMARK_DEFAULT_SIZE
    watermark_alpha = WATERMARK_DEFAULT_ALPHA
    

    if args.wm_position:
        try:
            watermark_position = WATERMARK_POSITIONS.get(args.wm_position, WATERMARK_POSITIONS[WATERMARK_DEFAULT_POSITION]) # defaults to default set at top of script
        except: # if this doesn't work - just go bottom-left !REDUNDANT?
            print("You just triggered an exception... So something went wrong, cos this part shouldn't be neccessary lol")
            watermark_position = WATERMARK_POSITIONS.get(args.wm_position, WATERMARK_POSITIONS["bottom-left"]) # defaults to bottom right if doesn't have get match
            
            
            

    if args.wm_size:
        if isinstance(args.wm_size, (int, float)):
            watermark_size = args.wm_size
        else:
            watermark_size = WATERMARK_SIZES.get(args.wm_size, WATERMARK_SIZES["default"])
        
    if args.wm_alpha:
        if isinstance(args.wm_alpha, (int, float)):
            watermark_alpha = args.wm_alpha
        else:        
            watermark_alpha = WATERMARK_TRANSPARENCY.get(args.wm_alpha, WATERMARK_TRANSPARENCY["default"])

    """
        | Want              | Change        |
        | ----------------- | ------------- |
        | Smaller watermark | `main_w*0.08` |
        | Normal  watermark | `main_w*0.12` |
        | Bigger watermark  | `main_w*0.15` |
        | Stronger logo     | `aa=0.8`      |
        | Normal logo       | `aa=0.6`     |
        | Subtle logo       | `aa=0.35`     |
        | Max cap           | `512 → 384`   |
    """

    # Slightly boost watermark size for vertical video by default
    if args.orientation == "vertical":# and not args.wm_size:
        watermark_size *= WATERMARK_VERTICAL_MULTIPLIER

    wm_target_px = int(min(W, H) * watermark_size)
    wm_target_px = min(wm_target_px, 512)

    if VERBOSE:
        print(
            f"Watermark sizing:\n"
            f"  orientation-mode = {args.orientation}\n"
            f"  size factor      = {watermark_size:.3f}\n"
            f"  target px        = {wm_target_px}"
        )

    # ============================================================
    # FFmpeg command
    # ============================================================

    # watermark_filter = (
        # f"[0:v]{vf}[bg];"
        # f"[1:v][bg]"
        # f"scale2ref='min(iw,min(main_w*{watermark_size},512))':-1"
        # f"[wm][bg2];"
        # f"[wm]format=rgba,colorchannelmixer=aa={watermark_alpha}[wm2];"
        # f"[bg2][wm2]overlay={watermark_position}"
        # )        

    watermark_filter = (
        f"[0:v]{vf}[bg];"
        f"[1:v]scale={wm_target_px}:-1[wm];"
        f"[wm]format=rgba,colorchannelmixer=aa={watermark_alpha}[wm2];"
        f"[bg][wm2]overlay={watermark_position}"
    )
    
    
    if args.watermark:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", input_filelist,
            "-i", args.watermark,
            "-filter_complex", watermark_filter,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", str(args.crf),
            "-preset", args.preset,
            "-movflags", "+faststart",
            output_path
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", input_filelist,
            "-vf", vf,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", str(args.crf),
            "-preset", args.preset,
            "-movflags", "+faststart",
            output_path
        ]

    # ============================================================
    # Execute
    # ============================================================
    print("\nFFmpeg command:\n")
    print(" ".join(cmd), "\n")

    if not args.dry_run:
        subprocess.run(cmd, check=True)

    if temp_file and os.path.exists(temp_file):
        os.unlink(temp_file)

    print(f"\nDone: {output_path}")


if __name__ == "__main__":
    main()
