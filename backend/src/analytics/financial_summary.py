"""
Financial Analytics and Summary Engine.
Computes cash flow metrics, category breakdowns, monthly trends,
top merchants, and ledger balance reconciliation health.
"""
from typing import List, Dict, Any
import pandas as pd
from ..models.schemas import Transaction, AccountDetails


class FinancialSummary:
    """
    Computes analytics and aggregations on classified bank transactions.
    """

    @classmethod
    def analyze(cls, transactions: List[Transaction], account_details: AccountDetails) -> Dict[str, Any]:
        """
        Generates full analytical report for the statement.
        """
        if not transactions:
            return {
                "total_debits": 0.0,
                "total_credits": 0.0,
                "net_cash_flow": 0.0,
                "transaction_count": 0,
                "category_summary": [],
                "channel_summary": [],
                "top_merchants": [],
                "monthly_trend": [],
                "balance_health": {"verified": 0, "total": 0, "percentage": 100.0},
            }

        df = pd.DataFrame([t.to_dict() for t in transactions])

        total_debits = float(df["debit"].sum())
        total_credits = float(df["credit"].sum())
        net_cash_flow = total_credits - total_debits

        # 1. Category breakdown (for Debits / Expenses)
        debit_df = df[df["debit"] > 0]
        cat_summary = []
        if not debit_df.empty:
            cat_grouped = debit_df.groupby("category")["debit"].agg(["sum", "count"]).reset_index()
            cat_grouped["percentage"] = (cat_grouped["sum"] / (total_debits or 1.0)) * 100.0
            cat_grouped = cat_grouped.sort_values(by="sum", ascending=False)
            for _, row in cat_grouped.iterrows():
                cat_summary.append({
                    "category": row["category"],
                    "total_amount": round(float(row["sum"]), 2),
                    "count": int(row["count"]),
                    "percentage": round(float(row["percentage"]), 1),
                })

        # 2. Payment Channel breakdown
        channel_grouped = df.groupby("channel")["debit"].agg(["sum", "count"]).reset_index()
        channel_grouped = channel_grouped.sort_values(by="sum", ascending=False)
        channel_summary = []
        for _, row in channel_grouped.iterrows():
            channel_summary.append({
                "channel": row["channel"] or "Other",
                "total_amount": round(float(row["sum"]), 2),
                "count": int(row["count"]),
            })

        # 3. Top Merchants (where merchant is identified)
        merchant_df = debit_df[debit_df["merchant"].notna() & (debit_df["merchant"] != "")]
        top_merchants = []
        if not merchant_df.empty:
            top_m = merchant_df.groupby("merchant")["debit"].agg(["sum", "count"]).reset_index()
            top_m = top_m.sort_values(by="sum", ascending=False).head(8)
            for _, row in top_m.iterrows():
                top_merchants.append({
                    "merchant": row["merchant"],
                    "total_amount": round(float(row["sum"]), 2),
                    "count": int(row["count"]),
                })

        # 4. Monthly Cashflow Trend
        df["month_year"] = df["date"].apply(lambda d: str(d)[:7] if d else "Unknown")
        monthly_grouped = df.groupby("month_year").agg({
            "debit": "sum",
            "credit": "sum",
        }).reset_index().sort_values(by="month_year")

        monthly_trend = []
        for _, row in monthly_grouped.iterrows():
            monthly_trend.append({
                "month": row["month_year"],
                "total_debit": round(float(row["debit"]), 2),
                "total_credit": round(float(row["credit"]), 2),
                "net": round(float(row["credit"]) - float(row["debit"]), 2),
            })

        # 5. Balance verification health
        verified_count = df["balance_verified"].fillna(True).sum()
        total_count = len(df)
        pct = (verified_count / total_count * 100.0) if total_count > 0 else 100.0

        return {
            "total_debits": round(total_debits, 2),
            "total_credits": round(total_credits, 2),
            "net_cash_flow": round(net_cash_flow, 2),
            "transaction_count": len(transactions),
            "avg_debit": round(float(debit_df["debit"].mean()), 2) if not debit_df.empty else 0.0,
            "category_summary": cat_summary,
            "channel_summary": channel_summary,
            "top_merchants": top_merchants,
            "monthly_trend": monthly_trend,
            "balance_health": {
                "verified": int(verified_count),
                "total": int(total_count),
                "percentage": round(pct, 1),
            },
        }
