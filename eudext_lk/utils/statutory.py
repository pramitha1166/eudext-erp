"""Pure, Frappe-free statutory calculation functions for Sri Lanka payroll.

Every rate/slab is passed in by the caller (sourced from the ``LK Statutory
Config`` DocType or one of its versioned snapshots) so nothing here is
hardcoded. All money arithmetic uses ``decimal.Decimal`` -- never ``float``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Sequence

TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0.00")
HUNDRED = Decimal("100")


def _round_currency(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class StatutoryRates:
    """Snapshot of the contribution rates in effect for a payroll period."""

    employee_epf_rate: Decimal
    employer_epf_rate: Decimal
    etf_rate: Decimal


@dataclass(frozen=True)
class APITSlab:
    """One row of a progressive APIT slab table.

    ``to_amount`` of ``None`` means "and above" (the top, open-ended slab).
    """

    from_amount: Decimal
    to_amount: Optional[Decimal]
    rate: Decimal  # percentage, e.g. Decimal("6") for 6%


def calc_epf_employee(gross: Decimal, config: StatutoryRates) -> Decimal:
    """Employee's EPF contribution (typically 8% of EPF-eligible gross)."""
    if gross <= 0:
        return ZERO
    return _round_currency(gross * config.employee_epf_rate / HUNDRED)


def calc_epf_employer(gross: Decimal, config: StatutoryRates) -> Decimal:
    """Employer's EPF contribution (typically 12% of EPF-eligible gross)."""
    if gross <= 0:
        return ZERO
    return _round_currency(gross * config.employer_epf_rate / HUNDRED)


def calc_etf(gross: Decimal, config: StatutoryRates) -> Decimal:
    """Employer's ETF contribution (typically 3% of EPF-eligible gross)."""
    if gross <= 0:
        return ZERO
    return _round_currency(gross * config.etf_rate / HUNDRED)


def calc_apit(taxable_amount: Decimal, slabs: Sequence[APITSlab]) -> Decimal:
    """Progressive APIT (PAYE) tax on ``taxable_amount`` given slab config.

    ``slabs`` are consumed as provided -- no assumption is made here about
    whether they are monthly or annualised; that decision belongs to the
    caller assembling the config for a given payroll period.
    """
    if taxable_amount <= 0 or not slabs:
        return ZERO

    tax = Decimal("0")
    for slab in sorted(slabs, key=lambda s: s.from_amount):
        if taxable_amount <= slab.from_amount:
            continue
        upper = slab.to_amount if slab.to_amount is not None else taxable_amount
        upper = min(upper, taxable_amount)
        taxable_in_slab = upper - slab.from_amount
        if taxable_in_slab <= 0:
            continue
        tax += taxable_in_slab * slab.rate / HUNDRED
    return _round_currency(tax)


def calc_gratuity(
    basic: Decimal,
    years_service: Decimal,
    min_qualifying_years: Decimal = Decimal("5"),
) -> Decimal:
    """Gratuity under the Payment of Gratuity Act No. 12 of 1983: half a
    month's basic salary for each completed year of service, payable only
    once the minimum qualifying period has been completed.
    """
    if basic <= 0 or years_service < min_qualifying_years:
        return ZERO
    return _round_currency(basic * Decimal("0.5") * years_service)
