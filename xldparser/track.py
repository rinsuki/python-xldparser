from dataclasses import dataclass
from io import TextIOBase
from . import constants as c
from .second_sector import SecondSectorInt

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
class XLDAccurateRipSuccessResult:
    v1: bool
    v2: bool
    confidence_used_v1: int
    confidence_used_v2: int
    offset: int

    @staticmethod
    def parse(line: str, with_different_offset: bool):
        match_result = (c.XLD_TRACK_ACCURATERIP_RESULT_SUCCESS_WITH_DIFFERENT_OFFSET_DETAIL_RE if with_different_offset else c.XLD_TRACK_ACCURATERIP_RESULT_SUCCESS_DETAIL_RE).match(line)
        assert match_result is not None
        v1 = match_result.group(1) == "v1" or match_result.group(1) == "v1+v2"
        v2 = match_result.group(1) == "v2" or match_result.group(1) == "v1+v2"
        if match_result.group(2) is not None:
            confidence_used_v1 = int(match_result.group(2)[:-1])
        else:
            confidence_used_v1 = 0
        confidence_used_v2 = int(match_result.group(3))
        if v1 and not v2:
            confidence_used_v1 = confidence_used_v2
            confidence_used_v2 = 0
        confidence_total = int(match_result.group(4))
        offset = match_result.group(5) if with_different_offset else None
        if offset is not None:
            if offset.startswith("+"):
                offset = int(offset[1:])
            else:
                offset = int(offset)
            assert offset != 0
        else:
            offset = 0
        return XLDAccurateRipSuccessResult(v1=v1, v2=v2, confidence_used_v1=confidence_used_v1, confidence_used_v2=confidence_used_v2, offset=offset), confidence_total

@dataclass
class XLDAccurateRipResultEntry:
    success_summary: XLDAccurateRipSuccessResult | None
    confidence_total: int

    @staticmethod
    def parse_track(line: str, with_different_offset: bool):
        if line == c.XLD_TRACK_ACCURATERIP_RESULT_NOTFOUND:
            return None
        success_match = (c.XLD_TRACK_ACCURATERIP_RESULT_SUCCESS_WITH_DIFFERENT_OFFSET_RE if with_different_offset else c.XLD_TRACK_ACCURATERIP_RESULT_SUCCESS_RE).match(line)
        if success_match is not None:
            success_summary, confidence_total = XLDAccurateRipSuccessResult.parse(success_match.group(1), with_different_offset)
        else:
            fail_match = c.XLD_TRACK_ACCURATERIP_RESULT_FAIL_RE.match(line)
            if fail_match is None:
                raise Exception("Unknown line: " + line)
            confidence_total = int(fail_match.group(1))
            success_summary = None
        return XLDAccurateRipResultEntry(success_summary=success_summary, confidence_total=confidence_total)

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
    accuraterip_v1_with_correction: str | None
    accuraterip_v2: str
    accuraterip_v2_with_correction: str | None
    accuraterip_result: XLDAccurateRipResultEntry | None
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
        accuraterip_v1 = c.XLD_TRACK_ACCURATERIP_HASH_RE.match(accuraterip_v1[len(c.XLD_TRACK_ACCURATERIP_V1_HEADER):])
        assert accuraterip_v1 is not None
        accuraterip_v1_with_correction = accuraterip_v1.group(2)
        accuraterip_v1 = accuraterip_v1.group(1)

        accuraterip_v2 = line.readline().rstrip()
        assert accuraterip_v2.startswith(c.XLD_TRACK_ACCURATERIP_V2_HEADER)
        accuraterip_v2 = c.XLD_TRACK_ACCURATERIP_HASH_RE.match(accuraterip_v2[len(c.XLD_TRACK_ACCURATERIP_V2_HEADER):])
        assert accuraterip_v2 is not None
        accuraterip_v2_with_correction = accuraterip_v2.group(2)
        accuraterip_v2 = accuraterip_v2.group(1)

        # If one of them is (not) found, the other must be (not) found.
        # TODO: this might be wrong
        if accuraterip_v1_with_correction is None:
            assert accuraterip_v2_with_correction is None
        else:
            assert accuraterip_v2_with_correction is not None

        accuraterip_result = XLDAccurateRipResultEntry.parse_track(line.readline().rstrip(), with_different_offset=accuraterip_v1_with_correction is not None or accuraterip_v2_with_correction is not None)
        statistics = XLDPerTrackStatistics.parse(line)
        return XLDTrackEntry(
            no=no,
            filename=filename,
            pre_gap_length=pre_gap_length,
            crc32_hash=crc32_hash,
            crc32_skip_zero_hash=crc32_skip_zero_hash,
            accuraterip_v1=accuraterip_v1,
            accuraterip_v1_with_correction=accuraterip_v1_with_correction,
            accuraterip_v2=accuraterip_v2,
            accuraterip_v2_with_correction=accuraterip_v2_with_correction,
            accuraterip_result=accuraterip_result,
            statistics=statistics
        )