"""Byte-exact output tests for the Commercial Bank generator, plus its
validation guard. No Frappe imports -- runs standalone under ``pytest`` or
``bench run-tests --app eudext_lk``.
"""

import unittest
from decimal import Decimal

from eudext_lk.banking.base import BankFileContext, BankValidationError, PayeeLine
from eudext_lk.banking.commercial_bank import CommercialBankFileGenerator

PAYEES = [
    PayeeLine("A B Perera", "0001234567", "7010", "001", Decimal("8000.00")),
    PayeeLine("C D Silva", "0007654321", "7010", "002", Decimal("12000.00")),
    PayeeLine("E F Fernando", "0009999999", "7056", "010", Decimal("3000.00")),
]


def _context(**overrides):
    defaults = dict(
        bank_name="Commercial Bank of Ceylon",
        format_code="COMBANK_CSV",
        debit_account="8001234567",
        value_date="25/08/2026",
        payees=list(PAYEES),
        delimiter=",",
        has_header=True,
        has_trailer=True,
        amount_in_cents=False,
    )
    defaults.update(overrides)
    return BankFileContext(**defaults)


class TestCommercialBankFileGenerator(unittest.TestCase):
    def test_three_row_batch_exact_bytes(self):
        generator = CommercialBankFileGenerator(_context())
        output = generator.generate()

        expected = (
            "H,8001234567,25/08/2026,3\r\n"
            "D,0001234567,7010,001,8000.00,A B Perera\r\n"
            "D,0007654321,7010,002,12000.00,C D Silva\r\n"
            "D,0009999999,7056,010,3000.00,E F Fernando\r\n"
            "T,3,23000.00\r\n"
        ).encode("utf-8")

        assert output == expected

    def test_amount_in_cents(self):
        generator = CommercialBankFileGenerator(_context(amount_in_cents=True))
        output = generator.generate().decode("utf-8")

        assert "D,0001234567,7010,001,800000,A B Perera" in output
        assert output.strip().endswith("T,3,2300000")

    def test_no_header_no_trailer(self):
        generator = CommercialBankFileGenerator(
            _context(has_header=False, has_trailer=False)
        )
        output = generator.generate().decode("utf-8")
        lines = [l for l in output.split("\r\n") if l]
        assert len(lines) == 3
        assert lines[0].startswith("D,")
        assert lines[-1].startswith("D,")

    def test_missing_bank_details_blocks_generation(self):
        bad_payees = [
            PayeeLine("A B Perera", "", "", "", Decimal("8000.00")),
            PayeeLine("C D Silva", "0007654321", "7010", "002", Decimal("12000.00")),
        ]
        generator = CommercialBankFileGenerator(_context(payees=bad_payees))
        with self.assertRaises(BankValidationError) as ctx:
            generator.generate()
        assert "A B Perera" in str(ctx.exception)
        assert "C D Silva" not in str(ctx.exception)

    def test_empty_batch_blocks_generation(self):
        generator = CommercialBankFileGenerator(_context(payees=[]))
        with self.assertRaises(BankValidationError):
            generator.generate()


if __name__ == "__main__":
    unittest.main()
