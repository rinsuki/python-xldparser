
from dataclasses import dataclass
from .second_sector import SecondSectorInt

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
