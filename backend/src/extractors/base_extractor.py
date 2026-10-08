"""
Base extractor class with regex helpers, date parsing, amount cleaning,
and balance reconciliation logic.
"""
import re
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from ..models.schemas import AccountDetails, Transaction, StatementProcessingResult, ExtractionMetadata


class BaseExtractor:
    """
    Common base class providing parsing utilities across text and OCR extractors.
    """

    # Common Indian & International date formats
    DATE_PATTERNS = [
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",
        r"\b\d{1,2}-\d{1,2}-\d{4}\b",
        r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",
        r"\b\d{1,2}/\d{1,2}/\d{2}\b",
        r"\b\d{1,2}-\d{1,2}-\d{2}\b",
        r"\b\d{1,2}\.\d{1,2}\.\d{2}\b",
        r"\b\d{1,2}-[A-Za-z]{3,9}-\d{4}\b",
        r"\b\d{1,2}-[A-Za-z]{3,9}-\d{2}\b",
        r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b",
        r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2}\b",
        r"\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\b",
        r"\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{4}/\d{2}/\d{2}\b",
    ]

    DATE_FORMATS = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d.%m.%y",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%m.%d.%Y",
        "%m/%d/%y",
        "%m-%d-%y",
        "%m.%d.%y",
        "%d-%b-%Y",
        "%d-%b-%y",
        "%d %b %Y",
        "%d %b %y",
        "%d-%B-%Y",
        "%d %B %Y",
        "%d %B %y",
        "%b %d, %Y",
        "%b %d %Y",
        "%B %d, %Y",
        "%B %d %Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
    ]

    @classmethod
    def clean_amount(cls, val_str: Any) -> float:
        """
        Cleans currency string into a float.
        Handles commas, currency symbols (₹, $, €, £, Rs.), accounting parentheses (100.00),
        trailing Cr/Dr/-, and European numbering formats (1.234,56).
        """
        if val_str is None:
            return 0.0
        if isinstance(val_str, (int, float)):
            return float(val_str)

        text = str(val_str).strip()
        if not text or text in ["-", "--", "NA", "N/A", "Nil", "nil", "0"]:
            return 0.0

        # Check for accounting negative in parentheses: (500.00) or ($500.00)
        is_parenthesis_neg = bool(re.search(r"^\s*\(.*?\)\s*$", text))

        # Remove currency symbols and non-essential whitespace
        text = re.sub(r"[₹$€£\s]", "", text)

        # Check for European number format: 1.234,56 or 12.345,67
        if re.search(r"^\d{1,3}(?:\.\d{3})+,\d{2}$", text) or re.search(r"^\d+,\d{2}$", text):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")

        # Check for trailing or leading negative, or Dr marker
        is_negative = (
            is_parenthesis_neg
            or "-" in text
            or text.endswith("Dr")
            or text.endswith("DR")
            or text.endswith("-")
        )
        text = re.sub(r"[^\d.]", "", text)

        try:
            val = float(text)
            return -val if is_negative else val
        except ValueError:
            return 0.0

    @classmethod
    def extract_statement_year(cls, text: str) -> Optional[int]:
        """
        Dynamically extracts the primary calendar year from statement context
        (e.g., statement dates, period dates, header timestamps).
        """
        if not text:
            return None

        date_patterns = [
            r"(?:Statement\s*Date|Date\s*of\s*Statement|Statement\s*as\s*of)\s*[:\-]?\s*(?:[A-Za-z]+\s*\d{1,2},?\s*(\d{4})|\d{1,2}[/-]\d{1,2}[/-](\d{4}))",
            r"(?:Ending\s*Balance|Beginning\s*Balance)\s*on\s*[A-Za-z]+\s*\d{1,2},?\s*(\d{4})",
            r"(?:Statement\s*Period|Period\s*From|Period)(?:.*?)\b(19\d\d|20\d\d)\b",
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*\d{1,2},?\s*(19\d\d|20\d\d)\b",
            r"\b\d{1,2}[/-]\d{1,2}[/-](19\d\d|20\d\d)\b",
        ]
        for p in date_patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                for g in m.groups():
                    if g and 1990 <= int(g) <= 2040:
                        return int(g)

        header_text = text[:2000]
        years = [int(y) for y in re.findall(r"\b(19\d\d|20\d\d)\b", header_text) if 1990 <= int(y) <= 2040]
        if years:
            from collections import Counter
            return Counter(years).most_common(1)[0][0]

        return None

    @classmethod
    def parse_date(cls, date_str: str, fallback_year: Optional[int] = None) -> Tuple[str, str]:
        """
        Attempts to parse a raw date string into standard ISO format (YYYY-MM-DD).
        Supports standard 3-part dates as well as 2-part dates (MM-DD, DD-MM, MM/DD, DD/MM, Mon DD).
        Returns (standardized_date, raw_date) if valid date, otherwise ("", "").
        """
        if not date_str:
            return "", ""

        cleaned = str(date_str).strip()
        # 1. Direct 3-part format checks
        for fmt in cls.DATE_FORMATS:
            try:
                dt = datetime.strptime(cleaned, fmt)
                if dt.year < 1970:
                    dt = dt.replace(year=dt.year + 100)
                # Sanity check year range
                if 1990 <= dt.year <= 2040:
                    return dt.strftime("%Y-%m-%d"), cleaned
            except ValueError:
                continue

        # 2. Regex search for 3-part date within substring
        for pattern in cls.DATE_PATTERNS:
            match = re.search(pattern, cleaned)
            if match:
                matched_str = match.group(0)
                for fmt in cls.DATE_FORMATS:
                    try:
                        dt = datetime.strptime(matched_str, fmt)
                        if dt.year < 1970:
                            dt = dt.replace(year=dt.year + 100)
                        if 1990 <= dt.year <= 2040:
                            return dt.strftime("%Y-%m-%d"), matched_str
                    except ValueError:
                        continue

        # 3. 2-part date formats (MM-DD, DD-MM, MM/DD, DD/MM, Mon DD, DD Mon)
        yr = fallback_year if (fallback_year and 1990 <= fallback_year <= 2040) else datetime.now().year

        # Month name + Day: "May 15", "May5", "Jun 05"
        m_alpha = re.search(r"\b([A-Za-z]{3,9})\s*(\d{1,2})\b", cleaned)
        if m_alpha:
            try:
                dt = datetime.strptime(f"{m_alpha.group(1)[:3]} {m_alpha.group(2)} {yr}", "%b %d %Y")
                return dt.strftime("%Y-%m-%d"), m_alpha.group(0)
            except ValueError:
                pass

        # Day + Month name: "15 May", "5 June"
        m_alpha_rev = re.search(r"\b(\d{1,2})\s*([A-Za-z]{3,9})\b", cleaned)
        if m_alpha_rev:
            try:
                dt = datetime.strptime(f"{m_alpha_rev.group(1)} {m_alpha_rev.group(2)[:3]} {yr}", "%d %b %Y")
                return dt.strftime("%Y-%m-%d"), m_alpha_rev.group(0)
            except ValueError:
                pass

        # Numeric 2-part: "05-15", "5/12", "15-05", "15.05"
        m_num = re.search(r"\b(\d{1,2})[/\.-](\d{1,2})\b", cleaned)
        if m_num:
            n1 = int(m_num.group(1))
            n2 = int(m_num.group(2))
            if 1 <= n1 <= 12 and 1 <= n2 <= 31:
                month, day = n1, n2
            elif 1 <= n2 <= 12 and 1 <= n1 <= 31:
                month, day = n2, n1
            else:
                return "", ""
            try:
                dt = datetime(yr, month, day)
                return dt.strftime("%Y-%m-%d"), m_num.group(0)
            except ValueError:
                pass

        return "", ""

    @classmethod
    def extract_account_metadata(cls, text: str, detected_bank: str = "Generic Bank") -> AccountDetails:
        """
        Extracts account holder, account number, IFSC, branch, and statement period
        using robust multi-pattern regular expressions and layout heuristics.
        """
        details = AccountDetails(bank_name=detected_bank)
        year_ctx = cls.extract_statement_year(text)

        # 1. Account Number (Supports local, international, IBAN, and masked formats)
        acc_patterns = [
            r"(?:(?:Primary|Secondary|Customer|Savings|Current)\s+)?(?:Account\s*(?:Number|No\.?)|AccountNo|A/c\s*(?:No\.?|Number)|Account\s*#|Account\s*ID|AcCount#)\s*[:\-]?\s*([X\*\d\-]{8,34})",
            r"(?:Savings\s*A/c\s*(?:No\.?|Number)?|Current\s*A/c\s*(?:No\.?|Number)?)\s*[:\-]?\s*([X\*\d\-]{8,34})",
            r"\bIBAN\s*[:\-]?\s*([A-Z]{2}\d{2}[A-Z0-9]{11,30})\b",
            r"\bAccount\s*Number\s*[:\-]?\s*(\d{8,20})\b",
            r"\b(?:A/c|Account)\s*[:\-]?\s*(\d{9,18})\b",
            r"\b(\d{11,18})\b",
        ]
        for p in acc_patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                cand_acc = m.group(1).strip()
                if not any(cand_acc.lower() == noise for noise in ["statement", "number"]):
                    details.account_number = cand_acc
                    break

        # 2. IFSC Code or SWIFT/BIC
        ifsc_m = re.search(r"\b([A-Z]{4}0[A-Z0-9]{6})\b", text)
        if ifsc_m:
            details.ifsc_code = ifsc_m.group(1)
        else:
            swift_m = re.search(r"\b([A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)\b", text)
            if swift_m:
                details.ifsc_code = swift_m.group(1)

        # 3. Account Holder Name
        name_patterns = [
            r"(?:Customer\s*Name|Account\s*Holder\s*(?:Name)?|Account\s*Name|Customer|Client\s*Name)\s*[:\-]\s*([A-Za-z\.\s]{2,40}?)(?=\s+(?:Account|A/c|Address|IFSC|Statement|Branch|Period|Date)|\n|$|\r)",
            r"\b(?:M/s\.?|Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Shri|Smt)\s+([A-Za-z\s\.]{3,35})(?=\s+(?:Account|A/c|Address)|\n|$|\r)",
            r"(?:Name)\s*[:\-]\s*([A-Za-z\.\s]{3,35})(?=\s+(?:Account|A/c|Address)|\n|$|\r)",
        ]
        for p in name_patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                cand = m.group(1).strip()
                if not any(stop in cand.lower() for stop in ["bank", "statement", "account", "address", "branch", "period", "limited", "date", "number"]):
                    details.account_holder = cand
                    break

        # Fallback for Account Holder: Preceding street address line heuristic
        if details.account_holder == "Not Found":
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            street_pat = re.compile(
                r"^\s*\d+[\s\w,\.-]*(?:Dr\.?|Drive|St\.?|Street|Ave\.?|Avenue|Rd\.?|Road|Blvd\.?|Boulevard|Lane|Ln\.?|Way|Court|Ct\.?|Circle|Nagar|Marg|Sector|Colony)\b",
                re.IGNORECASE
            )
            for i in range(1, len(lines)):
                if street_pat.search(lines[i]):
                    prev = lines[i - 1].strip()
                    if (
                        2 <= len(prev) <= 45
                        and not any(noise in prev.lower() for noise in [
                            "bank", "statement", "member", "fdic", "box", "p.o.", "branch", "page",
                            "account", "summary", "balance", "total", "phone", "call", "date", "dr."
                        ])
                        and not re.search(r"\d", prev)
                    ):
                        details.account_holder = prev
                        break

        # 4. Branch
        branch_m = re.search(r"(?:Branch\s*[:\-]|Branch\s*Name\s*[:\-])\s*([A-Za-z0-9\s,\-]{3,45})(?:\n|$)", text, re.IGNORECASE)
        if branch_m:
            details.branch = branch_m.group(1).strip()

        # 5. Statement Period
        period_patterns = [
            r"(?:Statement\s*Period|Period\s*From|Period)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}-[A-Za-z]{3}-\d{2,4})\s*(?:to|-|until)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}-[A-Za-z]{3}-\d{2,4})",
            r"(?:From|Between)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:To|and)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ]
        for p in period_patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                start_iso, _ = cls.parse_date(m.group(1), fallback_year=year_ctx)
                end_iso, _ = cls.parse_date(m.group(2), fallback_year=year_ctx)
                details.statement_period_start = start_iso or m.group(1)
                details.statement_period_end = end_iso or m.group(2)
                break

        # Date of statement / Beginning / Ending balance date period fallback
        if not details.statement_period_start or not details.statement_period_end:
            beg_date_m = re.search(r"Beginning\s*Balance\s*on\s*([A-Za-z]+\s*\d{1,2},?\s*\d{4})", text, re.IGNORECASE)
            end_date_m = re.search(r"Ending\s*Balance\s*on\s*([A-Za-z]+\s*\d{1,2},?\s*\d{4})", text, re.IGNORECASE)
            if beg_date_m and end_date_m:
                s_iso, _ = cls.parse_date(beg_date_m.group(1), fallback_year=year_ctx)
                e_iso, _ = cls.parse_date(end_date_m.group(1), fallback_year=year_ctx)
                if s_iso:
                    details.statement_period_start = s_iso
                if e_iso:
                    details.statement_period_end = e_iso
            elif end_date_m:
                e_iso, _ = cls.parse_date(end_date_m.group(1), fallback_year=year_ctx)
                if e_iso:
                    details.statement_period_end = e_iso

        # 6. Opening & Closing Balances (if explicitly stated in header/summary)
        open_bal_m = re.search(
            r"(?:Opening\s*Balance|Beginning\s*Balance|Balance\s*B/F|Brought\s*Forward)(?:[^\d\n\r]*on\s*[A-Za-z0-9\s,]+)?\s*[:\-]?\s*(?:INR|Rs\.?|₹|\$)?\s*([+\-]?[\d,]+\.\d{2}|[+\-]?\d+)",
            text, re.IGNORECASE
        )
        if open_bal_m:
            details.opening_balance = cls.clean_amount(open_bal_m.group(1))

        close_bal_m = re.search(
            r"(?:Closing\s*Balance|Ending\s*Balance|Balance\s*C/F|Carried\s*Forward)(?:[^\d\n\r]*on\s*[A-Za-z0-9\s,]+)?\s*[:\-]?\s*(?:INR|Rs\.?|₹|\$)?\s*([+\-]?[\d,]+\.\d{2}|[+\-]?\d+)",
            text, re.IGNORECASE
        )
        if close_bal_m:
            details.closing_balance = cls.clean_amount(close_bal_m.group(1))

        return details

    @classmethod
    def verify_running_balances(cls, transactions: List[Transaction]) -> Tuple[List[Transaction], List[str]]:
        """
        Performs mathematical audit of the transaction ledger:
        Verifies if: Balance[i] == Balance[i-1] + Credit[i] - Debit[i]
        Handles both ascending and descending statement orders.
        """
        if not transactions or len(transactions) < 2:
            if transactions:
                transactions[0].balance_verified = True
            return transactions, []

        anomalies = []
        
        # Test forward chronological order (row 0 to N-1)
        # Normal check: curr_bal ≈ prev_bal - debit + credit
        match_count_forward = 0
        for i in range(1, len(transactions)):
            prev_bal = transactions[i - 1].balance
            curr_bal = transactions[i].balance
            expected = prev_bal - transactions[i].debit + transactions[i].credit
            if abs(expected - curr_bal) < 0.05:
                match_count_forward += 1

        # Test reverse chronological order (statement starts with newest, ends with oldest)
        # Reverse check: prev_row_bal (newer) ≈ curr_row_bal (older) - curr_debit + curr_credit
        # which means: curr_bal (older) ≈ prev_bal (newer) + curr_debit - curr_credit
        match_count_reverse = 0
        for i in range(1, len(transactions)):
            newer_bal = transactions[i - 1].balance
            older_bal = transactions[i].balance
            expected_reverse = newer_bal + transactions[i - 1].debit - transactions[i - 1].credit
            if abs(expected_reverse - older_bal) < 0.05:
                match_count_reverse += 1

        is_reverse_order = match_count_reverse > match_count_forward

        for i in range(len(transactions)):
            if i == 0:
                transactions[i].balance_verified = True
                continue

            if not is_reverse_order:
                prev_bal = transactions[i - 1].balance
                curr_bal = transactions[i].balance
                expected = prev_bal - transactions[i].debit + transactions[i].credit
                if abs(expected - curr_bal) < 0.05:
                    transactions[i].balance_verified = True
                else:
                    transactions[i].balance_verified = False
                    msg = (f"Row {i+1} ({transactions[i].date}): Balance mismatch! "
                           f"Expected {expected:.2f} (from prev {prev_bal:.2f} - Dr {transactions[i].debit:.2f} + Cr {transactions[i].credit:.2f}), "
                           f"Found {curr_bal:.2f} (diff: {abs(expected - curr_bal):.2f})")
                    anomalies.append(msg)
            else:
                newer_bal = transactions[i - 1].balance
                older_bal = transactions[i].balance
                expected = newer_bal + transactions[i - 1].debit - transactions[i - 1].credit
                if abs(expected - older_bal) < 0.05:
                    transactions[i].balance_verified = True
                else:
                    transactions[i].balance_verified = False
                    msg = (f"Row {i+1} ({transactions[i].date}): Reverse ledger mismatch! "
                           f"Expected {expected:.2f}, Found {older_bal:.2f}")
                    anomalies.append(msg)

        return transactions, anomalies
