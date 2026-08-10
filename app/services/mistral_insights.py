import os
import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
from mistralai.client import Mistral
from app.core.config import settings
from app.schemas.insight import AIInsightContent

logger = logging.getLogger(__name__)

def generate_portfolio_hash(holdings: List[Dict[str, Any]]) -> str:
    """
    Generates a unique MD5 hash based on the current list of holdings
    to check if cached AI insights need to be updated.
    """
    # Sort holdings to ensure the hash is deterministic
    sorted_holdings = sorted(
        holdings,
        key=lambda x: (x["ticker"], x["quantity"], x["buy_price"], str(x["buy_date"]))
    )
    serialized = json.dumps(sorted_holdings, default=str)
    return hashlib.md5(serialized.encode("utf-8")).hexdigest()

def generate_fallback_insight(metrics: Dict[str, Any]) -> AIInsightContent:
    """
    Generates structured commentary locally when the Mistral API is unavailable.
    """
    total_val = metrics["summary"]["total_current_value"]
    cost_basis = metrics["summary"]["total_cost_basis"]
    abs_return = metrics["summary"]["absolute_return"]
    pct_return = metrics["summary"]["percentage_return"]
    
    summary = (
        f"Your portfolio currently has a total value of ₹{total_val:,.2f} "
        f"on a cost basis of ₹{cost_basis:,.2f}. "
        f"This represents an absolute return of ₹{abs_return:,.2f} "
        f"({pct_return:.2f}%)."
    )
    
    vol = metrics["risk_metrics"]["volatility"] * 100
    sharpe = metrics["risk_metrics"]["sharpe_ratio"]
    beta = metrics["risk_metrics"]["beta"]
    max_dd = metrics["risk_metrics"]["max_drawdown"] * 100
    
    risk_commentary = (
        f"The portfolio's annualized volatility stands at {vol:.2f}%, with a maximum drawdown of {max_dd:.2f}%. "
        f"A Sharpe ratio of {sharpe:.2f} indicates a "
        f"{'strong' if sharpe > 1 else 'moderate' if sharpe > 0 else 'weak'} risk-adjusted performance. "
        f"With a beta of {beta:.2f} against the benchmark, your portfolio is "
        f"{'more volatile than' if beta > 1 else 'less volatile than' if beta < 1 else 'equally volatile to'} Nifty 50."
    )
    
    stock_hhi = metrics["summary"]["stock_hhi"]
    sector_hhi = metrics["summary"]["sector_hhi"]
    
    if stock_hhi > 0.25:
        div_note = "Your portfolio exhibits high stock concentration, making it sensitive to individual stock movements."
    elif stock_hhi > 0.15:
        div_note = "Your portfolio shows moderate stock concentration. Review if your top holdings align with your target allocations."
    else:
        div_note = "Your portfolio is well-diversified across individual holdings, reducing single-stock risks."
        
    if sector_hhi > 0.25:
        div_note += " There is also significant sector concentration. Economic events affecting your primary sector could heavily impact your returns."
    elif sector_hhi > 0.15:
        div_note += " Sector concentration is moderate."
    else:
        div_note += " Your assets are distributed across multiple sectors, providing robust sector-level diversification."
        
    # Pick a watch item based on concentration and risk
    watch_items = [
        "Monitor the volatility of your top holdings to ensure your risk exposure is appropriate.",
        "Assess if sector allocations are consistent with long-term macroeconomic outlooks.",
        "Consider rebalancing if any single asset weight exceeds 30% of total portfolio value."
    ]
    
    if beta > 1.3:
        watch_items.append("Your high beta suggests vulnerability in market downturns; consider adding defensive holdings.")
    if max_dd > 0.2:
        watch_items.append("The maximum drawdown is high. Evaluate if your asset selection is matches your risk tolerance.")
        
    return AIInsightContent(
        summary=summary,
        risk_commentary=risk_commentary,
        diversification_note=div_note,
        watch_items=watch_items[:3],
        disclaimer="Disclaimer: This is an automatically generated analytical commentary for educational and informational purposes only. It does not constitute investment, financial, or tax advice."
    )

def generate_ai_insights(metrics: Dict[str, Any]) -> AIInsightContent:
    """
    Calls the Mistral AI API using Structured Outputs (.parse) to generate
    professional, context-aware portfolio commentary. Falls back gracefully on error.
    """
    api_key = settings.MISTRAL_API_KEY
    # Check if API key is unset or placeholders are used
    if not api_key or "your_mistral_api_key" in api_key.lower():
        logger.warning("Mistral API key is not configured or using default placeholder. Using fallback engine.")
        return generate_fallback_insight(metrics)
        
    try:
        client = Mistral(api_key=api_key)
        
        # Compact representation of sector allocations and holdings for token efficiency
        sector_str = ", ".join([f"{k}: {v*100:.1f}%" for k, v in metrics["sector_allocations"].items()])
        holdings_str = "; ".join([
            f"{h['ticker']} ({h['sector']}): wt={h['weight']*100:.1f}%, return={h['percentage_return']:.1f}%"
            for h in metrics["holdings"]
        ])
        
        system_instruction = (
            "You are a professional financial analyst. Analyze portfolio statistics and generate "
            "plain-English, structured commentary.\n"
            "Guidelines for text fields (summary, risk_commentary, diversification_note):\n"
            "- Be token-efficient: limit each field strictly to 2-3 concise, punchy sentences.\n"
            "- Interpret what the numbers mean for the investor rather than repeating raw metrics.\n"
            "- Ensure high readability: use active verbs, short sentences, and avoid jargon.\n"
            "- Frame everything as educational, never as direct investment advice."
        )
        
        user_prompt = (
            f"Analyze this portfolio:\n"
            f"Value: ₹{metrics['summary']['total_current_value']:,.2f} (Basis: ₹{metrics['summary']['total_cost_basis']:,.2f}), "
            f"Returns: ₹{metrics['summary']['absolute_return']:,.2f} ({metrics['summary']['percentage_return']:.2f}%)\n"
            f"Concentration HHI: Stock={metrics['summary']['stock_hhi']:.3f}, Sector={metrics['summary']['sector_hhi']:.3f}\n"
            f"Risk: Vol={metrics['risk_metrics']['volatility']*100:.1f}%, Sharpe={metrics['risk_metrics']['sharpe_ratio']:.2f}, "
            f"Beta={metrics['risk_metrics']['beta']:.2f}, MaxDD={metrics['risk_metrics']['max_drawdown']*100:.1f}%\n"
            f"Sectors: {sector_str}\n"
            f"Holdings: {holdings_str}"
        )
        
        response = client.chat.parse(
            model=settings.MISTRAL_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            response_format=AIInsightContent
        )
        
        parsed = response.choices[0].message.parsed
        if parsed:
            return parsed
        else:
            raise ValueError("Mistral returned an empty parsed response")
            
    except Exception as e:
        logger.error(f"Error calling Mistral AI API: {str(e)}. Using fallback engine.", exc_info=True)
        return generate_fallback_insight(metrics)
