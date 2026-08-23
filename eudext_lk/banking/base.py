"""Abstract base for bank payment file generators, plus a format_code
registry so new banks are added by writing a class and registering it --
never by branching on bank name in application code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Type

NEWLINE = "\r\n"


@dataclass
class PayeeLine:
    party_name: str
    account_no: str
    bank_code: str
    branch_code: str
    amount: Decimal
    reference: str = ""


@dataclass
class BankFileContext:
    """Everything a generator needs, assembled from ``LK Bank File Format``
    and ``LK Bulk Payment Batch`` by the caller -- generators never touch
    Frappe documents directly.
    """

    bank_name: str
    format_code: str
    debit_account: str
    value_date: str
    payees: List[PayeeLine]
    delimiter: str = ","
    has_header: bool = True
    has_trailer: bool = True
    amount_in_cents: bool = False
    extra: dict = field(default_factory=dict)


class BankValidationError(ValueError):
    """Raised by a generator's ``validate`` step; callers should surface the
    message to the user (e.g. the list of payee lines missing bank details).
    """


class BankFileGenerator(ABC):
    """Template-method generator: ``generate()`` always runs the same
    pipeline -- validate, build_header, build_rows, build_trailer, render --
    concrete banks only implement the steps that differ.
    """

    format_code: str = ""

    def __init__(self, context: BankFileContext):
        self.context = context

    def generate(self) -> bytes:
        self.validate()
        lines: List[str] = []
        header = self.build_header()
        if header is not None:
            lines.append(header)
        lines.extend(self.build_rows())
        trailer = self.build_trailer()
        if trailer is not None:
            lines.append(trailer)
        return self.render(lines)

    @abstractmethod
    def validate(self) -> None:
        """Raise ``BankValidationError`` if the context cannot be rendered."""

    @abstractmethod
    def build_header(self) -> Optional[str]:
        ...

    @abstractmethod
    def build_rows(self) -> List[str]:
        ...

    @abstractmethod
    def build_trailer(self) -> Optional[str]:
        ...

    def render(self, lines: List[str]) -> bytes:
        if not lines:
            return b""
        return (NEWLINE.join(lines) + NEWLINE).encode("utf-8")


GENERATOR_REGISTRY: Dict[str, Type[BankFileGenerator]] = {}


def register_generator(format_code: str):
    def _wrap(cls: Type[BankFileGenerator]) -> Type[BankFileGenerator]:
        cls.format_code = format_code
        GENERATOR_REGISTRY[format_code] = cls
        return cls

    return _wrap


def get_generator(format_code: str) -> Type[BankFileGenerator]:
    try:
        return GENERATOR_REGISTRY[format_code]
    except KeyError:
        raise BankValidationError(
            f"No bank file generator registered for format_code '{format_code}'"
        )
