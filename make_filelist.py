import os
import re
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Generate FFmpeg concat file list from JPGs (auto-detect naming style)"
    )
    parser.add_argument("directory", help="Folder containing JPG images")
    parser.add_argument("--start", type=int, default=None,
                        help="Start number (DSCF number OR suffix counter)")
    parser.add_argument("--end", type=int, default=None,
                        help="End number (DSCF number OR suffix counter)")
    parser.add_argument("--output", default="file_list.txt",
                        help="Output concat file list name")
    parser.add_argument("--skip", type = int, nargs='*', 
        default=None, help="Provide space-separated numbers to skip that range of DSCF files: 1 2 3 4")
    # parser.add_argument("--skip-range", type = str, default=None,
                        # help="Provide two numbers separated by a hyphen to skip that range of DSCF files: `1-50`")

    args = parser.parse_args()
    directory = args.directory
    start = args.start
    end = args.end
    skip_list = args.skip

    # skip_list = args.split(',') # ['1','2','3','4']
    # skip_range_list = list(map(int, *args.skip_range.split('-')))
    # skip_range_list = list(range(*args.skip_range.split('-')))
    # if skip_list:
        # skip_list = args.skip.split(',') # ['1','2','3','4']

    if not os.path.isdir(directory):
        raise RuntimeError(f"Not a directory: {directory}")

    files = os.listdir(directory)

    # Patterns
    # DSCF0851.JPG
    pattern_simple = re.compile(r"(DSCF)(\d{4})\.JPG$", re.IGNORECASE)

    # DSCF0851_0001.jpg
    pattern_suffix = re.compile(r"(DSCF\d{4})_(\d{4})\.JPG$", re.IGNORECASE)

    mode = None
    matches = []

    # --- Detect naming mode ---
    for f in files:
        if pattern_suffix.match(f):
            mode = "suffix"
            break
        if pattern_simple.match(f):
            mode = "simple"
            break

    if mode is None:
        raise RuntimeError("No supported JPG filename patterns found")

    print(f"Detected filename mode: {mode}")
    print(f"Skipping following file numbers: {skip_list}")
    

    # --- Collect matches ---
    for filename in files:
        fullpath = os.path.join(directory, filename)

        if mode == "suffix":
            m = pattern_suffix.match(filename)
            if not m:
                continue
            number = int(m.group(2))  # suffix counter

        else:  # simple DSCF####
            m = pattern_simple.match(filename)
            if not m:
                continue
            number = int(m.group(2))  # DSCF number

        if start is not None and number < start:
            continue
        if end is not None and number > end:
            continue
            
        
    # NEW: remove specific frames provided
        # if skip_range_list is not None and number in skip_range_list:
            # continue
        if skip_list is not None and number in skip_list:
            print(f"Skipping frame #{number}")
            continue
        
        matches.append((number, fullpath))

    if not matches:
        raise RuntimeError("No valid JPG files found in the specified range")

    # Sort numerically
    matches.sort(key=lambda x: x[0])

    # Write concat list
    with open(args.output, "w", encoding="utf-8") as f:
        for _, path in matches:
            f.write(f"file '{path}'\n")

    print(f"Created {args.output} with {len(matches)} frames")

if __name__ == "__main__":
    main()
