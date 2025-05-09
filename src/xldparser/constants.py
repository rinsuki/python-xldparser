import re

XLD_VERSION_PREFIX = "X Lossless Decoder version "
XLD_LOG_START_TIME_PREFIX = "XLD extraction logfile from "
XLD_LOG_START_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %z"
XLD_LOG_USED_DRIVE_PREFIX = "Used drive : "
XLD_LOG_MEDIA_TYPE_PREFIX = "Media type : "
XLD_RIPPER_MODE_PREFIX = "Ripper mode             : "
XLD_DISABLE_AUDIO_CACHE_PREFIX = "Disable audio cache     : "
XLD_MAKE_USE_OF_C2_POINTERS_PREFIX = "Make use of C2 pointers : "
XLD_READ_OFFSET_CORRECTION_PREFIX = "Read offset correction  : "
XLD_MAX_RETRY_COUNT_PREFIX = "Max retry count         : "
XLD_GAP_STATUS_PREFIX = "Gap status              : "
XLD_TOC_HEADER = "TOC of the extracted CD"
XLD_TOC_HEADER_TITLE = "     Track |   Start  |  Length  | Start sector | End sector "
XLD_TOC_HEADER_SEPARATOR = "    ---------------------------------------------------------"
XLD_ALTERNATE_OFFSET_CORRECTION_VALUES_LIST_TITLE = "List of alternate offset correction values"
XLD_ALTERNATE_OFFSET_CORRECTION_VALUES_LIST_TABLE_HEAD = "        #  | Absolute | Relative | Confidence "
XLD_ALTERNATE_OFFSET_CORRECTION_VALUES_LIST_TABLE_SEPARATOR = "    ------------------------------------------"
XLD_ACCURATERIP_SUMMARY_HEADER_RE = re.compile(r"^AccurateRip Summary \(DiscID: ([0-9a-f]{8}-[0-9a-f]{8}-[0-9a-f]{8})\)$")
XLD_ACCURATERIP_SUMMARY_TRACK_LINE = re.compile(r"    Track ([0-9]{2}) : ((OK|NG) \((.+)\)|Not Found)$")
XLD_ACCURATERIP_SUMMARY_SUCCESS_SUBMISSIONS = re.compile(r"(v1\+v2|v1|v2), confidence ([0-9]+\+)?([0-9]+)/([0-9]+)(, with different offset)?$")
XLD_ACCURATERIP_SUMMARY_FAIL_SUBMISSIONS = re.compile(r"total ([0-9]+) submissions?")
XLD_ACCURATERIP_SUMMARY_DISC_NOTFOUND_HEADER = "AccurateRip Summary"
XLD_ACCURATERIP_SUMMARY_DISC_NOTFOUND_MESSAGE = "    Disc not found in AccurateRip DB."
XLD_ACCURATERIP_SUMMARY_ACCURATELY_RIPPED = "        ->All tracks accurately ripped."
XLD_ACCURATERIP_SUMMARY_PARTIALLY_FAILED = re.compile(r"^        ->([0-9]+) tracks? accurately ripped, ([0-9]+) tracks? not$")
XLD_ALL_TRACKS_HEADER = "All Tracks"
XLD_TRACK_STATISTICS_HEADER = "    Statistics"
XLD_TRACK_STATISTICS_READ_ERROR = "        Read error                           : "
XLD_TRACK_STATISTICS_JITTER_ERROR = "        Jitter error (maybe fixed)           : "
XLD_TRACK_STATISTICS_RETRY_SECTOR_COUNT = "        Retry sector count                   : "
XLD_TRACK_STATISTICS_DAMAGED_SECTOR_COUNT = "        Damaged sector count                 : "
XLD_TRACK_STATISTICS_LIST_OF_DAMAGED_SECTOR_POSITIONS = "        List of damaged sector positions     :"
XLD_TRACK_STATISTICS_DAMAGED_SECTOR_POSITION_RE = re.compile(r"^            \(([0-9]+)\) ([0-9]{2}:[0-9]{2}:[0-9]{2})$")
XLD_TRACK_HEADER = re.compile(r"^Track ([0-9]{2})$")
XLD_TRACK_FILENAME_HEADER = "    Filename : "
XLD_TRACK_PRE_GAP_LENGTH_HEADER = "    Pre-gap length : "
XLD_TRACK_CRC32_HASH_TEST_HEADER = "    CRC32 hash (test run)    : "
XLD_TRACK_CRC32_HASH_HEADER = "    CRC32 hash               : "
XLD_TRACK_CRC32_HASH_TEST_FAIL = "        ->Rip may not be accurate."
XLD_TRACK_CRC32_SKIP_ZERO_HASH_HEADER = "    CRC32 hash (skip zero)   : "
XLD_TRACK_ACCURATERIP_V1_HEADER = "    AccurateRip v1 signature : "
XLD_TRACK_ACCURATERIP_V2_HEADER = "    AccurateRip v2 signature : "
XLD_TRACK_ACCURATERIP_HASH_RE = re.compile(r"^([0-9A-F]{8})(?: \(([0-9A-F]{8}) w/correction\))?$")
XLD_TRACK_ACCURATERIP_RESULT_SUCCESS_RE = re.compile(r"^        ->Accurately ripped \((.+)\)$")
XLD_TRACK_ACCURATERIP_RESULT_SUCCESS_DETAIL_RE = re.compile(r"(v1\+v2|v1|v2), confidence ([0-9]+\+)?([0-9]+)/([0-9]+)$")
XLD_TRACK_ACCURATERIP_RESULT_SUCCESS_WITH_DIFFERENT_OFFSET_RE = re.compile(r"^        ->Accurately ripped with different offset \((.+)\)$")
XLD_TRACK_ACCURATERIP_RESULT_SUCCESS_WITH_DIFFERENT_OFFSET_DETAIL_RE = re.compile(r"(v1\+v2|v1|v2), confidence ([0-9]+\+)?([0-9]+)/([0-9]+), offset ([+-][0-9]+)$")
XLD_TRACK_ACCURATERIP_RESULT_FAIL_RE = re.compile(r"^        ->Rip may not be accurate \(total ([0-9]+) submissions?\)\.$")
XLD_TRACK_ACCURATERIP_RESULT_NOTFOUND = "        ->Track not present in AccurateRip database."
XLD_FOOTER_NO_ERROR = "No errors occurred"
XLD_FOOTER_SOME_ERROR = "Some inconsistencies found"
XLD_FOOTER = "End of status report"