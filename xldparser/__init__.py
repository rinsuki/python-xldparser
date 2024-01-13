from dataclasses import dataclass
from datetime import datetime
from io import TextIOBase
from . import constants as c
from .second_sector import SecondSectorInt

_ALL_COUNT = -999999

def parse_ripped_count(input_str: str):
    input = input_str.split(", ")
    success_count = 0
    fail_count = 0
    not_found_count = 0
    for i in input:
        count, msg = i.split(" ", 1)
        if msg.endswith("."):
            msg = msg[:-1]
        if count == "All":
            count = _ALL_COUNT
        else:
            count = int(count)
        if count == 1 or count == 0:
            assert msg.startswith("track ")
            msg = msg[6:]
        else:
            assert msg.startswith("tracks ")
            msg = msg[7:]
        if msg == "accurately ripped":
            assert success_count == 0
            success_count = count
        elif msg == "not found":
            assert not_found_count == 0
            not_found_count = count
        elif msg == "not":
            assert fail_count == 0
            fail_count = count
    assert (success_count != 0) or (fail_count != 0) or (not_found_count != 0)
    return success_count, fail_count, not_found_count


@dataclass
class XLDTOCEntry:
    no: int
    start_sector: SecondSectorInt
    end_sector: SecondSectorInt

    @staticmethod
    def parse(line: str):
        cols = [x.strip(" ") for x in line.split("|")]
        no = int(cols[0])
        start_sector = SecondSectorInt(cols[3])
        end_sector = SecondSectorInt(cols[4])
        start_str = start_sector.as_second_sector_str()
        length_str = SecondSectorInt(end_sector - start_sector + 1).as_second_sector_str()
        assert cols[1] == start_str
        assert cols[2] == length_str
        return XLDTOCEntry(no=no, start_sector=start_sector, end_sector=end_sector)

@dataclass
class XLDAccurateRipSuccessSummary:
    v1: bool
    v2: bool
    confidence_used_v1: int
    confidence_used_v2: int

    @staticmethod
    def parse(line: str):
        match_result = c.XLD_ACCURATERIP_SUMMARY_SUCCESS_SUBMISSIONS.match(line)
        assert match_result is not None
        v1 = match_result.group(1) == "v1" or match_result.group(1) == "v1+v2"
        v2 = match_result.group(1) == "v2" or match_result.group(1) == "v1+v2"
        if match_result.group(2) is not None:
            confidence_used_v1 = int(match_result.group(2)[:-1])
        else:
            confidence_used_v1 = 0
        confidence_used_v2 = int(match_result.group(3))
        confidence_total = int(match_result.group(4))
        return XLDAccurateRipSuccessSummary(v1=v1, v2=v2, confidence_used_v1=confidence_used_v1, confidence_used_v2=confidence_used_v2), confidence_total

@dataclass
class XLDAccurateRipSummaryEntry:
    success_summary: XLDAccurateRipSuccessSummary | None
    confidence_total: int

    @staticmethod
    def parse_track(line: str):
        if line == c.XLD_TRACK_ACCURATERIP_RESULT_NOTFOUND:
            return None
        success_match = c.XLD_TRACK_ACCURATERIP_RESULT_SUCCESS_RE.match(line)
        if success_match is not None:
            success_summary, confidence_total = XLDAccurateRipSuccessSummary.parse(success_match.group(1))
        else:
            fail_match = c.XLD_TRACK_ACCURATERIP_RESULT_FAIL_RE.match(line)
            if fail_match is None:
                raise Exception("Unknown line: " + line)
            confidence_total = int(fail_match.group(1))
            success_summary = None
        return XLDAccurateRipSummaryEntry(success_summary=success_summary, confidence_total=confidence_total)

@dataclass
class XLDAccurateRipSummaryEntryWithNo:
    no: int
    entry: XLDAccurateRipSummaryEntry | None

    @staticmethod
    def parse(line: str):
        matched_line = c.XLD_ACCURATERIP_SUMMARY_TRACK_LINE.match(line)
        if matched_line is None:
            raise Exception("Unknown line: " + line)
        no = int(matched_line.group(1))
        if matched_line.group(2) == "Not Found":
            return XLDAccurateRipSummaryEntryWithNo(no = no, entry=None)
        ok = matched_line.group(3) == "OK"
        success_summary = None
        if ok:
            success_summary, confidence_total = XLDAccurateRipSuccessSummary.parse(matched_line.group(4))
        else:
            assert matched_line.group(3) == "NG"
            fail_submissions_match = c.XLD_ACCURATERIP_SUMMARY_FAIL_SUBMISSIONS.match(matched_line.group(4))
            if fail_submissions_match is None:
                raise Exception("Unknown line: " + line)
            confidence_total = int(fail_submissions_match.group(1))
        return XLDAccurateRipSummaryEntryWithNo(no = no, entry=XLDAccurateRipSummaryEntry(success_summary=success_summary, confidence_total=confidence_total))

@dataclass
class XLDTrackStatistics:
    read_error: int
    jitter_error: int
    retry_sector_count: int
    damaged_sector_count: int

    @staticmethod
    def parse(input: TextIOBase):
        assert input.readline().rstrip() == c.XLD_TRACK_STATISTICS_HEADER
        read_error = input.readline().rstrip()
        assert read_error.startswith(c.XLD_TRACK_STATISTICS_READ_ERROR)
        read_error = int(read_error[len(c.XLD_TRACK_STATISTICS_READ_ERROR):])
        jitter_error = input.readline().rstrip()
        assert jitter_error.startswith(c.XLD_TRACK_STATISTICS_JITTER_ERROR)
        jitter_error = int(jitter_error[len(c.XLD_TRACK_STATISTICS_JITTER_ERROR):])
        retry_sector_count = input.readline().rstrip()
        assert retry_sector_count.startswith(c.XLD_TRACK_STATISTICS_RETRY_SECTOR_COUNT)
        retry_sector_count = int(retry_sector_count[len(c.XLD_TRACK_STATISTICS_RETRY_SECTOR_COUNT):])
        damaged_sector_count = input.readline().rstrip()
        assert damaged_sector_count.startswith(c.XLD_TRACK_STATISTICS_DAMAGED_SECTOR_COUNT)
        damaged_sector_count = int(damaged_sector_count[len(c.XLD_TRACK_STATISTICS_DAMAGED_SECTOR_COUNT):])
        return XLDTrackStatistics(
            read_error=read_error,
            jitter_error=jitter_error,
            retry_sector_count=retry_sector_count,
            damaged_sector_count=damaged_sector_count
        )
        

@dataclass
class XLDPerTrackStatistics(XLDTrackStatistics):
    damaged_sectors: list[SecondSectorInt]

    @staticmethod
    def parse(input: TextIOBase):
        sup = XLDTrackStatistics.parse(input)
        damaged_sectors: list[SecondSectorInt] = []
        list_of_damaged_sector_positions = input.readline().rstrip()
        if list_of_damaged_sector_positions == c.XLD_TRACK_STATISTICS_LIST_OF_DAMAGED_SECTOR_POSITIONS:
            i = 0
            while True:
                line = input.readline().rstrip()
                if line == "":
                    break
                i += 1
                l = c.XLD_TRACK_STATISTICS_DAMAGED_SECTOR_POSITION_RE.match(line)
                if l is None:
                    raise Exception("Unknown line: " + line)
                assert int(l.group(1)) == i
                damaged_sectors.append(SecondSectorInt.from_second_sector_str(l.group(2)))
        elif list_of_damaged_sector_positions != "":
            raise Exception("Unknown line: " + list_of_damaged_sector_positions)
        return XLDPerTrackStatistics(
            read_error=sup.read_error,
            jitter_error=sup.jitter_error,
            retry_sector_count=sup.retry_sector_count,
            damaged_sector_count=sup.damaged_sector_count,
            damaged_sectors=damaged_sectors
        )

@dataclass
class XLDAccurateRipPerTrackEntry:
    v1_signature: int
    v2_signature: int
    accuratery_ripped: bool
    total_submissions: int

@dataclass
class XLDTrackEntryCancelled:
    no: int
    filename: str
    cancelled: bool = True

@dataclass
class XLDTrackEntry:
    no: int
    filename: str
    pre_gap_length: SecondSectorInt
    crc32_hash: str
    crc32_skip_zero_hash: str
    accuraterip_v1: str
    accuraterip_v2: str
    accuraterip_result: XLDAccurateRipSummaryEntry | None
    statistics: XLDPerTrackStatistics

    @staticmethod
    def parse(first: str, line: TextIOBase):
        no_match = c.XLD_TRACK_HEADER.match(first)
        if no_match is None:
            raise Exception("Unknown line: " + first)
        no = int(no_match.group(1))
        filename = line.readline().rstrip()
        assert filename.startswith(c.XLD_TRACK_FILENAME_HEADER)
        filename = filename[len(c.XLD_TRACK_FILENAME_HEADER):]
        pre_gap_length = line.readline().rstrip()
        if pre_gap_length.startswith(c.XLD_TRACK_PRE_GAP_LENGTH_HEADER):
            pre_gap_length = SecondSectorInt.from_second_sector_str(pre_gap_length[len(c.XLD_TRACK_PRE_GAP_LENGTH_HEADER):])
            assert line.readline().rstrip() == ""
        else:
            if pre_gap_length == "    (cancelled by user)":
                assert line.readline().rstrip() == ""
                return XLDTrackEntryCancelled(no=no, filename=filename)
            assert pre_gap_length == ""
            pre_gap_length = SecondSectorInt(0)

        crc32_hash = line.readline().rstrip()
        assert crc32_hash.startswith(c.XLD_TRACK_CRC32_HASH_HEADER)
        crc32_hash = crc32_hash[len(c.XLD_TRACK_CRC32_HASH_HEADER):]
        crc32_skip_zero_hash = line.readline().rstrip()
        assert crc32_skip_zero_hash.startswith(c.XLD_TRACK_CRC32_SKIP_ZERO_HASH_HEADER)
        crc32_skip_zero_hash = crc32_skip_zero_hash[len(c.XLD_TRACK_CRC32_SKIP_ZERO_HASH_HEADER):]
        accuraterip_v1 = line.readline().rstrip()
        assert accuraterip_v1.startswith(c.XLD_TRACK_ACCURATERIP_V1_HEADER)
        accuraterip_v1 = accuraterip_v1[len(c.XLD_TRACK_ACCURATERIP_V1_HEADER):]
        accuraterip_v2 = line.readline().rstrip()
        assert accuraterip_v2.startswith(c.XLD_TRACK_ACCURATERIP_V2_HEADER)
        accuraterip_v2 = accuraterip_v2[len(c.XLD_TRACK_ACCURATERIP_V2_HEADER):]
        accuraterip_result = XLDAccurateRipSummaryEntry.parse_track(line.readline().rstrip())
        statistics = XLDPerTrackStatistics.parse(line)
        return XLDTrackEntry(
            no=no,
            filename=filename,
            pre_gap_length=pre_gap_length,
            crc32_hash=crc32_hash,
            crc32_skip_zero_hash=crc32_skip_zero_hash,
            accuraterip_v1=accuraterip_v1,
            accuraterip_v2=accuraterip_v2,
            accuraterip_result=accuraterip_result,
            statistics=statistics
        )

@dataclass
class XLDAlternateOffsetCorrectionEntry:
    absolute: int
    relative: int
    confidence: int
    @staticmethod
    def parse(line: str, expected_index: int):
        cols = [x.strip(" ") for x in line.split("|")]
        assert int(cols[0]) == expected_index + 1
        absolute = int(cols[1])
        relative = int(cols[2])
        confidence = int(cols[3])
        return XLDAlternateOffsetCorrectionEntry(absolute=absolute, relative=relative, confidence=confidence)

@dataclass
class XLDLog:
    xld_version: str
    log_start_time: datetime
    used_drive: str
    media_type: str
    artist_and_album_title: str

    ripper_mode: str
    disable_audio_cache: str
    make_use_of_c2_pointers: bool
    read_offset_correction: int
    max_retry_count: int
    gap_status: str

    toc: list[XLDTOCEntry]
    alternate_offset_corrections: list[XLDAlternateOffsetCorrectionEntry]
    accuraterip_disc_id: str | None
    accuraterip_summary: list[XLDAccurateRipSummaryEntryWithNo]
    all_tracks_summary: XLDTrackStatistics | None
    tracks: list[XLDTrackEntry | XLDTrackEntryCancelled]

    successfly_ripped: bool
    is_cancelled: bool

    @staticmethod
    def parse(input: TextIOBase):
        cancelled = False

        xld_version = input.readline().rstrip()
        assert xld_version.startswith(c.XLD_VERSION_PREFIX)
        xld_version = xld_version[len(c.XLD_VERSION_PREFIX):]

        assert input.readline().rstrip() == ""

        log_start_time_str = input.readline().rstrip()
        assert log_start_time_str.startswith(c.XLD_LOG_START_TIME_PREFIX)
        log_start_time = datetime.strptime(log_start_time_str[len(c.XLD_LOG_START_TIME_PREFIX):], c.XLD_LOG_START_TIME_FORMAT)

        assert input.readline().rstrip() == ""
        artist_and_album_title = input.readline().rstrip()
        assert input.readline().rstrip() == ""

        used_drive = input.readline().rstrip()
        assert used_drive.startswith(c.XLD_LOG_USED_DRIVE_PREFIX)
        used_drive = used_drive[len(c.XLD_LOG_USED_DRIVE_PREFIX):]

        media_type = input.readline().rstrip()
        assert media_type.startswith(c.XLD_LOG_MEDIA_TYPE_PREFIX)
        media_type = media_type[len(c.XLD_LOG_MEDIA_TYPE_PREFIX):]

        assert input.readline().rstrip() == ""

        ripper_mode = input.readline().rstrip()
        assert ripper_mode.startswith(c.XLD_RIPPER_MODE_PREFIX)
        ripper_mode = ripper_mode[len(c.XLD_RIPPER_MODE_PREFIX):]

        disable_audio_cache = input.readline().rstrip()
        assert disable_audio_cache.startswith(c.XLD_DISABLE_AUDIO_CACHE_PREFIX)
        disable_audio_cache = disable_audio_cache[len(c.XLD_DISABLE_AUDIO_CACHE_PREFIX):]

        make_use_of_c2_pointers = input.readline().rstrip()
        assert make_use_of_c2_pointers.startswith(c.XLD_MAKE_USE_OF_C2_POINTERS_PREFIX)
        make_use_of_c2_pointers = make_use_of_c2_pointers[len(c.XLD_MAKE_USE_OF_C2_POINTERS_PREFIX):]
        if make_use_of_c2_pointers == "NO":
            make_use_of_c2_pointers = False
        elif make_use_of_c2_pointers == "YES":
            make_use_of_c2_pointers = True
        else:
            raise Exception(f"Unknown Value for Make use of C2 pointers: {make_use_of_c2_pointers}")
        
        read_offset_correction = input.readline().rstrip()
        assert read_offset_correction.startswith(c.XLD_READ_OFFSET_CORRECTION_PREFIX)
        read_offset_correction = int(read_offset_correction[len(c.XLD_READ_OFFSET_CORRECTION_PREFIX):])

        max_retry_count = input.readline().rstrip()
        assert max_retry_count.startswith(c.XLD_MAX_RETRY_COUNT_PREFIX)
        max_retry_count = int(max_retry_count[len(c.XLD_MAX_RETRY_COUNT_PREFIX):])

        gap_status = input.readline().rstrip()
        assert gap_status.startswith(c.XLD_GAP_STATUS_PREFIX)
        gap_status = gap_status[len(c.XLD_GAP_STATUS_PREFIX):]

        assert input.readline().rstrip() == ""

        assert input.readline().rstrip() == c.XLD_TOC_HEADER
        assert input.readline().rstrip("\n") == c.XLD_TOC_HEADER_TITLE
        assert input.readline().rstrip() == c.XLD_TOC_HEADER_SEPARATOR

        toc: list[XLDTOCEntry] = []
        while True:
            line = input.readline().rstrip()
            if line == "":
                break
            toc.append(XLDTOCEntry.parse(line))

        alternate_offset_corrections: list[XLDAlternateOffsetCorrectionEntry] = []
        while True:
            accuraterip_summary_header = input.readline().rstrip()
            if accuraterip_summary_header == c.XLD_ALTERNATE_OFFSET_CORRECTION_VALUES_LIST_TITLE:
                assert input.readline().rstrip("\n") == c.XLD_ALTERNATE_OFFSET_CORRECTION_VALUES_LIST_TABLE_HEAD
                assert input.readline().rstrip() == c.XLD_ALTERNATE_OFFSET_CORRECTION_VALUES_LIST_TABLE_SEPARATOR
                i = 0
                while True:
                    line = input.readline().rstrip()
                    if line == "":
                        break
                    alternate_offset_corrections.append(XLDAlternateOffsetCorrectionEntry.parse(line, i))
                    i += 1
                continue
            break

        accuraterip_summary: list[XLDAccurateRipSummaryEntryWithNo] = []
        if accuraterip_summary_header == c.XLD_ACCURATERIP_SUMMARY_DISC_NOTFOUND_HEADER:
            assert input.readline().rstrip() == c.XLD_ACCURATERIP_SUMMARY_DISC_NOTFOUND_MESSAGE
            accuraterip_disc_id = None
            assert input.readline().rstrip() == ""
        else:
            accuraterip_summary_header = c.XLD_ACCURATERIP_SUMMARY_HEADER_RE.match(accuraterip_summary_header)
            assert accuraterip_summary_header is not None
            accuraterip_disc_id = accuraterip_summary_header.group(1)
            i = 0
            while True:
                line = input.readline().rstrip()
                if line.startswith("    Track "):
                    accuraterip_summary.append(XLDAccurateRipSummaryEntryWithNo.parse(line))
                    i += 1
                    continue
                if line.startswith("        ->"):
                    success_count, fail_count, not_found_count = parse_ripped_count(line[10:])
                    for track in accuraterip_summary:
                        if track.entry is None:
                            not_found_count -= 1
                        elif track.entry.success_summary is not None:
                            success_count -= 1
                        else:
                            fail_count -= 1
                    assert (success_count == 0) or (success_count < _ALL_COUNT)
                    assert (fail_count == 0) or (fail_count < _ALL_COUNT)
                    assert (not_found_count == 0) or (not_found_count < _ALL_COUNT)
                    assert input.readline().rstrip() == ""
                    break
                elif line == "":
                    cancelled = True
                    break
                else:
                    raise Exception("Unknown line: " + line)
        if not cancelled:
            assert input.readline().rstrip() == c.XLD_ALL_TRACKS_HEADER
            all_tracks_summary = XLDTrackStatistics.parse(input)
            assert input.readline().rstrip() == ""
        else:
            all_tracks_summary = None

        tracks: list[XLDTrackEntry | XLDTrackEntryCancelled] = []
        successfly_ripped = False
        while True:
            line = input.readline().rstrip()
            if line == c.XLD_FOOTER_NO_ERROR:
                successfly_ripped = True
                break
            elif line == c.XLD_FOOTER_SOME_ERROR:
                successfly_ripped = False
                break
            elif not line.startswith("Track "):
                raise Exception("Unknown line: " + line)
            track_entry = XLDTrackEntry.parse(line, input)
            if isinstance(track_entry, XLDTrackEntryCancelled):
                assert cancelled
            tracks.append(track_entry)

        return XLDLog(
            xld_version=xld_version,
            log_start_time=log_start_time,
            used_drive=used_drive,
            media_type=media_type,
            artist_and_album_title=artist_and_album_title,
            ripper_mode=ripper_mode,
            disable_audio_cache=disable_audio_cache,
            make_use_of_c2_pointers=make_use_of_c2_pointers,
            read_offset_correction=read_offset_correction,
            max_retry_count=max_retry_count,
            gap_status=gap_status,
            toc=toc,
            alternate_offset_corrections=alternate_offset_corrections,
            accuraterip_disc_id=accuraterip_disc_id,
            accuraterip_summary=accuraterip_summary,
            all_tracks_summary=all_tracks_summary,
            tracks=tracks,
            successfly_ripped=successfly_ripped,
            is_cancelled=cancelled
        )

    def as_log(self, dest: TextIOBase):
        dest.write(c.XLD_VERSION_PREFIX + self.xld_version + "\n\n")
        dest.write(c.XLD_LOG_START_TIME_PREFIX + self.log_start_time.strftime(c.XLD_LOG_START_TIME_FORMAT) + "\n\n")
        dest.write(self.artist_and_album_title + "\n\n")
        dest.write(c.XLD_LOG_USED_DRIVE_PREFIX + self.used_drive + "\n")
        dest.write(c.XLD_LOG_MEDIA_TYPE_PREFIX + self.media_type + "\n\n")
        dest.write(c.XLD_RIPPER_MODE_PREFIX + self.ripper_mode + "\n")
        dest.write(c.XLD_DISABLE_AUDIO_CACHE_PREFIX + self.disable_audio_cache + "\n")
        dest.write(c.XLD_MAKE_USE_OF_C2_POINTERS_PREFIX + ("YES" if self.make_use_of_c2_pointers else "NO") + "\n")
        dest.write(c.XLD_READ_OFFSET_CORRECTION_PREFIX + str(self.read_offset_correction) + "\n")
        dest.write(c.XLD_MAX_RETRY_COUNT_PREFIX + str(self.max_retry_count) + "\n")
        dest.write(c.XLD_GAP_STATUS_PREFIX + self.gap_status + "\n\n")
        dest.write(c.XLD_TOC_HEADER + "\n")
        dest.write(c.XLD_TOC_HEADER_TITLE + "\n")
        dest.write(c.XLD_TOC_HEADER_SEPARATOR + "\n")
        for track in self.toc:
            len_sector = SecondSectorInt(track.end_sector - track.start_sector + 1)
            dest.write("       %2d  | %s | %s |    %6d    |   %6d   \n" % (
                track.no,
                track.start_sector.as_second_sector_str(),
                len_sector.as_second_sector_str(),
                track.start_sector,
                track.end_sector
            ))
        dest.write("\n")
        if len(self.alternate_offset_corrections) > 0:
            dest.write(c.XLD_ALTERNATE_OFFSET_CORRECTION_VALUES_LIST_TITLE + "\n")
            dest.write(c.XLD_ALTERNATE_OFFSET_CORRECTION_VALUES_LIST_TABLE_HEAD + "\n")
            dest.write(c.XLD_ALTERNATE_OFFSET_CORRECTION_VALUES_LIST_TABLE_SEPARATOR + "\n")
            for i, alternate_offset_correction in enumerate(self.alternate_offset_corrections):
                dest.write("      %3d  |   %4d   |   %4d   |     %2d     \n" % (
                    i + 1,
                    alternate_offset_correction.absolute,
                    alternate_offset_correction.relative,
                    alternate_offset_correction.confidence
                ))
            dest.write("\n")
        if self.accuraterip_disc_id is None:
            dest.write(c.XLD_ACCURATERIP_SUMMARY_DISC_NOTFOUND_HEADER + "\n")
            dest.write(c.XLD_ACCURATERIP_SUMMARY_DISC_NOTFOUND_MESSAGE + "\n")
        else:
            dest.write("AccurateRip Summary (DiscID: " + self.accuraterip_disc_id + ")\n")
            assert self.accuraterip_summary is not None
            success_count = 0
            fail_count = 0
            not_found_count = 0
            for track in self.accuraterip_summary:
                dest.write("    Track %02d : " % (track.no,))
                if track.entry is None:
                    not_found_count += 1
                    dest.write("Not Found\n")
                elif track.entry.success_summary is None:
                    fail_count += 1
                    dest.write("NG (total %d submissions)\n" % (track.entry.confidence_total,))
                else:
                    success_count += 1
                    dest.write("OK (")
                    if track.entry.success_summary.v1:
                        dest.write("v1")
                        if track.entry.success_summary.v2:
                            dest.write("+v2")
                    elif track.entry.success_summary.v2:
                        dest.write("v2")
                    else:
                        raise Exception("wrong flags")
                    dest.write(", confidence %d/%d)\n" % (track.entry.success_summary.confidence_used_v2, track.entry.confidence_total))
            if not self.is_cancelled:
                dest.write("        ->")
                if success_count > 0 and fail_count == 0 and not_found_count == 0:
                    dest.write("All tracks accurately ripped.\n")
                else:
                    dest.write("%d track" % (success_count,))
                    if success_count > 1:
                        dest.write("s")
                    dest.write(" accurately ripped")
                    if fail_count > 0:
                        dest.write(", ")
                        dest.write("%d track" % (fail_count,))
                        if fail_count > 1:
                            dest.write("s")
                        dest.write(" not")
                    if not_found_count > 0:
                        dest.write(", ")
                        dest.write("%d track" % (not_found_count,))
                        if not_found_count > 1:
                            dest.write("s")
                        dest.write(" not found")
                    dest.write("\n")
        dest.write("\n")
        if self.all_tracks_summary is not None:
            dest.write(c.XLD_ALL_TRACKS_HEADER + "\n")
            dest.write(c.XLD_TRACK_STATISTICS_HEADER + "\n")
            dest.write(c.XLD_TRACK_STATISTICS_READ_ERROR + str(self.all_tracks_summary.read_error) + "\n")
            dest.write(c.XLD_TRACK_STATISTICS_JITTER_ERROR + str(self.all_tracks_summary.jitter_error) + "\n")
            dest.write(c.XLD_TRACK_STATISTICS_RETRY_SECTOR_COUNT + str(self.all_tracks_summary.retry_sector_count) + "\n")
            dest.write(c.XLD_TRACK_STATISTICS_DAMAGED_SECTOR_COUNT + str(self.all_tracks_summary.damaged_sector_count) + "\n")
            dest.write("\n")
        for track in self.tracks:
            dest.write("Track %02d\n" % (track.no,))
            dest.write(c.XLD_TRACK_FILENAME_HEADER + track.filename + "\n")
            if isinstance(track, XLDTrackEntryCancelled):
                dest.write("    (cancelled by user)\n\n")
                break
            elif not isinstance(track, XLDTrackEntry):
                raise Exception("???")
            if track.pre_gap_length > 0:
                dest.write(c.XLD_TRACK_PRE_GAP_LENGTH_HEADER + track.pre_gap_length.as_second_sector_str() + "\n")
            dest.write("\n")
            dest.write(c.XLD_TRACK_CRC32_HASH_HEADER + track.crc32_hash + "\n")
            dest.write(c.XLD_TRACK_CRC32_SKIP_ZERO_HASH_HEADER + track.crc32_skip_zero_hash + "\n")
            dest.write(c.XLD_TRACK_ACCURATERIP_V1_HEADER + track.accuraterip_v1 + "\n")
            dest.write(c.XLD_TRACK_ACCURATERIP_V2_HEADER + track.accuraterip_v2 + "\n")
            if track.accuraterip_result is None:
                dest.write(c.XLD_TRACK_ACCURATERIP_RESULT_NOTFOUND + "\n")
            elif track.accuraterip_result.success_summary is None:
                dest.write("        ->Rip may not be accurate (total %d submission" % (track.accuraterip_result.confidence_total,))
                if track.accuraterip_result.confidence_total > 1:
                    dest.write("s")
                dest.write(").\n")
            else:
                dest.write("        ->Accurately ripped (")
                if track.accuraterip_result.success_summary.v1:
                    dest.write("v1")
                    if track.accuraterip_result.success_summary.v2:
                        dest.write("+v2")
                elif track.accuraterip_result.success_summary.v2:
                    dest.write("v2")
                else:
                    raise Exception("wrong flags")
                dest.write(", confidence ")
                if track.accuraterip_result.success_summary.confidence_used_v1 > 0:
                    dest.write("%d+" % (track.accuraterip_result.success_summary.confidence_used_v1,))
                dest.write("%d/%d)\n" % (track.accuraterip_result.success_summary.confidence_used_v2, track.accuraterip_result.confidence_total))
            dest.write(c.XLD_TRACK_STATISTICS_HEADER + "\n")
            dest.write(c.XLD_TRACK_STATISTICS_READ_ERROR + str(track.statistics.read_error) + "\n")
            dest.write(c.XLD_TRACK_STATISTICS_JITTER_ERROR + str(track.statistics.jitter_error) + "\n")
            dest.write(c.XLD_TRACK_STATISTICS_RETRY_SECTOR_COUNT + str(track.statistics.retry_sector_count) + "\n")
            dest.write(c.XLD_TRACK_STATISTICS_DAMAGED_SECTOR_COUNT + str(track.statistics.damaged_sector_count) + "\n")
            if len(track.statistics.damaged_sectors) > 0:
                dest.write(c.XLD_TRACK_STATISTICS_LIST_OF_DAMAGED_SECTOR_POSITIONS + "\n")
                for i, sector in enumerate(track.statistics.damaged_sectors):
                    dest.write("            (%d) %s\n" % (i + 1, sector.as_second_sector_str()))
            dest.write("\n")
        if self.successfly_ripped:
            dest.write(c.XLD_FOOTER_NO_ERROR + "\n")
        else:
            dest.write(c.XLD_FOOTER_SOME_ERROR + "\n")
        dest.write("\n")
        dest.write(c.XLD_FOOTER + "\n")
