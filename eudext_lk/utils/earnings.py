"""Pure helpers for deriving EPF-eligible gross pay from a salary slip's
earnings rows. No Frappe imports -- works against any duck-typed object
(a real ``Salary Slip`` document, a ``frappe._dict``, or a plain dict/list
used in tests).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterable, Set

TWO_PLACES = Decimal("0.01")


def _get(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def epf_eligible_gross(salary_slip: Any, eligible_components: Set[str]) -> Decimal:
    """Sum the amounts of every earnings row whose salary component is in
    ``eligible_components`` (the whitelist maintained on ``LK Statutory
    Config``). Components not on the whitelist -- overtime, bonuses,
    reimbursements, and anything else the config excludes -- are skipped.

    ``salary_slip`` need only expose an ``earnings`` iterable of rows that
    each carry ``salary_component`` and ``amount``.
    """
    earnings: Iterable[Any] = _get(salary_slip, "earnings", []) or []
    total = Decimal("0")
    for row in earnings:
        component = _get(row, "salary_component")
        if component not in eligible_components:
            continue
        amount = _get(row, "amount", 0) or 0
        total += Decimal(str(amount))
    return total.quantize(TWO_PLACES)
