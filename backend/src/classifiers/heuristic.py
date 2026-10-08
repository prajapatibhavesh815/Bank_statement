"""
Heuristic Rule-Based Transaction Classifier.
Uses regex patterns, keyword matching, merchant dictionaries,
and transaction direction (Debit vs Credit) to classify financial transactions without LLMs.
"""
import re
from typing import Dict, Any, Tuple, Optional
from ..models.schemas import Transaction


CATEGORIES = [
    "Salary & Income",
    "Groceries & Supermarkets",
    "Food & Dining",
    "Utilities & Bills",
    "Shopping & E-Commerce",
    "Travel & Fuel",
    "Healthcare & Medical",
    "Entertainment & OTT",
    "Investments & Trading",
    "Loan EMI & Credit Card",
    "Cash & ATM Withdrawal",
    "Bank Charges & Taxes",
    "Transfer (P2P / Self)",
    "Miscellaneous / Others",
]


class HeuristicClassifier:
    """
    Rule-based transaction classification engine.
    """

    # Keyword and regex pattern definitions
    RULES: Dict[str, Dict[str, Any]] = {
        "Salary & Income": {
            "keywords": [
                r"\bsalary\b", r"\bpayroll\b", r"\bsal\s+cr\b", r"\bach\s+cr\b",
                r"\binterest\s+p(?:ai)?d\b", r"\bint\.pd\b", r"\bdividend\b",
                r"\bbonus\b", r"\breimbursement\b", r"\bstipend\b",
            ],
            "direction": "CREDIT",
        },
        "Groceries & Supermarkets": {
            "keywords": [
                r"\bblinkit\b", r"\bzepto\b", r"\bbigbasket\b", r"\bdmart\b",
                r"\breliance\s*(?:fresh|smart|retail)\b", r"\bspencer(?:s)?\b",
                r"\bnature'?s\s*basket\b", r"\bgrocery\b", r"\bsupermarket\b",
                r"\bvegetable\b", r"\bfruit\b", r"\bmilk\b", r"\bdairy\b",
                r"\bmore\s*retail\b", r"\binstamart\b",
            ],
            "direction": "DEBIT",
        },
        "Food & Dining": {
            "keywords": [
                r"\bzomato\b", r"\bswiggy\b", r"\bmcdonald\b", r"\bdomino\b",
                r"\bpizza\b", r"\bburger\b", r"\bkfc\b", r"\bsubway\b",
                r"\bstarbucks\b", r"\bcafe\b", r"\brestaurant\b", r"\bbakery\b",
                r"\bdhaba\b", r"\bchaayos\b", r"\bchai\s*point\b", r"\beatery\b",
                r"\bkitchen\b", r"\bbarbeque\b", r"\bhotel\b", r"\bfood\b",
            ],
            "direction": "DEBIT",
        },
        "Utilities & Bills": {
            "keywords": [
                r"\bbescom\b", r"\bmseb\b", r"\btneb\b", r"\belectricity\b",
                r"\bpower\s*corp\b", r"\bwater\s*board\b", r"\bwssb\b",
                r"\bgas\s*bill\b", r"\bindane\b", r"\bhp\s*gas\b", r"\bbharat\s*gas\b",
                r"\badani\s*gas\b", r"\bmahanagar\s*gas\b", r"\bairtel\b",
                r"\bjio\b", r"\bvodafone\b", r"\bvi\s*bill\b", r"\bbroadband\b",
                r"\bact\s*fiber\b", r"\btata\s*play\b", r"\bdish\s*tv\b",
                r"\bbilldesk\b", r"\bbill\s*pay\b", r"\brecharge\b",
            ],
            "direction": "DEBIT",
        },
        "Shopping & E-Commerce": {
            "keywords": [
                r"\bamazon\b", r"\bflipkart\b", r"\bmyntra\b", r"\bajio\b",
                r"\bmeesho\b", r"\bnykaa\b", r"\btata\s*cliq\b", r"\bebay\b",
                r"\bzara\b", r"\bh&m\b", r"\blifestyle\b", r"\bwestside\b",
                r"\bshoppers\s*stop\b", r"\buniliver\b", r"\bdecathlon\b",
                r"\bretail\b", r"\becom\b", r"\bfashion\b", r"\bmall\b",
            ],
            "direction": "DEBIT",
        },
        "Travel & Fuel": {
            "keywords": [
                r"\buber\b", r"\bola\b", r"\brapido\b", r"\birctc\b",
                r"\bmakemytrip\b", r"\bgoibibo\b", r"\byatra\b", r"\bcleartrip\b",
                r"\bindigo\b", r"\bair\s*india\b", r"\bspicejet\b", r"\bakasa\b",
                r"\bpetrol\b", r"\bdiesel\b", r"\bfuel\b", r"\bhpcl\b",
                r"\biocl\b", r"\bbpcl\b", r"\bshell\b", r"\btoll\b",
                r"\bfastag\b", r"\bauto\s*fare\b", r"\bmetro\b",
            ],
            "direction": "DEBIT",
        },
        "Healthcare & Medical": {
            "keywords": [
                r"\bapollo\b", r"\bpharmeasy\b", r"\b1mg\b", r"\bnetmeds\b",
                r"\bhospital\b", r"\bclinic\b", r"\bpharmacy\b", r"\bchemist\b",
                r"\bmedical\b", r"\bdoctor\b", r"\bhealthcare\b", r"\blab\b",
                r"\bpathology\b", r"\bmedplus\b", r"\bdental\b",
            ],
            "direction": "DEBIT",
        },
        "Entertainment & OTT": {
            "keywords": [
                r"\bnetflix\b", r"\bspotify\b", r"\bprime\s*video\b",
                r"\bhotstar\b", r"\bdisney\b", r"\bbookmyshow\b", r"\bpvr\b",
                r"\binox\b", r"\bcinema\b", r"\btheatre\b", r"\byoutube\s*prem\b",
                r"\bapple\.com/bill\b", r"\bgoogle\s*play\b", r"\bgaming\b",
                r"\bplaystation\b", r"\bsteam\b",
            ],
            "direction": "DEBIT",
        },
        "Investments & Trading": {
            "keywords": [
                r"\bzerodha\b", r"\bgroww\b", r"\bupstox\b", r"\bangel\s*one\b",
                r"\bmutual\s*fund\b", r"\bsip\b", r"\bnse\b", r"\bbse\b",
                r"\bcamsonline\b", r"\bkfintech\b", r"\bindmoney\b",
                r"\bppf\b", r"\bnps\b", r"\bcoin\b", r"\bsecurities\b",
            ],
            "direction": "ANY",
        },
        "Loan EMI & Credit Card": {
            "keywords": [
                r"\bcred\b", r"\bcredit\s*card\b", r"\bcc\s*pay(?:ment)?\b",
                r"\bemi\b", r"\bloan\b", r"\bbajaj\s*finance\b", r"\bhdfc\s*card\b",
                r"\bsbi\s*card\b", r"\bicici\s*card\b", r"\baxis\s*card\b",
                r"\bhome\s*loan\b", r"\bcar\s*loan\b", r"\bauto\s*loan\b",
                r"\bpersonal\s*loan\b", r"\bfinance\b",
            ],
            "direction": "DEBIT",
        },
        "Cash & ATM Withdrawal": {
            "keywords": [
                r"\batm\s*w(?:d)?l\b", r"\bcash\s*w(?:d)?l\b", r"\bnfs\s*w(?:d)?l\b",
                r"\bcash\s*deposit\b", r"\bcwdr\b", r"\bself\s*wdl\b",
                r"\bbranch\s*cash\b", r"\batm\b",
            ],
            "direction": "ANY",
        },
        "Bank Charges & Taxes": {
            "keywords": [
                r"\bchg\b", r"\bcharges\b", r"\bgst\b", r"\bannual\s*fee\b",
                r"\bsms\s*ch(?:g|arge)\b", r"\bmin\s*bal\b", r"\bpenalty\b",
                r"\bdebit\s*card\s*fee\b", r"\bconsolidated\s*chg\b",
                r"\binterest\s*debit\b", r"\btds\b",
            ],
            "direction": "DEBIT",
        },
        "Transfer (P2P / Self)": {
            "keywords": [
                r"\bupi\b", r"\bneft\b", r"\bimps\b", r"\brtgs\b",
                r"\btransfer\b", r"\btrf\b", r"\bfund\s*transfer\b",
                r"\bto\s+[a-z\s]+\b", r"\bfrom\s+[a-z\s]+\b",
            ],
            "direction": "ANY",
        },
    }

    # Merchant entity recognizer
    MERCHANT_PATTERNS = [
        (r"\b(ZOMATO|SWIGGY|BLINKIT|ZEPTO|BIGBASKET|DMART|AMAZON|FLIPKART|MYNTRA|AJIO|MEESHO|NYKAA|UBER|OLA|RAPIDO|IRCTC|MAKEMYTRIP|INDIGO|AIR INDIA|NETFLIX|SPOTIFY|BOOKMYSHOW|PVR|INOX|ZERODHA|GROWW|CRED|APOLLO|PHARMEASY|1MG|BESCOM|AIRTEL|JIO)\b", 1),
        (r"UPI/(?:[A-Z0-9]+/)?([A-Za-z0-9\s_\.\-]+?)/(?:UPI|Payment|Ref|DR|CR)", 1),
        (r"(?:TO|FROM|PAY TO)\s+([A-Za-z0-9\s]{3,25})", 1),
    ]

    # Payment channel detector
    CHANNEL_PATTERNS = [
        (r"\bUPI\b", "UPI"),
        (r"\bNEFT\b", "NEFT"),
        (r"\bIMPS\b", "IMPS"),
        (r"\bRTGS\b", "RTGS"),
        (r"\b(?:ATM|NFS|CWDR)\b", "ATM Cash"),
        (r"\b(?:POS|EDC|DEBIT CARD)\b", "POS / Card"),
        (r"\b(?:ACH|NACH|ECS)\b", "ACH / Mandate"),
        (r"\b(?:CHQ|CHEQUE|INWARD CLG|OUTWARD CLG)\b", "Cheque"),
        (r"\b(?:INT\.PD|INTEREST)\b", "Interest"),
    ]

    @classmethod
    def detect_channel(cls, description: str) -> str:
        """Extracts transaction channel (UPI, NEFT, IMPS, POS, ATM, etc.)."""
        for pat, channel in cls.CHANNEL_PATTERNS:
            if re.search(pat, description, re.IGNORECASE):
                return channel
        return "Internal / NetBanking"

    @classmethod
    def extract_merchant(cls, description: str) -> Optional[str]:
        """Extracts merchant or payee name if present."""
        for pat, group_idx in cls.MERCHANT_PATTERNS:
            m = re.search(pat, description, re.IGNORECASE)
            if m:
                merchant = m.group(group_idx).strip()
                # Clean up punctuation
                merchant = re.sub(r"[/\\_-]", " ", merchant).strip()
                if len(merchant) > 2 and not merchant.isdigit():
                    return merchant.title()
        return None

    @classmethod
    def classify(cls, transaction: Transaction) -> Tuple[str, Optional[str], float]:
        """
        Classifies a transaction using rule-based heuristics.
        Returns (category, sub_category, confidence_score).
        """
        desc = (transaction.description or "").lower()
        is_credit = transaction.credit > 0 or transaction.type == "CREDIT"
        is_debit = transaction.debit > 0 or transaction.type == "DEBIT"

        # Specific high-priority brand and universal semantic tokens (resilient to OCR word concatenation)
        BRAND_SUBSTRINGS = {
            "Food & Dining": ["zomato", "swiggy", "mcdonald", "domino", "starbuck", "subway", "kfc", "restaurant", "cafe", "bakery", "dhaba", "food", "dine", "kitchen", "meals", "pizza", "burger", "coffee", "eatery", "bistro", "pub", "barbeque"],
            "Groceries & Supermarkets": ["blinkit", "zepto", "bigbasket", "dmart", "reliancefresh", "spencer", "supermarket", "grocery", "provision", "mart", "store", "dairy", "milk", "vegetable", "fruit", "instamart", "hypermarket", "bakery", "bazaar", "kirana"],
            "Shopping & E-Commerce": ["amazon", "flipkart", "myntra", "ajio", "meesho", "nykaa", "tatacliq", "zara", "decathlon", "ecommerce", "e-com", "retail", "apparel", "clothing", "shopping", "mall", "fashion", "footwear", "boutique", "electronics"],
            "Travel & Fuel": ["uber", "ola", "rapido", "irctc", "makemytrip", "indigo", "airindia", "petrol", "fuel", "hpcl", "iocl", "bpcl", "fastag", "toll", "airline", "flight", "railway", "transit", "train", "metro", "bus", "cab", "taxi", "gas station", "parking", "shell petrol"],
            "Utilities & Bills": ["bescom", "mseb", "tneb", "electricity", "billdesk", "airtel", "jio", "vodafone", "broadband", "gasbill", "billpay", "utility", "water board", "power corp", "recharge", "telecom", "dth", "broadband", "postpaid", "dish tv"],
            "Entertainment & OTT": ["netflix", "spotify", "primevideo", "hotstar", "bookmyshow", "pvr", "inox", "youtube", "cinema", "movie", "entertainment", "theatre", "streaming", "music", "gaming", "amusement"],
            "Investments & Trading": ["zerodha", "groww", "upstox", "angelone", "mutualfund", "sip", "camsonline", "securities", "trading", "investment", "equities", "stock", "broker", "depository", "amc", "bse", "nse", "crypto"],
            "Healthcare & Medical": ["apollo", "pharmeasy", "1mg", "netmeds", "hospital", "clinic", "pharmacy", "chemist", "doctor", "medical", "healthcare", "diagnostic", "lab", "dental", "meds", "druggist", "opticals"],
            "Loan EMI & Credit Card": ["cred club", "creditcard", "emi", "bajajfinance", "homeloan", "carloan", "loan", "mortgage", "installment", "finance", "card payment", "credit card", "personal loan", "housing loan", "auto loan"],
            "Cash & ATM Withdrawal": ["atm", "cashwdl", "cwdr", "cdm", "cash wdl", "cash withdrawal", "nfs*cash", "atm wdl", "self cash", "branch cash"],
            "Salary & Income": ["salary", "payroll", "int.pd", "dividend", "bonus", "stipend", "wage", "direct deposit", "pension", "honorarium", "interest paid", "interest cr", "consulting fee", "freelance"],
            "Bank Charges & Taxes": ["charges", "annualfee", "smschg", "penalty", "bank fee", "service charge", "gst", "min bal", "maintenance fee", "ledger fee", "processing fee", "forex markup"],
        }

        # Substring token match check (prioritized before generic transfer)
        for cat, tokens in BRAND_SUBSTRINGS.items():
            # Direction sanity
            if cat == "Salary & Income" and not is_credit:
                continue
            if cat in ["Loan EMI & Credit Card", "Bank Charges & Taxes", "Utilities & Bills"] and is_credit:
                continue

            for tok in tokens:
                if tok in desc:
                    return cat, None, 0.95

        # Check standard rules
        for category, config in cls.RULES.items():
            if category == "Transfer (P2P / Self)":
                continue  # Evaluate transfer at the end

            req_dir = config["direction"]
            if req_dir == "CREDIT" and not is_credit:
                continue
            if req_dir == "DEBIT" and not is_debit:
                continue

            for pattern in config["keywords"]:
                if re.search(pattern, desc):
                    return category, None, 0.95

        # Fallback for generic UPI or Transfers
        if "upi" in desc or "imps" in desc or "neft" in desc or "transfer" in desc:
            return "Transfer (P2P / Self)", None, 0.75

        # Fallback for credit transactions if not matched
        if is_credit:
            return "Salary & Income", "Other Deposit", 0.60

        return "Miscellaneous / Others", None, 0.50
