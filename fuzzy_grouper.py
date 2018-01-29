import re
import sys
from difflib import SequenceMatcher

SIMILARITY_DIGITS = 3

def fuzzy_grouper(files, similarity_threshold=0.90,
                  comparison_slice=slice(0, 1),
                  status_line=None):
    """Group together similar files.
    
    Input: {"filename": "file-contents", ...}
    
    Output: [["filename", ...], ["filename", ...]]
    
    * similarity_threshold: Minimum similarity between two files to be
      considered part of the same group.
    * comparison_slice: Slice of items in a group to compare a new file
      with before also adding it to that group.
    """
    groups = []
    
    for i, (this_filename, this_content) in enumerate(files.items()):
        if status_line:
            status_line.update("Comparing file {} of {} against {} group{}...".format(
                i,
                len(files),
                len(groups),
                "s" if len(groups) != 1 else ""))
        for group in groups:
            for other_filename in group[comparison_slice]:
                other_content = files[other_filename]
                sm = SequenceMatcher(None,
                                     this_content,
                                     other_content,
                                     autojunk=False)
                if (sm.real_quick_ratio() < similarity_threshold
                        or sm.ratio() < similarity_threshold):
                    # This group doesn't match, give up
                    break
            else:
                # This group does match! Join it!
                group.append(this_filename)
                break
        else:
            # No group contains anything similar, start a new group
            groups.append([this_filename])
            if status_line:
                status_line.append(
                    "Created new group for {}".format(this_filename))
        
        # Keep the largest group first since this one is most likely to match
        # future groups
        groups.sort(key=len, reverse=True)
    
    if status_line:
        status_line.update("")
        status_line.append(
            "Found {} group{}.".format(
                len(groups),
                "s" if len(groups) != 1 else ""))
    
    return groups


def remove_hex(s):
    """Remove all hex literals (e.g. 0x1234ABCD) from a string."""
    return re.sub(r"0x[0-9a-f]+", "@", s, flags=re.IGNORECASE)

def remove_numbers(s):
    """Remove all numbers from a string."""
    return re.sub(r"[0-9]+([.][0-9]+)?", "@", s, flags=re.IGNORECASE)

def remove_bars(s):
    """Shorten all long bars which vary in length when different numbers are
    present.
    """
    return re.sub(r"(^[-=_~+!]+ | [-=_~+!]+$)", "=", s, flags=re.MULTILINE)

def filter_string(s):
    return remove_hex(remove_numbers(remove_bars(s)))

class StatusLine(object):
    
    def __init__(self):
        self._started = False
        self._last_line = None
    
    def update(self, new_line):
        if not self._started:
            sys.stderr.write("\n")
            self._started = True
        sys.stderr.write("\033[1F\033[2K{}\n".format(new_line))
        self._last_line = new_line
    
    def append(self, new_line):
        old_status = self._last_line
        self.update(new_line)
        
        sys.stderr.write("\n")
        self.update(old_status)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="""
            A quick-and-dirty tool for grouping together similar log files. The
            provided filenames are printed on standard out with blank lines
            seperating groups of similar files.
        """
    )
    
    parser.add_argument("file", nargs="*",
                        help="Files to compare.")
    
    parser.add_argument("--threshold", "-t", type=float, default=0.9,
                        help="Lower threshold for similarity scores of " 
                             "files to be grouped together.")
    
    parser.add_argument("--summary-only", "-s", action="store_true",
                        help="Only show a single file from each group.")
    
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print a status line indicating progress.")
    
    parser.add_argument("--compare-whole-group", "-w", action="store_true",
                        help="If set, files are checked agaisnt every other " 
                             "file in a candidate group before adding it. "
                             "Otherwise, candidates are only compared with a "
                             "single candidate within the group. Setting "
                             "this option significantly slows down this "
                             "program.")
    
    parser.add_argument("--keep-numbers", "-n", action="store_true",
                        help="If set, numbers are not stripped from files "
                             "before comparison.")
    parser.add_argument("--keep-hex", "-x", action="store_true",
                        help="If set, hex strings are not stripped from files "
                             "before comparison.")
    parser.add_argument("--keep-ascii-bars", "-b", action="store_true",
                        help="If set, horizontal ASCII-art bars are not "
                             "stripped from files before comparison.")
    
    parser.add_argument("--print-similarity-matrix", "-m", action="store_true",
                        help="Print the similarity matrix of the groups.")
    
    parser.add_argument("--score", "-S", nargs=2, metavar="file",
                        default=[],
                        help="Print the similarity score of two files.")
    
    parser.add_argument("--normalise", "-N", nargs=1, metavar="file",
                        default=[],
                        help="Show the normalised version of a file.")
    
    args = parser.parse_args()
    
    if bool(args.score) + bool(args.normalise) + bool(args.file) > 1:
        parser.error("file, --score, --normalise are mutually exclusive.")
    
    filenames = args.file + args.normalise + args.score
    
    if args.verbose:
        status_line = StatusLine()
    else:
        status_line = None
    
    filter_bank = []
    if not args.keep_numbers:
        filter_bank.append(remove_numbers)
    if not args.keep_hex:
        filter_bank.append(remove_hex)
    if not args.keep_ascii_bars:
        filter_bank.append(remove_bars)
    
    if status_line:
        status_line.update(
            "Filtering {} files...".format(len(filenames)))
    files = {}
    for filename in filenames:
        with open(filename, "r") as f:
            s = f.read()
        for fn in filter_bank:
            s = fn(s)
        files[filename] = s
    
    if args.normalise:
        sys.stdout.write(files[args.normalise[0]])
        return 0
    
    if args.score:
        file_0 = files[args.score[0]]
        file_1 = files[args.score[1]]
        
        sm = SequenceMatcher(None, file_0, file_1, autojunk=False)
        print(sm.ratio())
        return 0

    if args.compare_whole_group:
        comparison_slice = slice(0, None)
    else:
        comparison_slice = slice(0, 1)

    # Construct the groups
    groups = fuzzy_grouper(files,
                           args.threshold,
                           comparison_slice,
                           status_line)
    
    if args.summary_only:
        print("\n\n".join(
            "{}\n(and {} other{})".format(group[0],
                                          len(group)-1,
                                          "s" if (len(group)-1) != 1 else "")
            for group in groups))
    else:
        print("\n\n".join("\n".join(group) for group in groups))
    
    if args.print_similarity_matrix:
        print("")
        
        # Print column numbers
        line = "{:{}s} ".format("GROUP", SIMILARITY_DIGITS+2)
        for j in range(len(groups)):
            line += "{:{}d} ".format(j, SIMILARITY_DIGITS+2)
        print(line)
        
        for i, group_a in enumerate(groups):
            # Row number
            line = "{:{}d} ".format(i, SIMILARITY_DIGITS+2)
            
            # Row contents
            for j, group_b in enumerate(groups):
                if j > i:
                    sm = SequenceMatcher(None,
                                         files[group_a[0]],
                                         files[group_b[0]],
                                         autojunk=False)
                    line += "{:1.{}f} ".format(sm.ratio(), SIMILARITY_DIGITS)
                elif j == i:
                    line += "{:1.{}f} ".format(1.0, SIMILARITY_DIGITS)
                else:
                    line += " "*(2 + SIMILARITY_DIGITS + 1)
            print(line)
    

if __name__ == "__main__":
    main()
