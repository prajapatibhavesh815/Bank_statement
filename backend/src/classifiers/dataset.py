"""
Training dataset generator and loader for Traditional Machine Learning models.
Includes thousands of realistic Indian & international banking transaction descriptions
across all 14 categories.
"""
import random
from typing import List, Tuple
import pandas as pd


# Core training corpus templates
SEED_DATA = [
    # Salary & Income
    ("Salary & Income", "NEFT CR-CITI0000001-INFOSYS LIMITED-SALARY FOR AUG 2024"),
    ("Salary & Income", "ACH CR TATA CONSULTANCY SERVICES LTD SALARY"),
    ("Salary & Income", "SALARY CREDIT - WIPRO TECH MONTHLY PAYROLL"),
    ("Salary & Income", "NEFT CR-ACCENTURE SERVICES PVT LTD-SALARY"),
    ("Salary & Income", "BY CLG SALARY CREDIT - COGNIZANT TECH"),
    ("Salary & Income", "ACH CR PAYROLL SERVICES PVT LTD"),
    ("Salary & Income", "MONTHLY STIPEND GOOGLE INDIA PVT LTD"),
    ("Salary & Income", "ANNUAL PERFORMANCE BONUS CR HCL TECH"),
    ("Salary & Income", "INT.PD:01-07-2024 TO 30-09-2024 SAVINGS INTEREST CREDIT"),
    ("Salary & Income", "INTEREST PAID FOR Q2 2024-25"),
    ("Salary & Income", "DIVIDEND CREDIT - RELIANCE INDUSTRIES LTD"),
    ("Salary & Income", "DIVIDEND PAID - INFOSYS LTD ACH CR"),
    ("Salary & Income", "EXPENSE REIMBURSEMENT TECH MAHINDRA"),

    # Groceries & Supermarkets
    ("Groceries & Supermarkets", "UPI/428192019281/BLINKIT COMMERCE/blinkit@icici/DR"),
    ("Groceries & Supermarkets", "UPI/981726354120/ZEPTO GROCERIES/zepto@hdfc/DR"),
    ("Groceries & Supermarkets", "UPI/120938475610/BIGBASKET/bigbasket@kotak/Payment"),
    ("Groceries & Supermarkets", "POS 482910 DMART AVENUE SUPERMARTS KANDIVALI MUMBAI"),
    ("Groceries & Supermarkets", "POS 819201 RELIANCE FRESH POWAI STORE MUMBAI"),
    ("Groceries & Supermarkets", "POS 281920 SPENCERS RETAIL SOUTH EXTENSION DELHI"),
    ("Groceries & Supermarkets", "POS NATURES BASKET INDIRANAGAR BANGALORE"),
    ("Groceries & Supermarkets", "UPI/392019283746/MORE RETAIL SUPERMARKET/DR"),
    ("Groceries & Supermarkets", "UPI/SWIGGY INSTAMART GROCERIES/swiggy@axis"),
    ("Groceries & Supermarkets", "LOCAL VEGETABLE AND FRUIT MARKET UPI DR"),
    ("Groceries & Supermarkets", "COUNTRY DELIGHT MILK AND DAIRY DELIVERY"),
    ("Groceries & Supermarkets", "AMUL ICE CREAM AND MILK PARLOUR UPI"),

    # Food & Dining
    ("Food & Dining", "UPI/420192837461/ZOMATO LIMITED/zomato@icici/Food order"),
    ("Food & Dining", "UPI/391029384756/SWIGGY/swiggy@hdfc/Lunch payment"),
    ("Food & Dining", "POS 382910 MCDONALDS CONNAUGHT PLACE NEW DELHI"),
    ("Food & Dining", "POS 849201 DOMINOS PIZZA SECTOR 18 NOIDA"),
    ("Food & Dining", "POS 920192 STARBUCKS COFFEE BANDRA WEST MUMBAI"),
    ("Food & Dining", "POS SUBWAY SANDWICHES AIRPORT ROAD PUNE"),
    ("Food & Dining", "POS KFC RESTAURANTS HYDERABAD IN"),
    ("Food & Dining", "POS 829102 THEOBROMA BAKERY COLABA"),
    ("Food & Dining", "POS BARBEQUE NATION HOSPITALITY BANGALORE"),
    ("Food & Dining", "UPI/CHAAYOS CAFE PRIVATE LTD/chaayos@yesbank"),
    ("Food & Dining", "UPI/CHAI POINT CAFE/chaipoint@hdfcbank"),
    ("Food & Dining", "LOCAL RESTAURANT AND DHABA DINNER UPI PAYMENT"),
    ("Food & Dining", "HALDIRAM SWEETS AND RESTAURANT CHANDNI CHOWK"),

    # Utilities & Bills
    ("Utilities & Bills", "BILLDESK BESCOM BANGALORE ELECTRICITY BILL"),
    ("Utilities & Bills", "MAHADISCOM MSEB ELECTRICITY ONLINE BILL PAYMENT"),
    ("Utilities & Bills", "TNEB CHENNAI ELECTRICITY BOARD BILLPAY"),
    ("Utilities & Bills", "DELHI JAL BOARD WATER SUPPLY BILL PAYMENT"),
    ("Utilities & Bills", "BWSSB WATER SUPPLY BILL BANGALORE"),
    ("Utilities & Bills", "INDANE LPG GAS CYLINDER REFILL BOOKING"),
    ("Utilities & Bills", "BHARAT GAS REFILL BOOKING HPCL GAS"),
    ("Utilities & Bills", "ADANI TOTAL GAS LTD PIPED GAS BILL"),
    ("Utilities & Bills", "AIRTEL POSTPAID MOBILE AND DTH RECHARGE"),
    ("Utilities & Bills", "JIO PREPAID MOBILITY RECHARGE 299 PLAN"),
    ("Utilities & Bills", "VODAFONE IDEA VI POSTPAID BILL PAYMENT"),
    ("Utilities & Bills", "ACT FIBERNET HIGH SPEED BROADBAND BILL"),
    ("Utilities & Bills", "TATA PLAY DTH MONTHLY PACK SUBSCRIPTION"),

    # Shopping & E-Commerce
    ("Shopping & E-Commerce", "AMAZON SELLER SERVICES MUMBAI IN WEB"),
    ("Shopping & E-Commerce", "AMAZON PAY INDIA PRIVATE LIMITED UPI/DR"),
    ("Shopping & E-Commerce", "FLIPKART INTERNET PRIVATE LIMITED BANGALORE"),
    ("Shopping & E-Commerce", "MYNTRA DESIGNS PRIVATE LIMITED ONLINE"),
    ("Shopping & E-Commerce", "AJIO ONLINE FASHION SHOPPING RELIANCE RETAIL"),
    ("Shopping & E-Commerce", "MEESHO SUPPLY CHAIN ECOMMERCE BANGALORE"),
    ("Shopping & E-Commerce", "NYKAA E-RETAIL BEAUTY PRODUCTS MUMBAI"),
    ("Shopping & E-Commerce", "TATA CLIQ LUXURY ONLINE PURCHASE"),
    ("Shopping & E-Commerce", "POS ZARA RETAIL INDIA PHOENIX MARKETCITY"),
    ("Shopping & E-Commerce", "POS H&M HENNES & MAURITZ SELECT CITYWALK"),
    ("Shopping & E-Commerce", "POS DECATHLON SPORTS INDIA SARJAPUR"),
    ("Shopping & E-Commerce", "POS SHOPPERS STOP LTD MALAD WEST MUMBAI"),

    # Travel & Fuel
    ("Travel & Fuel", "UPI/UBER INDIA SYSTEMS PVT LTD/uber@axisbank"),
    ("Travel & Fuel", "UPI/OLA CABS/olacabs@icici/Ride payment"),
    ("Travel & Fuel", "UPI/RAPIDO BIKE TAXI/rapido@hdfc"),
    ("Travel & Fuel", "IRCTC E-TICKETING NEW DELHI RAILWAY BOOKING"),
    ("Travel & Fuel", "MAKEMYTRIP INDIA PVT LTD FLIGHT BOOKING"),
    ("Travel & Fuel", "GOIBIBO ONLINE TRAVEL BOOKING GURGAON"),
    ("Travel & Fuel", "INTERGLOBE AVIATION INDIGO AIRLINES FLIGHT"),
    ("Travel & Fuel", "AIR INDIA BOOKING COMMERCIAL AIR TICKETS"),
    ("Travel & Fuel", "POS INDIAN OIL CORPORATION PETROL PUMP IOCL"),
    ("Travel & Fuel", "POS BHARAT PETROLEUM BPCL FUEL STATION"),
    ("Travel & Fuel", "POS HINDUSTAN PETROLEUM HPCL AUTO CARE"),
    ("Travel & Fuel", "POS SHELL PETROL PUMP KORAMANGALA BANGALORE"),
    ("Travel & Fuel", "IHMCL NETC FASTAG RECHARGE TOLL PLAZA"),
    ("Travel & Fuel", "DELHI METRO SMART CARD AUTO RECHARGE DMRC"),

    # Healthcare & Medical
    ("Healthcare & Medical", "POS APOLLO HOSPITALS ENTERPRISE GREAMS ROAD"),
    ("Healthcare & Medical", "POS APOLLO PHARMACY INDIRANAGAR STORE"),
    ("Healthcare & Medical", "UPI/PHARMEASY MEDICINE ORDER/pharmeasy@icici"),
    ("Healthcare & Medical", "UPI/TATA 1MG HEALTHCARE/1mg@hdfc"),
    ("Healthcare & Medical", "UPI/NETMEDS MARKETPLACE/netmeds@axis"),
    ("Healthcare & Medical", "POS FORTIS HEALTHCARE LIMITED DELHI"),
    ("Healthcare & Medical", "POS MANIPAL HOSPITAL AIRPORT ROAD BANGALORE"),
    ("Healthcare & Medical", "DR LAL PATHLABS DIAGNOSTIC BLOOD TEST"),
    ("Healthcare & Medical", "THYROCARE TECHNOLOGIES LAB PROFILE"),
    ("Healthcare & Medical", "MEDPLUS HEALTH SERVICES PHARMACY STORE"),
    ("Healthcare & Medical", "DR CONSULTATION FEES CLINIC UPI DR"),

    # Entertainment & OTT
    ("Entertainment & OTT", "NETFLIX.COM INTERNET ENTERTAINMENT MUMBAI"),
    ("Entertainment & OTT", "SPOTIFY INDIA SERVICES PRIVATE LIMITED"),
    ("Entertainment & OTT", "AMAZON PRIME VIDEO ANNUAL MEMBERSHIP"),
    ("Entertainment & OTT", "DISNEY PLUS HOTSTAR SUBSCRIPTION BILLDESK"),
    ("Entertainment & OTT", "BOOKMYSHOW BIGTREE ENTERTAINMENT MOVIE TICKETS"),
    ("Entertainment & OTT", "POS PVR CINEMAS FORUM MALL BANGALORE"),
    ("Entertainment & OTT", "POS INOX LEISURE NARIMAN POINT MUMBAI"),
    ("Entertainment & OTT", "YOUTUBE PREMIUM MONTHLY RECURRING GOOGLE"),
    ("Entertainment & OTT", "APPLE.COM/BILL RECURRENT SUBSCRIPTION ICLOUD"),
    ("Entertainment & OTT", "PLAYSTATION NETWORK SONY INTERACTIVE"),
    ("Entertainment & OTT", "STEAM GAMES VALVE CORPORATION ONLINE"),

    # Investments & Trading
    ("Investments & Trading", "ACH DR ZERODHA BROKING LIMITED TRADING ACC"),
    ("Investments & Trading", "UPI/GROWW INVEST TECH/groww@icici/Stocks"),
    ("Investments & Trading", "UPI/UPSTOX RKSV SECURITIES/upstox@hdfc"),
    ("Investments & Trading", "ANGEL ONE LIMITED SHARE TRADING MARGIN"),
    ("Investments & Trading", "ACH DR NIPPON INDIA MUTUAL FUND SIP 5000"),
    ("Investments & Trading", "ACH DR HDFC MUTUAL FUND SYSTEMATIC INV"),
    ("Investments & Trading", "ACH DR SBI MUTUAL FUND BLUECHIP EQUITY"),
    ("Investments & Trading", "CAMSONLINE MUTUAL FUND REDEMPTION CR"),
    ("Investments & Trading", "KFIN TECHNOLOGIES MUTUAL FUND INVEST"),
    ("Investments & Trading", "PUBLIC PROVIDENT FUND PPF DEPOSIT TRF"),
    ("Investments & Trading", "NATIONAL PENSION SYSTEM NPS TRUST CONTRIBUTION"),

    # Loan EMI & Credit Card
    ("Loan EMI & Credit Card", "UPI/CRED CLUB BBPS PAYMENT/cred@axisbank"),
    ("Loan EMI & Credit Card", "AUTODEBIT HDFC BANK CREDIT CARD PAYMENT"),
    ("Loan EMI & Credit Card", "ACH DR SBI CARDS AND PAYMENT SERVICES"),
    ("Loan EMI & Credit Card", "AUTODEBIT ICICI BANK CC PAYMENT 5402"),
    ("Loan EMI & Credit Card", "ACH DR BAJAJ FINANCE LTD EMI PAYMENT"),
    ("Loan EMI & Credit Card", "ACH DR HDFC BANK HOME LOAN EMI PRINCIPAL"),
    ("Loan EMI & Credit Card", "ACH DR SBI HOME FINANCE LOAN EMI REPAY"),
    ("Loan EMI & Credit Card", "ACH DR ICICI BANK CAR LOAN EMI DEBIT"),
    ("Loan EMI & Credit Card", "TATA CAPITAL FINANCIAL PERSONAL LOAN EMI"),
    ("Loan EMI & Credit Card", "MUTHOOT FINANCE GOLD LOAN INTEREST REPAY"),

    # Cash & ATM Withdrawal
    ("Cash & ATM Withdrawal", "ATM WDL-NFS-HDFC ATM MG ROAD BLR-2091"),
    ("Cash & ATM Withdrawal", "ATM WDL-NFS-SBI CASH DISPENSER CONNAUGHT PL"),
    ("Cash & ATM Withdrawal", "ATM WDL-CASH WITHDRAWAL ICICI BANK ATM"),
    ("Cash & ATM Withdrawal", "CWDR-ATM CASH DISPENSE TXN REF 409182"),
    ("Cash & ATM Withdrawal", "SELF CASH WITHDRAWAL BY CHEQUE NO 401928"),
    ("Cash & ATM Withdrawal", "BRANCH CASH WITHDRAWAL SAVINGS ACCOUNT"),
    ("Cash & ATM Withdrawal", "CASH DEPOSIT MACHINE CDM BRANCH ENTRY"),

    # Bank Charges & Taxes
    ("Bank Charges & Taxes", "CONSOLIDATED CHARGES FOR QUARTER ENDED"),
    ("Bank Charges & Taxes", "SMS ALERT AND NOTIFICATION CHARGES DEBIT"),
    ("Bank Charges & Taxes", "ANNUAL DEBIT CARD MAINTENANCE CHARGE"),
    ("Bank Charges & Taxes", "MINIMUM BALANCE NON MAINTENANCE CHARGE"),
    ("Bank Charges & Taxes", "GST @ 18% ON BANKING SERVICES FEES"),
    ("Bank Charges & Taxes", "CHEQUE RETURN CHARGES INSUFFICIENT FUNDS"),
    ("Bank Charges & Taxes", "OUTWARD CHEQUE CLEARING RETURN CHG"),
    ("Bank Charges & Taxes", "TDS DEDUCTED ON FIXED DEPOSIT INTEREST"),

    # Transfer (P2P / Self)
    ("Transfer (P2P / Self)", "UPI/402910291029/RAHUL SHARMA/rahul@oksbi/Transfer"),
    ("Transfer (P2P / Self)", "UPI/901928374610/PRIYA PATEL/priya@okaxis/Rent share"),
    ("Transfer (P2P / Self)", "UPI/102938475619/AMIT KUMAR/amit@paytm/P2P"),
    ("Transfer (P2P / Self)", "NEFT CR-HDFC0000123-MANISH GUPTA-FUND TRANSFER"),
    ("Transfer (P2P / Self)", "NEFT DR-SBIN0001234-DEEPAK VERMA-RENT PAYMENT"),
    ("Transfer (P2P / Self)", "IMPS/P2A/401928374/SURESH MENON/HDFC BANK"),
    ("Transfer (P2P / Self)", "RTGS DR-ICIC0000001-KAVITA DESHMUKH-PROPERTY"),
    ("Transfer (P2P / Self)", "TRANSFER TO A/C 501002938491 SELF TRANSFER"),
    ("Transfer (P2P / Self)", "INTERNAL FUNDS TRANSFER BETWEEN LINKED ACCOUNTS"),
]


def generate_augmented_training_data(multiplier: int = 15) -> pd.DataFrame:
    """
    Augments the seed corpus with synthetic variations (random UTRs, dates,
    channel tokens, noise words) to produce a rich training set of 1,500+ samples.
    """
    data: List[Tuple[str, str]] = []
    banks = ["HDFC", "SBI", "ICICI", "AXIS", "KOTAK", "PNB", "BOB"]
    channels = ["UPI", "NEFT", "IMPS", "POS", "ACH"]

    for category, base_text in SEED_DATA:
        # Include the original
        data.append((category, base_text))

        # Generate synthetic permutations
        for _ in range(multiplier):
            rand_ref = str(random.randint(100000000000, 999999999999))
            rand_bank = random.choice(banks)
            prefix = ""
            suffix = ""

            rand_type = random.randint(1, 4)
            if rand_type == 1:
                # Add UPI prefix/suffix
                variant = f"UPI/{rand_ref}/{base_text}/{rand_bank}"
            elif rand_type == 2:
                # Add NEFT / IMPS envelope
                variant = f"NEFT DR-{rand_bank}000{random.randint(100, 999)}-{base_text}-{rand_ref}"
            elif rand_type == 3:
                # Add POS envelope
                variant = f"POS {rand_ref[:6]} {base_text} {rand_bank} IN"
            else:
                variant = f"{base_text} REF#{rand_ref[:8]}"

            data.append((category, variant))

    df = pd.DataFrame(data, columns=["category", "description"])
    return df.sample(frac=1.0, random_state=42).reset_index(drop=True)
