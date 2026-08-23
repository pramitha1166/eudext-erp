"""Commercial Bank of Ceylon bulk-payment CSV generator.

Format assumed for manual portal upload (not a direct bank API):

    H<d>{debit_account}<d>{value_date}<d>{record_count}
    D<d>{account_no}<d>{bank_code}<d>{branch_code}<d>{amount}<d>{party_name}
    ...
    T<d>{record_count}<d>{total_amount}

where ``<d>`` is the configured delimiter (comma by default), amounts are
formatted per ``LK Bank File Format.amount_format`` (decimal or cents), and
lines are terminated CRLF. To add another bank, subclass
``BankFileGenerator`` and decorate it with ``@register_generator("<code>")``
matching the ``format_code`` on the corresponding ``LK Bank File Format``
record -- see README.md.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from eudext_lk.banking.base import (
    BankFileGenerator,
    BankValidationError,
    register_generator,
)

FORMAT_CODE = "COMBANK_CSV"


@register_generator(FORMAT_CODE)
class CommercialBankFileGenerator(BankFileGenerator):
    def validate(self) -> None:
        ctx = self.context
        if not ctx.debit_account:
            raise BankValidationError("Debit account is required")
        if not ctx.payees:
            raise BankValidationError("At least one payee line is required")

        missing = []
        for payee in ctx.payees:
            if not (payee.account_no and payee.bank_code and payee.branch_code):
                missing.append(payee.party_name)
            elif payee.amount is None or payee.amount <= 0:
                missing.append(payee.party_name)
        if missing:
            raise BankValidationError(
                "Missing/invalid bank details for: " + ", ".join(missing)
            )

    def build_header(self) -> Optional[str]:
        if not self.context.has_header:
            return None
        d = self.context.delimiter
        return d.join(
            [
                "H",
                self.context.debit_account,
                self.context.value_date,
                str(len(self.context.payees)),
            ]
        )

    def build_rows(self) -> List[str]:
        d = self.context.delimiter
        return [
            d.join(
                [
                    "D",
                    payee.account_no,
                    payee.bank_code,
                    payee.branch_code,
                    self._format_amount(payee.amount),
                    payee.party_name,
                ]
            )
            for payee in self.context.payees
        ]

    def build_trailer(self) -> Optional[str]:
        if not self.context.has_trailer:
            return None
        d = self.context.delimiter
        total = sum((p.amount for p in self.context.payees), Decimal("0"))
        return d.join(["T", str(len(self.context.payees)), self._format_amount(total)])

    def _format_amount(self, amount: Decimal) -> str:
        if self.context.amount_in_cents:
            cents = (amount * 100).to_integral_value()
            return str(int(cents))
        return f"{amount:.2f}"
