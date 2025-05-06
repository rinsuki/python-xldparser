import re

SECOND_SECTOR_STR = re.compile(r"^([0-9]{2}):([0-9]{2}):([0-9]{2})$")

SECOND_PER_SECTOR = 75

class SecondSectorInt(int):
    @staticmethod
    def from_second_sector_str(second_sector: str):
        result = SECOND_SECTOR_STR.match(second_sector)
        assert result is not None
        return SecondSectorInt(
            (int(result.group(1)) * 60 * SECOND_PER_SECTOR) +
            (int(result.group(2)) * SECOND_PER_SECTOR) +
            int(result.group(3))
        )

    def as_second_sector_str(self):
        return "%02d:%02d:%02d" % (
            self // SECOND_PER_SECTOR // 60,
            (self // SECOND_PER_SECTOR) % 60,
            self % SECOND_PER_SECTOR
        )
