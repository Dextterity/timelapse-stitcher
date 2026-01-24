import os
import argparse
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
# EXIF DATE EXTRACTION
# ============================================================
def extract_date_from_first_image(filelist_path, verbose = False):
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
        if verbose:
            print("Can't find first image! (extract_date_from_first_image)")
        return None

    try:
        img = Image.open(first_image)
        exif = img._getexif()
        if not exif:
            if verbose:
                print("No exif data! (extract_date_from_first_image)")
            return None

        for tag, value in exif.items():
            if TAGS.get(tag) == "DateTimeOriginal":
                dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                return dt.strftime("%Y-%m-%d")
    except Exception as e:
        if verbose:
            print("extract_date_from_first_image failed:")
            print(type(e).__name__, e)
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
    }
}


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Render timelapse video from FFmpeg concat file list"
    )

    # --- Required ---
    parser.add_argument("filelist", help="FFmpeg concat file list (.txt)")

    # --- Output ---
    parser.add_argument("--name", help="Base output name (default: file list name)")
    parser.add_argument("--outdir", default="Timelapses", help="Output directory")

    # --- Video basics ---
    parser.add_argument("--resolution", choices=["1080p", "4k"], default="1080p")
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
        "--look", choices=["milkyway", "aurora"],
        help="Apply recommended astro look preset: \n"
        "\n"
        "PRESET DETAILS: \n"
        "'milkyway': { \n"
        "    'gamma': 1.30,       # Midtone lift (≈ +0.3 EV) \n"
        "    'contrast': 1.15,    # Restores punch after gamma \n"
        "    'saturation': 1.10,  # Gentle color boost \n"
        "    'clarity': 0.30      # Subtle micro-contrast (safe) \n"
        "}, \n"
        " \n"
        "# Aurora-friendly look \n"
        "# Preserves color gradients and motion \n"
        "'aurora': { \n"
        "    'gamma': 1.35,       # Slightly brighter midtones \n"
        "    'contrast': 1.15,    # Softer contrast for glow \n"
        "    'saturation': 1.15,  # Aurora colors benefit here \n"
        "    'clarity': 0.30 \n"
        "}         \n"

        
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
        "--use-exif-date", action="store_true", default=True,
        help="Prefix output filename with EXIF date (YYYY-MM-DD)"
    )

    # --- Encoding ---
    parser.add_argument("--crf", type=int, default=20)
    parser.add_argument("--preset", default="slow")

    # --- Debug ---
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")


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
        date_str = extract_date_from_first_image(args.filelist, verbose = VERBOSE)
        if date_str:
            print(f"Date found! {date_str} \n")
            base_name = f"{date_str}_{base_name}"

    suffix = [args.resolution]

    if args.look:
        suffix.append(args.look)

    if args.slowdown != 1.0:
        suffix.append(f"slow{args.slowdown}x")

    if args.boomerang:
        suffix.append("boom")

    # if args.watermark:
        # suffix.append("wm")

    if args.wm_position:
        # watermark_position = WATERMARK_POSITIONS.get(args.wm_position, WATERMARK_POSITIONS["bottom-left"]) # defaults to bottom right if doesn't have get match
        # print(watermark_position) # !DEL
        print(args.wm_position) # !DEL
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
    scale = "1920:1080" if args.resolution == "1080p" else "3840:2160"

    # ============================================================
    # Filters (ORDER MATTERS)
    # ============================================================
    filters = [
        f"scale={scale}:flags=lanczos"
    ]

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



    # ============================================================
    # FFmpeg command
    # ============================================================

    # watermark_filter = (
        # f"[0:v]{vf}[bg];"
        # f"[1:v][bg]"
        # f"scale2ref='min(iw,min(main_w*0.12,512))':-1"
        # f"[wm][bg2];"
        # f"[wm]format=rgba,colorchannelmixer=aa=0.6[wm2];"
        # f"[bg2][wm2]overlay=W-w-0.02*W:H-h-0.02*H"
        # )        

    watermark_filter = (
        f"[0:v]{vf}[bg];"
        f"[1:v][bg]"
        f"scale2ref='min(iw,min(main_w*{watermark_size},512))':-1"
        f"[wm][bg2];"
        f"[wm]format=rgba,colorchannelmixer=aa={watermark_alpha}[wm2];"
        f"[bg2][wm2]overlay={watermark_position}"
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
