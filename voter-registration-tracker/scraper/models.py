"""
scraper/models.py
Shared data model for all scrapers.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class RegistrationSnapshot:
    """
    Normalized registration snapshot returned by every state scraper.
    Percentages should sum to ~100. Totals should sum to total_registered.
    """
    state_name:           str
    dem_pct:              float
    rep_pct:              float
    ind_pct:              float
    other_pct:            float
    dem_total:            int
    rep_total:            int
    ind_total:            int
    other_total:          int
    total_registered:     int
    state_published_date: Optional[date]
    source_url:           str

    def validate(self) -> None:
        """Raise ValueError if data looks implausible."""
        pct_sum = self.dem_pct + self.rep_pct + self.ind_pct + self.other_pct
        if not (98.0 <= pct_sum <= 102.0):
            raise ValueError(
                f"{self.state_name}: percentages sum to {pct_sum:.1f}%, expected ~100%"
            )
        total_sum = self.dem_total + self.rep_total + self.ind_total + self.other_total
        if self.total_registered > 0:
            discrepancy = abs(total_sum - self.total_registered) / self.total_registered
            if discrepancy > 0.02:
                raise ValueError(
                    f"{self.state_name}: totals sum to {total_sum:,}, "
                    f"reported total is {self.total_registered:,} "
                    f"({discrepancy*100:.1f}% discrepancy)"
                )
        for pct_field in [self.dem_pct, self.rep_pct, self.ind_pct, self.other_pct]:
            if not (0.0 <= pct_field <= 100.0):
                raise ValueError(f"{self.state_name}: invalid percentage {pct_field}")
