# eudext_lk

Sri Lanka statutory localisation for ERPNext / Frappe HR (hrms) — EPF, ETF,
APIT (PAYE) payroll calculations, gratuity, and bank payment file
generation. Built entirely as a Frappe custom app: **no file under
`apps/erpnext/` or `apps/hrms/` is ever modified.** Everything here extends
ERPNext/HRMS through hooks, Custom Fields, new DocTypes, and Salary
Component formulas.

## Stack

Frappe Framework v15, ERPNext v15, Frappe HR (hrms) v15, Python 3.11,
MariaDB 10.6+.

## Install

```bash
cd ~/frappe-bench
bench get-app eudext_lk /path/to/eudext_lk   # or a git URL
bench --site eudext.local install-app eudext_lk
bench --site eudext.local migrate
```

`install-app` pulls in `erpnext` and `hrms` automatically via
`required_apps` in `hooks.py` if they are not already installed.

After install, open **LK Statutory Config** (Setup) and fill in:

- Employee / Employer EPF rate, ETF rate, `effective_from`
- APIT slabs (from/to/rate rows)
- The list of Salary Components counted towards EPF-eligible gross

Saving publishes a dated snapshot to **LK Statutory Config Version**, so
changing a rate never rewrites history -- payroll runs for past periods
keep using the rates that were actually in force then.

## The extension-only rule

This app must never edit `apps/erpnext/` or `apps/hrms/` source. Every
touchpoint is one of:

- **Custom Fields** (shipped as fixtures) -- `Employee.epf_number`,
  `Employee.bank_code`/`branch_code`/`bank_account_no`,
  `Supplier.bank_code`/`branch_code`/`bank_account_no`,
  `Salary Component.lk_epf_eligible`.
- **New DocTypes** -- everything under `eudext_lk/eudext_lk/doctype/`.
- **`doc_events` hooks** -- `Salary Slip.validate` and
  `Payroll Entry.on_submit` (see `hooks.py`), never a monkey-patched
  controller method.
- **Salary Component formulas** that call whitelisted methods in
  `payroll/formulas.py` -- the component definitions themselves are
  fixtures, not code changes to HRMS.

If a change ever seems to require editing `erpnext` or `hrms` directly,
that is a sign the right extension point hasn't been found yet -- ask
before reaching for a fork.

## Where the numbers come from

All rates and slabs are data, not code:

- `LK Statutory Config` (Single) is what admins edit.
- Saving it publishes/updates a matching `LK Statutory Config Version`
  record, keyed by `effective_from`.
- `tax/rates.py` resolves *which* version applies to a given payroll date
  (the latest version with `effective_from <= date`, falling back to the
  live Single if no version has been published yet) and hands plain
  `StatutoryRates` / `APITSlab` dataclasses to the calculators.
- `utils/statutory.py` and `utils/earnings.py` contain the actual maths --
  pure functions, `Decimal` only, no Frappe import, fully unit-testable
  (`tests/test_statutory.py`, `tests/test_bank_file.py`).

Changing next year's budget rates is therefore a record edit in the UI,
never a deployment.

### EPF-eligible gross

`Salary Component.lk_epf_eligible` is a quick visual marker for HR staff.
The value the payroll calculation actually reads is the whitelist on
**LK Statutory Config → EPF-Eligible Earning Components**, because that
table is versioned along with the rates (a checkbox on a component record
has no history). Overtime, bonuses, and reimbursements are excluded simply
by not adding them to that whitelist.

### Salary Slip calculation flow

1. HRMS evaluates every Salary Component's `formula` as usual. The four LK
   statutory components (`EPF Employee 8%`, `EPF Employer 12%`, `ETF 3%`,
   `APIT`) have formulas that call the whitelisted methods in
   `payroll/formulas.py`, which in turn call `utils/statutory.py` -- so
   even the live formula preview is rate-config-driven.
2. `doc_events["Salary Slip"]["validate"]`
   (`payroll/salary_slip.py:inject_statutory_amounts`) then runs
   *after* HRMS's own calculation. It has access to the full earnings
   breakdown, computes EPF-eligible gross via `utils/earnings.py`, and
   overwrites the four component rows with the authoritative amount --
   this is what actually lands on the slip, the formula step above is a
   convenience preview only.
3. `EPF Employer 12%` and `ETF 3%` are `type=Deduction` with
   `do_not_include_in_total=1`, ERPNext's standard way of showing a
   component as a row on the payslip without it reducing net pay -- the
   correct fit for an employer-side contribution the employee should still
   see. (`statistical_component=1` was deliberately *not* used here: HRMS
   never adds a statistical component as a row to the slip at all, it only
   keeps the value available for other components' formulas to reference.)
   Building a Salary Structure through the Desk UI copies `formula` and
   `do_not_include_in_total` from the Salary Component master onto the
   structure's row automatically when you pick a component from the
   dropdown (`salary_structure.js`); if you ever assemble a Salary
   Structure via the API/a script instead, copy those two fields across
   yourself the same way.

## Bank payment files

`LK Bank File Format` describes a bank's file layout (delimiter, header,
trailer, date/amount format). `LK Bulk Payment Batch` (submittable) holds
the payee lines -- pulled from a `Payroll Entry`'s submitted Salary Slips
via the *"Create an LK Bulk Payment Batch"* link that
`Payroll Entry.on_submit` offers -- and its **Generate File** button calls
the whitelisted `generate_file` method, which:

1. Refuses to run if any payee line is missing account number, bank code,
   or branch code, listing the offending row numbers.
2. Looks up the generator class registered for the format's `format_code`.
3. Builds the file and attaches it to the batch as a private File.

### `banking/base.py`

`BankFileGenerator` is an abstract template: `generate()` always runs
`validate -> build_header -> build_rows -> build_trailer -> render` in that
order; a concrete bank only implements those four steps. Generators
self-register into `GENERATOR_REGISTRY` via `@register_generator(code)`,
keyed by `LK Bank File Format.format_code`.

### Adding a new bank format

1. Create the `LK Bank File Format` record with its `format_code`,
   delimiter, header/trailer flags, date/amount format.
2. Add `banking/<bank>.py` subclassing `BankFileGenerator`:

   ```python
   from eudext_lk.banking.base import BankFileGenerator, register_generator

   @register_generator("YOUR_FORMAT_CODE")
   class YourBankFileGenerator(BankFileGenerator):
       def validate(self): ...
       def build_header(self): ...
       def build_rows(self): ...
       def build_trailer(self): ...
   ```

3. Import that module once from `doctype/lk_bulk_payment_batch/lk_bulk_payment_batch.py`
   (next to the existing `commercial_bank` import) so the registration
   runs at load time.
4. Add byte-exact tests in `tests/test_bank_file.py` the same way
   `CommercialBankFileGenerator` is tested.

The first implementation, `banking/commercial_bank.py` (`COMBANK_CSV`),
targets a delimited file for manual upload to the bank's own payment
portal -- not a direct bank API integration.

## Updating statutory rates

Open **LK Statutory Config**, edit the rate/slab/whitelist fields, save.
That's it -- no code change, no deployment. The save publishes a new
`LK Statutory Config Version` snapshot dated by `effective_from`, so any
payroll already run for an earlier period is unaffected the next time it
is recalculated.

## Reports

- **LK EPF Return (C Form)** -- per-employee EPF-eligible gross, employee
  and employer EPF contributions for submitted Salary Slips in a period.
- **LK ETF Return** -- the same, for the employer ETF contribution.

Both are Script Reports under Setup > Reports, filterable by company,
date range, and employee.

## Tests

```bash
bench --site eudext.local run-tests --app eudext_lk
```

`tests/test_statutory.py` and `tests/test_bank_file.py` import only the
`utils/` and `banking/` modules -- no Frappe, no database -- so they also
run under plain `pytest` from the app's root directory.

## Assumptions

- ERPNext / hrms `version-15` branch.
- Commercial Bank of Ceylon is the first bank format
  (`banking/commercial_bank.py`, `COMBANK_CSV`); others are added the same
  way as demand arises.
- Generated files are for manual upload to a bank's payment portal, not a
  direct bank API integration.
- APIT is computed as a straightforward progressive slab calculation over
  whatever taxable amount and slabs are configured; it does not attempt to
  replicate every nuance of the official APIT computation rules (secondary
  employment, cumulative relief, etc.) -- treat `utils/statutory.calc_apit`
  as the slab engine and encode any additional policy in the slabs/config
  around it.
