from dataclasses import dataclass


@dataclass(frozen=True)
class SectorConstituent:
    sector: str
    ticker: str
    name: str
    shares_base: float
