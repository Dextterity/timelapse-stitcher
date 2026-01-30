# Timelapse-stitcher

## ABOUT
Have you filled up all your hard drives with astro/aurora shoots? Yes!
Have you at least kept settings and framing somewhat conistent? Yes!
Are you an expert at FFmpeg? No?...  
Then you're in the right place! 

Fill up MORE storage-space by transforming your wonderful pics into timelapse films using this handy little python script[^1].  
No FFmpeg knowledge required![^bignote]

## SCRIPTS:
1. `make_filelist.py`
    - Generate FFmpeg concat file list from JPGs
3. `render_timelapse.py`
    - Render timelapse video from FFmpeg concat file list 

## USAGE:
in python terminal meeting requirements: `python make_filelist.py -h`

### Filelist 
Full usage printout:
```
usage: make_filelist.py [-h] [--start START] [--end END] [--output OUTPUT] [--skip [SKIP ...]] directory

Generate FFmpeg concat file list from JPGs (auto-detect naming style)

positional arguments:
  directory          Folder containing JPG images

options:
  -h, --help         show this help message and exit
  --start START      Start number (DSCF number OR suffix counter)
  --end END          End number (DSCF number OR suffix counter)
  --output OUTPUT    Output concat file list name
  --skip [SKIP ...]  Provide space-separated numbers to skip that range of DSCF files: 1 2 3 4
```

### TImelapse 

in python terminal meeting requirements: `python render_timelapse.py -h`

Full usage printout:
  ```
  usage: render_timelapse.py [-h] [--name NAME] [--outdir OUTDIR] [--orientation {landscape,vertical}] [--resolution {1080p,2160p,HD,4k}] [--aspect-mode {auto,scale,crop,pad}]
                             [--crop-bias {upper,center,lower}] [--debug-overlay] [--fps FPS] [--slowdown SLOWDOWN] [--watermark WATERMARK] [--wm-position WM_POSITION] [--wm-size WM_SIZE]
                             [--wm-alpha WM_ALPHA] [--look {milkyway,aurora,aurora-boosted}] [--gamma GAMMA] [--contrast CONTRAST] [--saturation SATURATION] [--clarity CLARITY] [--boomerang]
                             [--use-exif-date] [--crf CRF] [--preset PRESET] [--dry-run] [--verbose]
                             filelist
  
  Render timelapse video from FFmpeg concat file list
  
  positional arguments:
    filelist              FFmpeg concat file list (.txt)
  
  options:
    -h, --help            show this help message and exit
    --name NAME           Base output name (default: file list name)
    --outdir OUTDIR       Output directory
    --orientation {landscape,vertical}
                          Output orientation: landscape (16:9) or vertical (9:16)
    --resolution {1080p,2160p,HD,4k}
                          Resolution tier. Landscape: HD = 1080p = 1920x1080, 4k = 2160p = 3840x2160. Vertical: HD= 1080p = 1080x1920, 4k= 2160p = 2160x3840.
    --aspect-mode {auto,scale,crop,pad}
                          How to fit source into output frame. auto: landscape->scale, vertical->crop. scale: force exact WxH (distorts if AR differs). crop: preserve AR, fill frame by cropping. pad: preserve AR, fit inside frame with bars.
    --crop-bias {upper,center,lower}
                          Crop bias for crop mode: upper/center/lower
    --debug-overlay       Burn frame number + filename on video (for debugging)
    --fps FPS
    --slowdown SLOWDOWN   Playback slowdown (1.5 = 50% slower). Use 1.2–1.6 for astro.
    --watermark WATERMARK
                          Path to watermark PNG
    --wm-position WM_POSITION
                          Watermark position (top-left, top-right, bottom-left, bottom-right, center, center-bottom)
    --wm-size WM_SIZE     Watermark sizes (small, default, large)
    --wm-alpha WM_ALPHA   Watermark alpha / transparency (weak, default, strong)
    --look {milkyway,aurora,aurora-boosted}
                          Apply recommended astro look preset.
                          PRESET DETAILS:
  
                          'milkyway':
                              gamma = 1.30,       # Midtone lift (≈ +0.3 EV)
                              contrast = 1.15,    # Restores punch after gamma
                              saturation = 1.10,  # Gentle color boost
                              clarity = 0.30      # Subtle micro-contrast (safe)
  
                          'aurora':               # Aurora-friendly look: Preserves color gradients and motion
                              gamma = 1.35,       # Slightly brighter midtones
                              contrast = 1.15,    # Softer contrast for glow
                              saturation = 1.15,  # Aurora colors benefit here
                              clarity = 0.30
  
                          'aurora-boosted':
                              gamma = 1.42,       # brighter midtones
                              contrast = 1.35,    # Softer contrast for glow
                              saturation = 1.3,   # Powerful colours
                              clarity = 0.35
  
    --gamma GAMMA         Gamma lift (1.2–1.25 recommended for astro)
    --contrast CONTRAST   Contrast multiplier (1.1–1.25 recommended)
    --saturation SATURATION
                          Color saturation (1.05–1.15 recommended)
    --clarity CLARITY     Micro-contrast via unsharp mask (0.2–0.4 safe)
    --boomerang
    --use-exif-date       Prefix output filename with EXIF date (YYYY-MM-DD)
    --crf CRF             FFmpeg encoding eption - see FFmpeg docs for more
    --preset PRESET       FFmpeg encoding eption - see FFmpeg docs for more
    --dry-run             Print the final FFmpeg comand without executing
    --verbose             For debugging perposes
  ```

[^bignote]: You do need to have FFmpeg installed though:  

    - Release full build recommended  
    - Different builds could work, but I gyan is recommended: https://www.gyan.dev/ffmpeg/builds/  
    - Credits & build used: `FFmpeg version 8.0-full_build-www.gyan.dev Copyright (c) 2000-2025 the FFmpeg developers`  

[^1]: Really just a python wrapper to create FFmpeg calls (cos too lazy to learn FFmpeg lol).
