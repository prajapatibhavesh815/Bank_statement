"""
Universal Adaptive Bank Statement Parser.
Extracts transactions from text-based tables or raw lines using intelligent
multi-pattern column header mapping, dynamic content-based column profiling,
multi-line narration merging, and mathematical debit/credit deduction.
Completely dynamic — does not rely on hardcoded bank assumptions.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from ..base_extractor import BaseExtractor
from ...models.schemas import Transaction


class GenericBankParser:
    """
    Adaptive universal parser capable of dynamically extracting transactions
    from ANY bank statement layout worldwide.
    """

    DATE_SYNONYMS = [
        "txn date", "trans date", "transaction date", "value date", "val date",
        "val dt", "post date", "posting date", "booking date", "effective date",
        "date of transaction", "txn dt", "trans dt", "date", "dt"
    ]
    DESC_SYNONYMS = [
        "narration", "description", "particulars", "transaction details",
        "transaction remarks", "details", "remarks", "memo", "payee",
        "payment details", "narrative", "activity", "desc", "transaction description"
    ]
    CHQ_SYNONYMS = [
        "chq / ref no", "chq./ref.no.", "chq/ref no", "cheque no", "ref no",
        "reference no", "reference number", "instrument no", "utr", "trans id",
        "txn id", "chq no", "cheque", "ref", "reference", "check #", "doc no",
        "seq no", "voucher no"
    ]
    DEBIT_SYNONYMS = [
        "withdrawal amt.", "withdrawal amt", "withdrawal amount", "withdrawals",
        "withdrawal", "debit amount", "debit amt", "debit", "dr amt",
        "dr amount", "payments", "paid out", "money out", "dr.", "dr"
    ]
    CREDIT_SYNONYMS = [
        "deposit amt.", "deposit amt", "deposit amount", "deposits",
        "deposit", "credit amount", "credit amt", "credit", "cr amt",
        "cr amount", "receipts", "paid in", "money in", "cr.", "cr"
    ]
    AMOUNT_SYNONYMS = [
        "transaction amount", "txn amount", "net amount", "amount", "amt",
        "trans amount", "total amount"
    ]
    TYPE_SYNONYMS = [
        "cr/dr", "dr/cr", "cr / dr", "dr / cr", "txn type", "trans type",
        "type", "c/d", "d/c", "sign", "indicator"
    ]
    BALANCE_SYNONYMS = [
        "closing balance", "running balance", "net balance", "available balance",
        "book balance", "closing bal", "balance", "bal.", "bal"
    ]

    @classmethod
    def identify_column_indices(cls, header_row: List[str]) -> Dict[str, int]:
        """
        Dynamically maps normalized header names to column index positions using regex.
        Supports single-word, multi-word, and abbreviated headers.
        """
        col_map: Dict[str, int] = {}
        cleaned_headers = [str(c).strip().lower() if c else "" for c in header_row]

        for idx, h in enumerate(cleaned_headers):
            if not h:
                continue

            # 1. Dr/Cr Type Indicator column (must be checked BEFORE debit/credit)
            if any(th in h for th in ["cr/dr", "dr/cr", "cr / dr", "dr / cr", "c/d", "d/c"]) or (re.search(r"\btype\b", h) and "amount" not in h):
                if "type" not in col_map:
                    col_map["type"] = idx
                    continue

            # 2. Balance check (must take priority over simple debit/credit terms)
            if ("balance" in h or "closing" in h or re.search(r"\bbal\b", h)) and "balance" not in col_map:
                col_map["balance"] = idx
                continue

            # 3. Debit check (protect against 'dr/cr' and words like 'driver')
            if "cr" not in h and (any(dh in h for dh in ["withdrawal", "withdrawals", "debit", "paid out", "money out"]) or re.search(r"\bdr\b|\bdr\s*amt\b", h)):
                if "debit" not in col_map:
                    col_map["debit"] = idx
                    continue

            # 4. Credit check (protect against 'dr/cr' and 'cr' in 'description')
            if "dr" not in h and (any(ch in h for ch in ["deposit", "deposits", "credit", "paid in", "money in"]) or re.search(r"\bcr\b|\bcr\s*amt\b", h)):
                if "credit" not in col_map:
                    col_map["credit"] = idx
                    continue

            # 5. Description check
            if any(desc in h for desc in ["description", "narration", "particular", "remark", "detail", "memo", "narrative", "activity"]) or re.search(r"\bdesc\b", h):
                if "desc" not in col_map:
                    col_map["desc"] = idx
                    continue

            # 6. Reference / Cheque
            if any(rh in h for rh in ["ref", "chq", "cheque", "utr", "instrument", "trans id", "txn id", "check #", "doc no", "seq no"]):
                if "ref" not in col_map:
                    col_map["ref"] = idx
                    continue

            # 7. Date check
            if any(dh in h for dh in ["date", "txn dt", "val dt", "post dt", "booking dt"]) or re.search(r"\bdt\b", h):
                if "date" not in col_map:
                    col_map["date"] = idx
                    continue

            # 8. Single Amount check
            if any(ah in h for ah in ["amount", "amt"]) and "amount" not in col_map and "debit" not in col_map and "credit" not in col_map:
                col_map["amount"] = idx
                continue

        return col_map

    @classmethod
    def profile_columns_dynamically(cls, rows: List[List[Any]]) -> Dict[str, int]:
        """
        Dynamically infers column roles by inspecting the distribution of cell values
        across all data rows. Used when table headers are missing, abnormal, or obscured.
        """
        if not rows:
            return {}

        num_cols = max(len(r) for r in rows if r)
        col_date_counts = [0] * num_cols
        col_numeric_counts = [0] * num_cols
        col_text_lengths = [0] * num_cols
        total_rows = len(rows)

        for row in rows:
            for idx in range(num_cols):
                if idx < len(row) and row[idx] is not None:
                    cell_val = str(row[idx]).strip()
                    if not cell_val:
                        continue
                    # Check date
                    iso_d, _ = BaseExtractor.parse_date(cell_val)
                    if iso_d:
                        col_date_counts[idx] += 1
                    # Check monetary number
                    cleaned_num = cell_val.replace(",", "").replace("₹", "").replace("$", "").strip()
                    if re.match(r"^-?\d+(\.\d{1,2})?(?:\s*(?:dr|cr))?$", cleaned_num, re.IGNORECASE):
                        col_numeric_counts[idx] += 1
                    col_text_lengths[idx] += len(cell_val)

        col_map: Dict[str, int] = {}

        # 1. Date column: column with highest date count (must be > 20% of rows)
        best_date_idx = max(range(num_cols), key=lambda i: col_date_counts[i])
        if col_date_counts[best_date_idx] >= max(1, total_rows * 0.2):
            col_map["date"] = best_date_idx

        # 2. Description column: column with highest text length among non-date columns
        non_date_indices = [i for i in range(num_cols) if i != col_map.get("date")]
        if non_date_indices:
            best_desc_idx = max(non_date_indices, key=lambda i: col_text_lengths[i])
            col_map["desc"] = best_desc_idx

        # 3. Numeric columns (potential debit, credit, amount, balance)
        numeric_candidates = [
            i for i in range(num_cols)
            if i != col_map.get("date") and i != col_map.get("desc") and col_numeric_counts[i] > 0
        ]
        numeric_candidates.sort()

        if len(numeric_candidates) >= 3:
            # Layout: [Debit, Credit, Balance]
            col_map["debit"] = numeric_candidates[-3]
            col_map["credit"] = numeric_candidates[-2]
            col_map["balance"] = numeric_candidates[-1]
        elif len(numeric_candidates) == 2:
            # Layout: [Amount, Balance]
            col_map["amount"] = numeric_candidates[0]
            col_map["balance"] = numeric_candidates[1]
        elif len(numeric_candidates) == 1:
            col_map["balance"] = numeric_candidates[0]

        return col_map

    @classmethod
    def parse_table_rows(cls, table: List[List[Any]]) -> List[Transaction]:
        """
        Parses structured table rows into Transaction objects.
        Automatically detects single-line or multi-line headers, profiles column types,
        resolves wrapped narrations, and computes debit/credit amounts.
        """
        if not table or len(table) < 2:
            return []

        # If table has fewer than 3 columns, it's a summary/metadata card, not transactions
        max_cols = max(len(row) for row in table if row)
        if max_cols < 3:
            return []

        # Find header row (check single rows and merged 2-row combinations)
        header_idx = -1
        col_map: Dict[str, int] = {}

        for i, row in enumerate(table[:15]):
            if not row:
                continue
            row_str = " ".join([str(c or "").lower() for c in row])

            # Check single row header
            if any(d in row_str for d in ["date", "particulars", "narration", "description"]) and \
               any(m in row_str for m in ["balance", "debit", "withdrawal", "credit", "deposit", "amount"]):
                header_idx = i
                col_map = cls.identify_column_indices(row)
                break

            # Check 2-row combination (wrapped headers)
            if i + 1 < len(table):
                next_row = table[i + 1]
                combined_row = [f"{c or ''} {next_row[idx] if idx < len(next_row) and next_row[idx] else ''}".strip() for idx, c in enumerate(row)]
                comb_str = " ".join([c.lower() for c in combined_row])
                if any(d in comb_str for d in ["date", "particulars", "narration", "description"]) and \
                   any(m in comb_str for m in ["balance", "debit", "withdrawal", "credit", "deposit", "amount"]):
                    header_idx = i + 1
                    col_map = cls.identify_column_indices(combined_row)
                    break

        # Fallback to dynamic column profiling if header wasn't found or missing date
        if header_idx == -1 or "date" not in col_map:
            candidate_rows = table[1:] if len(table) > 1 else table
            col_map = cls.profile_columns_dynamically(candidate_rows)
            header_idx = 0 if "date" in col_map else -1

        # Extract statement year context from table cells for 2-part dates
        table_full_text = " ".join([str(c or "") for r in table for c in r])
        statement_year = BaseExtractor.extract_statement_year(table_full_text)

        if "date" not in col_map:
            return cls.parse_rows_positional_fallback(table, fallback_year=statement_year)

        transactions: List[Transaction] = []
        current_txn: Optional[Transaction] = None

        date_idx = col_map.get("date", 0)
        desc_idx = col_map.get("desc", 1)
        ref_idx = col_map.get("ref", -1)
        debit_idx = col_map.get("debit", -1)
        credit_idx = col_map.get("credit", -1)
        amount_idx = col_map.get("amount", -1)
        type_idx = col_map.get("type", -1)
        bal_idx = col_map.get("balance", -1)

        # Check if table or header has a single direction (e.g. section-based table for deposits or debits)
        header_text = " ".join([str(c or "") for c in (table[header_idx] if 0 <= header_idx < len(table) else [])]).lower()
        table_prefix_text = " ".join([str(c or "") for r in table[:max(1, header_idx)] for c in r]).lower()
        combined_hdr_ctx = header_text + " " + table_prefix_text

        section_direction = None
        if debit_idx == -1 and credit_idx == -1 and amount_idx >= 0:
            if any(k in combined_hdr_ctx for k in ["deposit", "credit", "money in", "paid in"]):
                section_direction = "CREDIT"
            elif any(k in combined_hdr_ctx for k in ["withdrawal", "debit", "money out", "paid out", "check", "cheque"]):
                section_direction = "DEBIT"

        start_row = max(0, header_idx + 1)
        for row in table[start_row:]:
            if not row or all(c is None or str(c).strip() == "" for c in row):
                continue

            def get_cell(idx: int) -> str:
                if 0 <= idx < len(row) and row[idx] is not None:
                    return str(row[idx]).strip()
                return ""

            # Check if this row is a repeated header across page breaks
            row_concat = " ".join(get_cell(i).lower() for i in range(len(row)))
            if any(h in row_concat for h in ["transaction date", "txn date", "narration", "particulars"]) and \
               any(m in row_concat for m in ["balance", "withdrawal", "deposit"]):
                continue

            # Discard non-transaction summary, carried over, and footer rows
            if any(skip in row_concat for skip in ["balance forward", "carried forward", "brought forward", "page total", "statement summary", "total amount", "grand total", "reward points"]) or re.match(r"^\s*total\b", row_concat):
                continue

            date_val = get_cell(date_idx)
            std_date, raw_date = BaseExtractor.parse_date(date_val, fallback_year=statement_year)

            # Is this row starting a new transaction?
            if std_date and re.search(r"\d", std_date):
                if current_txn and (current_txn.debit > 0 or current_txn.credit > 0 or current_txn.balance > 0):
                    transactions.append(current_txn)

                raw_desc = get_cell(desc_idx)
                cleaned_desc = " ".join(raw_desc.split()) if raw_desc else ""
                # Reconnect broken single-letter wraps (e.g. 'Z EPTO' -> 'ZEPTO', 'S WIGGY' -> 'SWIGGY')
                cleaned_desc = re.sub(r"\b([A-Za-z])\s+([A-Za-z]{3,}\b)", r"\1\2", cleaned_desc)
                ref_val = get_cell(ref_idx) if ref_idx >= 0 else None

                # Debit / Credit calculation
                debit_val = 0.0
                credit_val = 0.0

                if debit_idx >= 0:
                    debit_val = BaseExtractor.clean_amount(get_cell(debit_idx))
                if credit_idx >= 0:
                    credit_val = BaseExtractor.clean_amount(get_cell(credit_idx))

                # Handle single Amount column
                if debit_val == 0.0 and credit_val == 0.0 and amount_idx >= 0:
                    amt_str = get_cell(amount_idx)
                    parsed_amt = BaseExtractor.clean_amount(amt_str)
                    type_str = get_cell(type_idx).lower() if type_idx >= 0 else ""

                    if section_direction == "CREDIT":
                        credit_val = abs(parsed_amt)
                    elif section_direction == "DEBIT":
                        debit_val = abs(parsed_amt)
                    elif "cr" in type_str or "cr" in amt_str.lower() or (parsed_amt > 0 and ("+" in amt_str)):
                        credit_val = abs(parsed_amt)
                    elif "dr" in type_str or "dr" in amt_str.lower() or parsed_amt < 0:
                        debit_val = abs(parsed_amt)
                    else:
                        # Deduce direction using running balance progression
                        current_bal_temp = BaseExtractor.clean_amount(get_cell(bal_idx)) if bal_idx >= 0 else 0.0
                        if current_txn and current_txn.balance > 0 and current_bal_temp > 0:
                            if current_bal_temp > current_txn.balance + 0.01:
                                credit_val = abs(parsed_amt)
                            else:
                                debit_val = abs(parsed_amt)
                        else:
                            # Check narration keywords
                            if any(k in cleaned_desc.lower() for k in ["salary", "deposit", "credit", "cr", "refund", "interest"]):
                                credit_val = abs(parsed_amt)
                            else:
                                debit_val = abs(parsed_amt)

                bal_val = BaseExtractor.clean_amount(get_cell(bal_idx)) if bal_idx >= 0 else 0.0
                txn_type = "CREDIT" if credit_val > 0 and debit_val == 0 else "DEBIT"

                current_txn = Transaction(
                    date=std_date,
                    raw_date=raw_date,
                    description=cleaned_desc,
                    debit=debit_val,
                    credit=credit_val,
                    balance=bal_val,
                    type=txn_type,
                    chq_ref_no=ref_val if ref_val else None,
                )
            else:
                # Continuation row of multi-line narration
                if current_txn:
                    extra_desc = get_cell(desc_idx)
                    if not extra_desc:
                        for idx, cell in enumerate(row):
                            c_text = str(cell or "").strip()
                            if c_text and not re.search(r"^\d+[\.,]\d+$", c_text):
                                extra_desc = c_text
                                break
                    if extra_desc and not any(k in extra_desc.lower() for k in ["page ", "total", "carried forward", "brought forward"]):
                        current_txn.description += " " + extra_desc

        if current_txn and (current_txn.debit > 0 or current_txn.credit > 0 or current_txn.balance > 0):
            transactions.append(current_txn)

        return transactions

    @classmethod
    def parse_rows_positional_fallback(cls, table: List[List[Any]], fallback_year: Optional[int] = None) -> List[Transaction]:
        """
        Positional fallback parser when table headers are completely missing.
        Identifies rows beginning with a date and extracts monetary numbers.
        """
        transactions: List[Transaction] = []
        current_txn: Optional[Transaction] = None

        for row in table:
            if not row:
                continue
            row_items = [str(c or "").strip() for c in row if str(c or "").strip()]
            if not row_items:
                continue

            first_col = row_items[0]
            std_date, raw_date = BaseExtractor.parse_date(first_col, fallback_year=fallback_year)

            if std_date and re.search(r"\d", std_date):
                if current_txn:
                    transactions.append(current_txn)

                amounts: List[float] = []
                non_amount_parts: List[str] = []

                for item in row_items[1:]:
                    cleaned_item = item.replace(",", "").replace("₹", "").replace("$", "").strip()
                    if re.match(r"^-?\d+(\.\d{1,2})?$", cleaned_item):
                        try:
                            amounts.append(float(cleaned_item))
                        except ValueError:
                            non_amount_parts.append(item)
                    else:
                        non_amount_parts.append(item)

                desc = " ".join(non_amount_parts)
                debit, credit, balance = 0.0, 0.0, 0.0

                if len(amounts) >= 3:
                    debit = amounts[-3]
                    credit = amounts[-2]
                    balance = amounts[-1]
                elif len(amounts) == 2:
                    amt = amounts[0]
                    balance = amounts[1]
                    if "cr" in desc.lower():
                        credit = amt
                    else:
                        debit = amt
                elif len(amounts) == 1:
                    balance = amounts[0]

                txn_type = "CREDIT" if credit > 0 and debit == 0 else "DEBIT"
                current_txn = Transaction(
                    date=std_date,
                    raw_date=raw_date,
                    description=desc,
                    debit=debit,
                    credit=credit,
                    balance=balance,
                    type=txn_type
                )
            elif current_txn:
                continuation_text = " ".join(row_items)
                if not any(k in continuation_text.lower() for k in ["page", "statement summary", "carried over"]):
                    current_txn.description += " " + continuation_text

        if current_txn:
            transactions.append(current_txn)

        return transactions

    @classmethod
    def _parse_section_based_text(cls, lines: List[str], fallback_yr: Optional[int] = None) -> List[Transaction]:
        """
        Parses section-divided statements (e.g., Deposits & Credits, Withdrawals, Checks Paid).
        Dynamically attributes amounts to Debit or Credit based on the surrounding section scope.
        """
        transactions: List[Transaction] = []
        current_section: Optional[str] = None
        pending_narration: List[str] = []

        AMOUNT_RE = re.compile(r"(?:[\$₹€£]\s*)?([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]{2}|[0-9]+\.[0-9]{2})\b")
        DATE_RE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}[/-]\d{1,2})\b")

        for line in lines:
            clean_line = line.strip()
            if not clean_line:
                continue
            low_line = clean_line.lower()

            amounts_m = list(AMOUNT_RE.finditer(clean_line))
            dates_m = list(DATE_RE.finditer(clean_line))

            # Detect Section Headers:
            if not amounts_m or "account#" in low_line or "account #" in low_line:
                if re.search(r"\b(account\s*summary|statement\s*summary|balance\s*summary|daily\s*balance)\b", low_line) or "accountsummary" in low_line:
                    current_section = "SUMMARY"
                    pending_narration = []
                    continue
                elif (re.search(r"deposits?\s*(?:&|and)?\s*other\s*credits?|deposits?\s*account|credits?", low_line)
                      or (current_section != "CREDIT" and re.search(r"\b(deposits?|credits?)\b", low_line))):
                    current_section = "CREDIT"
                    pending_narration = []
                    continue
                elif (re.search(r"atm\s*withdrawals?\s*&|withdrawals?\s*(?:&|and)?\s*(?:other\s*)?debits?|electronic\s*(?:withdrawals|debits)", low_line)
                      or (current_section != "DEBIT" and re.search(r"\b(withdrawals?|debits?)\b", low_line))):
                    current_section = "DEBIT"
                    pending_narration = []
                    continue
                elif re.search(r"checks?\s*paid|cheques?\s*paid|checks?\s*presented", low_line):
                    current_section = "CHECKS"
                    pending_narration = []
                    continue

            # If inside summary block, ignore non-transaction rows
            if current_section == "SUMMARY":
                continue

            # Skip section totals
            if low_line.startswith("total") or re.search(r"\btotal\b", low_line):
                pending_narration = []
                continue

            # Skip column headers
            if any(h in low_line for h in ["date credited", "tran date", "date paid", "checknumber", "check number", "reference number"]) and not amounts_m:
                continue

            # 1. CHECKS Section: Date Paid | Check Number | Amount | Reference Number
            if current_section == "CHECKS":
                if dates_m and amounts_m:
                    d_tok = dates_m[0].group(0)
                    std_d, raw_d = BaseExtractor.parse_date(d_tok, fallback_year=fallback_yr)
                    amt_val = float(amounts_m[-1].group(1).replace(",", ""))

                    # Extract check number and reference number from remaining tokens
                    rem = clean_line[:dates_m[0].start()] + " " + clean_line[dates_m[0].end():]
                    for am in amounts_m:
                        rem = rem.replace(am.group(0), "")
                    rem = re.sub(r"[\$₹€£]", "", rem)
                    tokens = [t.strip() for t in rem.split() if t.strip()]

                    chq_no = None
                    ref_no = None
                    for tok in tokens:
                        if re.match(r"^\d{3,6}$", tok) and not chq_no:
                            chq_no = tok
                        elif re.match(r"^\d{7,}$", tok) and not ref_no:
                            ref_no = tok

                    if not chq_no and tokens:
                        chq_no = tokens[0]
                    if not ref_no and len(tokens) > 1:
                        ref_no = tokens[-1]

                    desc = f"Check #{chq_no}" if chq_no else "Check"
                    if ref_no:
                        desc += f" Ref: {ref_no}"

                    transactions.append(Transaction(
                        date=std_d,
                        raw_date=raw_d,
                        description=desc,
                        debit=amt_val,
                        credit=0.0,
                        balance=0.0,
                        type="DEBIT",
                        chq_ref_no=chq_no
                    ))
                continue

            # 2. CREDIT or DEBIT Section
            if current_section in ("CREDIT", "DEBIT"):
                if dates_m and amounts_m:
                    std_d, raw_d = BaseExtractor.parse_date(dates_m[0].group(0), fallback_year=fallback_yr)
                    amt_val = float(amounts_m[-1].group(1).replace(",", ""))

                    # Remove dates and amounts to form clean description
                    desc_clean = clean_line
                    for dm in dates_m:
                        desc_clean = desc_clean.replace(dm.group(0), "")
                    for am in amounts_m:
                        desc_clean = desc_clean.replace(am.group(0), "")
                    desc_clean = re.sub(r"[\$₹€£]", "", desc_clean)
                    desc_clean = " ".join(desc_clean.split()).strip()

                    full_desc = " ".join(pending_narration + ([desc_clean] if desc_clean else [])).strip()
                    pending_narration = []

                    # Detect reference number
                    ref_m = re.search(r"(?:ref\s*(?:nbr|no\.?)?|chq\s*(?:no\.?)?)\s*[:\-]?\s*([A-Za-z0-9]+)", full_desc, re.I)
                    ref_val = ref_m.group(1) if ref_m else None

                    dr = amt_val if current_section == "DEBIT" else 0.0
                    cr = amt_val if current_section == "CREDIT" else 0.0
                    ttype = current_section

                    transactions.append(Transaction(
                        date=std_d,
                        raw_date=raw_d,
                        description=full_desc,
                        debit=dr,
                        credit=cr,
                        balance=0.0,
                        type=ttype,
                        chq_ref_no=ref_val
                    ))
                else:
                    if clean_line and not any(h in low_line for h in ["description", "amount", "date"]):
                        pending_narration.append(clean_line)
                continue

        return transactions

    @classmethod
    def _parse_standard_text(cls, lines: List[str], fallback_yr: Optional[int] = None) -> List[Transaction]:
        """
        Parses standard single-ledger text lines: <Date> <Narration> <Ref?> <Debit?> <Credit?> <Balance>
        """
        transactions: List[Transaction] = []
        current_txn: Optional[Transaction] = None

        date_pattern = re.compile(
            r"^(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}-[A-Za-z]{3}-\d{2,4}|\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4}|\d{4}-\d{2}-\d{2})\b"
        )
        amount_pattern = re.compile(r"(\d{1,3}(?:,\d{2,3})*(?:\.\d{2})|\d+(?:\.\d{2}))")

        for line in lines:
            if any(skip in line.lower() for skip in ["page no", "statement of account", "generated on", "opening balance", "closing balance"]):
                continue

            date_match = date_pattern.match(line)
            if date_match:
                if current_txn:
                    transactions.append(current_txn)

                date_str = date_match.group(1)
                std_date, raw_date = BaseExtractor.parse_date(date_str, fallback_year=fallback_yr)

                remainder = line[date_match.end():].strip()
                amounts_found = amount_pattern.findall(remainder)

                debit, credit, balance = 0.0, 0.0, 0.0
                desc = remainder

                if len(amounts_found) >= 3:
                    debit = BaseExtractor.clean_amount(amounts_found[-3])
                    credit = BaseExtractor.clean_amount(amounts_found[-2])
                    balance = BaseExtractor.clean_amount(amounts_found[-1])
                    for amt_str in amounts_found[-3:]:
                        desc = desc.replace(amt_str, "").strip()
                elif len(amounts_found) == 2:
                    amt1 = BaseExtractor.clean_amount(amounts_found[-2])
                    balance = BaseExtractor.clean_amount(amounts_found[-1])

                    lower_rem = remainder.lower()
                    is_deposit = any(k in lower_rem for k in ["salary", "payroll", "deposit", "credit", "cr", "int.pd", "dividend"])

                    if current_txn and current_txn.balance > 0:
                        if balance > current_txn.balance + 0.01:
                            credit = amt1
                        elif balance < current_txn.balance - 0.01:
                            debit = amt1
                        elif is_deposit:
                            credit = amt1
                        else:
                            debit = amt1
                    elif is_deposit:
                        credit = amt1
                    else:
                        debit = amt1

                    for amt_str in amounts_found[-2:]:
                        desc = desc.replace(amt_str, "").strip()
                elif len(amounts_found) == 1:
                    balance = BaseExtractor.clean_amount(amounts_found[-1])
                    desc = desc.replace(amounts_found[-1], "").strip()

                desc = re.sub(r"\s+", " ", desc).strip()
                txn_type = "CREDIT" if credit > 0 and debit == 0 else "DEBIT"

                current_txn = Transaction(
                    date=std_date,
                    raw_date=raw_date,
                    description=desc,
                    debit=debit,
                    credit=credit,
                    balance=balance,
                    type=txn_type
                )
            elif current_txn:
                if not any(stop in line.lower() for stop in ["page", "statement", "closing", "total"]):
                    current_txn.description += " " + line

        if current_txn:
            transactions.append(current_txn)

        return transactions

    @classmethod
    def parse_raw_text_lines(cls, text: str) -> List[Transaction]:
        """
        Parses transactions dynamically from raw text lines.
        Intelligently detects section-based versus single-ledger layouts.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return []

        fallback_yr = BaseExtractor.extract_statement_year(text)

        # Detect if document uses section-divided architecture
        has_sections = bool(
            re.search(r"deposits?\s*(?:&|and)?\s*other\s*credits?|deposits?\s*account#?", text, re.I)
            or re.search(r"atm\s*withdrawals?|withdrawals?\s*(?:&|and)?\s*(?:other\s*)?debits?|checks?\s*paid", text, re.I)
        )

        if has_sections:
            txns = cls._parse_section_based_text(lines, fallback_yr=fallback_yr)
            if txns:
                return txns

        # Fallback to standard line parser
        return cls._parse_standard_text(lines, fallback_yr=fallback_yr)

    @classmethod
    def parse_all_tables(cls, all_tables: List[List[List[Any]]]) -> List[Transaction]:
        """
        Universal entry point: stitches and parses tables across all statement pages
        dynamically into a clean, reconciled list of transactions.
        """
        all_transactions: List[Transaction] = []
        for table in all_tables:
            txns = cls.parse_table_rows(table)
            all_transactions.extend(txns)
        return all_transactions
