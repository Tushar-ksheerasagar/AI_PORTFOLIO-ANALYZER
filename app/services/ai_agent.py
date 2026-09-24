import logging
from typing import List, Dict, Any

try:
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    from langchain_core.output_parsers import StrOutputParser
    from langchain_mistralai import ChatMistralAI
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    ChatMistralAI = None
    SystemMessage = HumanMessage = AIMessage = None
    StrOutputParser = None

from app.core.config import settings


logger = logging.getLogger(__name__)


def _offline_chat_fallback(
    message: str,
    metrics: Dict[str, Any],
    holdings_str: str,
    sector_str: str
) -> str:
    """
    Intelligent offline fallback engine for GrowwPro AI Advisor.
    Generates dynamic, metrics-aware responses if the API call is offline, rate-limited, or unavailable.
    """
    msg_lower = message.lower().strip()
    
    summary = metrics.get("summary", {}) if isinstance(metrics, dict) else {}
    risk = metrics.get("risk_metrics", {}) if isinstance(metrics, dict) else {}
    val = summary.get("total_current_value", 0.0)
    basis = summary.get("total_cost_basis", 0.0)
    abs_ret = summary.get("absolute_return", 0.0)
    pct_ret = summary.get("percentage_return", 0.0)
    vol = risk.get("volatility", 0.0) * 100
    sharpe = risk.get("sharpe_ratio", 0.0)
    beta = risk.get("beta", 0.0)
    max_dd = risk.get("max_drawdown", 0.0) * 100
    
    # 1. Greetings & Introductions
    if any(w in msg_lower for w in ["hi", "hello", "hey", "good morning", "good evening", "greetings", "thanks", "thank you"]):
        if val > 0:
            return (
                f"Hello! I am your GrowwPro AI Advisor. Your active portfolio is currently valued at **₹{val:,.2f}** "
                f"with an overall return of **{pct_ret:+.2f}%** (₹{abs_ret:,.2f}). How can I assist you with your investments today?\n\n"
                "*Disclaimer: Informational analysis only; not financial advice.*"
            )
        else:
            return (
                "Hello! I am your GrowwPro AI Advisor. Your active portfolio currently has no holdings. "
                "Add stock holdings using the '+ Add Stock' button to analyze real-time performance, risk ratios, and sector allocations!\n\n"
                "*Disclaimer: Informational analysis only; not financial advice.*"
            )

    # 2. Buy/Sell/Hold Stock Recommendation Guardrail
    if any(w in msg_lower for w in ["should i buy", "should i sell", "buy or sell", "which stock to buy", "recommend stock", "target price"]):
        return (
            "As an AI, I cannot provide direct buy, sell, or hold recommendations for individual stocks. "
            "However, I can help you evaluate your portfolio's overall diversification, volatility, and historical risk ratios. "
            "Please consult a registered investment advisor for stock advice.\n\n"
            "*Disclaimer: Educational guardrail enforced.*"
        )

    # 3. Return & Performance Queries
    if any(w in msg_lower for w in ["return", "profit", "loss", "gain", "performance", "doing", "value"]):
        if val > 0:
            status = "profit" if abs_ret >= 0 else "loss"
            return (
                f"Your active portfolio total value is **₹{val:,.2f}** against a cost basis of **₹{basis:,.2f}**, "
                f"yielding an overall {status} of **₹{abs_ret:,.2f} ({pct_ret:+.2f}%)**.\n\n"
                "*Disclaimer: Past performance is not indicative of future returns.*"
            )
        else:
            return (
                "Your active portfolio has no holdings yet (Total Value: ₹0.00). "
                "Add holdings to track performance and net returns.\n\n"
                "*Disclaimer: Informational context.*"
            )

    # 4. Risk, Volatility & Sharpe Ratio Queries
    if any(w in msg_lower for w in ["risk", "volatility", "sharpe", "beta", "drawdown", "safe"]):
        return (
            f"Here are your portfolio's key risk metrics: Volatility is **{vol:.1f}%**, Sharpe Ratio is **{sharpe:.2f}**, "
            f"Beta is **{beta:.2f}**, and Maximum Drawdown is **{max_dd:.1f}%**. "
            f"A Sharpe ratio above 1.0 indicates good risk-adjusted returns relative to volatility.\n\n"
            "*Disclaimer: Historical risk metrics are for evaluation only.*"
        )

    # 5. Sector & Holding Allocation Queries
    if any(w in msg_lower for w in ["sector", "holding", "allocation", "weight", "diversif"]):
        return (
            f"Sector Breakdown: **{sector_str}**.\n"
            f"Holdings Summary: **{holdings_str}**.\n"
            f"To maintain good diversification, monitor your top sector weightings and risk ratios.\n\n"
            "*Disclaimer: Educational analysis only.*"
        )

    # 6. Off-Topic Guardrail
    if any(w in msg_lower for w in ["recipe", "cook", "python", "weather", "movie", "game", "joke", "history"]):
        return (
            "I am your GrowwPro AI Advisor. I can only assist you with portfolio-related questions, asset allocations, "
            "risk metrics, and stock market analysis. Please ask a finance-related question.\n\n"
            "*Disclaimer: Educational guardrail enforced.*"
        )

    # 7. General Financial Analysis Fallback
    if val > 0:
        return (
            f"GrowwPro Analysis: Your portfolio value is **₹{val:,.2f}** ({pct_ret:+.2f}% return). "
            f"Sectors: {sector_str}. Risk: Volatility={vol:.1f}%, Sharpe={sharpe:.2f}. "
            "Feel free to ask about your risk ratios, returns, or sector allocations!\n\n"
            "*Disclaimer: Informational analysis only.*"
        )
    else:
        return (
            "GrowwPro AI Advisor is ready to assist you! "
            "Please add stock holdings to your portfolio to view detailed performance metrics, risk ratios, and sector insights.\n\n"
            "*Disclaimer: Informational analysis only.*"
        )


def run_chat_agent(
    message: str,
    history: List[Dict[str, str]],
    metrics: Dict[str, Any],
    holdings_str: str,
    sector_str: str
) -> str:
    """
    Executes a token-efficient LangChain financial advisor agent with inline guardrails and fallback.
    """
    api_key = settings.MISTRAL_API_KEY
    if not api_key or "your_mistral_api_key" in api_key.lower():
        logger.info("Using GrowwPro offline fallback agent (API key unconfigured).")
        return _offline_chat_fallback(message, metrics, holdings_str, sector_str)
        
    try:
        if not HAS_LANGCHAIN or ChatMistralAI is None:
            logger.warning("LangChain Mistral integration is unavailable; using offline fallback agent.")
            return _offline_chat_fallback(message, metrics, holdings_str, sector_str)

        # Limit completion output length to cap output token costs
        llm = ChatMistralAI(
            api_key=api_key,
            model=settings.MISTRAL_MODEL,
            temperature=0.2,
            max_tokens=150
        )
        
        # Inline guardrails and context instructions
        system_instruction = (
            "You are GrowwPro AI Advisor, a professional financial analyst.\n"
            "Real-time Portfolio Context:\n"
            f"- Value: ₹{metrics['summary']['total_current_value']:,.2f} (Basis: ₹{metrics['summary']['total_cost_basis']:,.2f}), Gain/Loss: ₹{metrics['summary']['absolute_return']:,.2f} ({metrics['summary']['percentage_return']:.2f}%)\n"
            f"- Risk: Volatility={metrics['risk_metrics']['volatility']*100:.1f}%, Sharpe={metrics['risk_metrics']['sharpe_ratio']:.2f}, Beta={metrics['risk_metrics']['beta']:.2f}, MaxDD={metrics['risk_metrics']['max_drawdown']*100:.1f}%\n"
            f"- Sectors: {sector_str}\n"
            f"- Holdings: {holdings_str}\n\n"
            "Safety Guardrails & Interaction Rules:\n"
            "1. Conversational greetings (e.g., 'hi', 'hello', 'hey', 'good morning', 'thanks') and general financial inquiries are WELCOME. Respond warmly and offer assistance regarding their portfolio.\n"
            "2. If the user query asks for direct stock recommendations or whether to buy/sell/hold a specific stock ticker, reply exactly: "
            "'As an AI, I cannot provide direct buy, sell, or hold recommendations for individual stocks. However, I can help you evaluate your portfolio's overall diversification, volatility, and historical risk ratios. Please consult a registered investment advisor for stock advice.'\n"
            "3. If the user query is completely off-topic (unrelated to finance, stock market, asset allocation, or standard greetings/thanks), reply exactly: "
            "'I am your GrowwPro AI Advisor. I can only assist you with portfolio-related questions, asset allocations, risk metrics, and stock market analysis. Please ask a finance-related question.'\n"
            "4. Otherwise, answer helpfully and concisely using the portfolio context. Limit each answer to 2-3 sentences. Always end with a short disclaimer sentence."
        )
        
        # Truncate message history to last 4 messages (2 exchanges) to save input tokens
        history_window = history[-4:] if isinstance(history, list) else []
        
        # Build direct BaseMessage objects to avoid prompt template variable parsing bugs (e.g. KeyError with curly braces)
        messages = [SystemMessage(content=system_instruction)]
        for msg in history_window:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not content or not isinstance(content, str):
                continue
            if role == "assistant":
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))
            
        messages.append(HumanMessage(content=message))
        
        chain = llm | StrOutputParser()
        response = chain.invoke(messages)
        
        return response
        
    except Exception as e:
        logger.error(f"Error inside LangChain Chat Agent: {str(e)}. Switching to intelligent fallback.", exc_info=True)
        return _offline_chat_fallback(message, metrics, holdings_str, sector_str)

from app.schemas.insight import RebalanceResponse, RecommendationItem
from mistralai.client import Mistral

def recommend_stock_replacements(
    weakest_ticker: str,
    weakest_sector: str,
    weakest_return: float,
    weakest_buy_price: float
) -> RebalanceResponse:
    """
    Queries Mistral AI to recommend strong replacement stocks from the same sector 
    for an underperforming holding. Falls back to pre-defined quality picks if offline.
    """
    api_key = settings.MISTRAL_API_KEY
    
    # 1. Define high-quality offline fallbacks per sector
    sector_fallbacks = {
        "Technology": [
            RecommendationItem(
                ticker="TCS.NS",
                name="Tata Consultancy Services",
                rationale="Industry leader in IT services with robust cash flows, a strong deal pipeline, and consistent dividend payouts.",
                risk="Subject to global macroeconomic slowdowns impacting enterprise IT spending."
            ),
            RecommendationItem(
                ticker="INFY.NS",
                name="Infosys Limited",
                rationale="Highly competitive operating margins, strong digital cloud capabilities, and solid revenue guidance.",
                risk="Higher attrition rates and exposure to geopolitical currency fluctuations."
            )
        ],
        "Financial Services": [
            RecommendationItem(
                ticker="ICICIBANK.NS",
                name="ICICI Bank Limited",
                rationale="Exceptional net interest margins, strong retail asset growth, and superior asset quality compared to peers.",
                risk="Regulatory shifts in interest rate cycles affecting credit growth."
            ),
            RecommendationItem(
                ticker="HDFCBANK.NS",
                name="HDFC Bank Limited",
                rationale="Largest private sector bank in India with robust cross-selling, post-merger scale advantages, and high capital adequacy.",
                risk="Integration digestion of the merger may compress margins in the short term."
            )
        ],
        "Energy": [
            RecommendationItem(
                ticker="RELIANCE.NS",
                name="Reliance Industries Limited",
                rationale="Conglomerate strength with retail and telecom divisions balancing the traditional oil-to-chemicals segment, plus green energy upside.",
                risk="Capital-intensive expansion projects could delay debt reduction targets."
            ),
            RecommendationItem(
                ticker="TATAPOWER.NS",
                name="Tata Power Company",
                rationale="Aggressive expansion in green energy transmission, EV charging grids, and utility-scale solar projects.",
                risk="High leverage and regulatory price caps on power purchase agreements."
            )
        ]
    }
    
    # Standard default fallback for miscellaneous sectors
    default_fallback = [
        RecommendationItem(
            ticker="ITC.NS",
            name="ITC Limited",
            rationale="Defensive consumer staple giant with massive market share, strong FMCG margin expansion, and a high dividend yield.",
            risk="Subject to regulatory tobacco tax hikes."
        ),
        RecommendationItem(
            ticker="LT.NS",
            name="Larsen & Toubro Limited",
            rationale="Leading infrastructure giant with a record order book, benefit from government capex push, and global execution capabilities.",
            risk="Execution delays on large-scale engineering contracts due to commodity pricing."
        )
    ]
    
    # 2. Check if API key is unset or placeholders are used
    if not api_key or "your_mistral_api_key" in api_key.lower():
        logger.warning("Mistral API key is not configured. Using offline rebalancer fallback.")
        picks = sector_fallbacks.get(weakest_sector, default_fallback)
        return RebalanceResponse(
            weak_stock=weakest_ticker,
            reason_weak=f"This stock is underperforming with an absolute return of {weakest_return:.1f}% on your buy price of ₹{weakest_buy_price:,.2f}.",
            recommendations=picks
        )
        
    try:
        client = Mistral(api_key=api_key)
        
        system_instruction = (
            "You are GrowwPro Smart Rebalancer, an advanced portfolio optimizer advisor.\n"
            "Identify strong alternative stock tickers (from NSE/BSE) belonging to the SAME sector as the underperforming stock to serve as replacement candidates.\n"
            "Respond strictly in structured JSON format matching the schema rules.\n"
            "Frame recommendations educationally. Never promise returns."
        )
        
        user_prompt = (
            f"The underperforming stock in the user's portfolio is {weakest_ticker} in the {weakest_sector} sector. "
            f"It has generated a return of {weakest_return:.1f}% on a buy price of ₹{weakest_buy_price:,.2f}.\n"
            f"Recommend 2 strong alternatives in the {weakest_sector} sector."
        )
        
        response = client.chat.parse(
            model=settings.MISTRAL_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            response_format=RebalanceResponse
        )
        
        parsed = response.choices[0].message.parsed
        if parsed:
            return parsed
        else:
            raise ValueError("Mistral returned an empty rebalance response")
            
    except Exception as e:
        logger.error(f"Error calling Mistral AI API for rebalancing: {str(e)}. Using fallback rebalancer.", exc_info=True)
        picks = sector_fallbacks.get(weakest_sector, default_fallback)
        return RebalanceResponse(
            weak_stock=weakest_ticker,
            reason_weak=f"This stock is underperforming with an absolute return of {weakest_return:.1f}% on your buy price of ₹{weakest_buy_price:,.2f}.",
            recommendations=picks
        )
