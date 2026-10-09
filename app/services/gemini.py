import json
import logging
from typing import Any, Dict, List, Type, TypeVar

from app.core.config import settings
from app.schemas.insight import AIInsightContent, RebalanceResponse

logger = logging.getLogger(__name__)

T = TypeVar("T")


def is_gemini_configured() -> bool:
    api_key = settings.GEMINI_API_KEY
    return bool(api_key and "your_gemini_api_key" not in api_key.lower())


def _get_client():
    try:
        from google import genai
    except ImportError as error:
        raise RuntimeError(
            "The Gemini SDK is not installed. Install dependencies from requirements.txt."
        ) from error

    return genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_structured(
    system_instruction: str,
    user_prompt: str,
    response_schema: Type[T],
    max_output_tokens: int = 600,
) -> T:
    if not is_gemini_configured():
        raise RuntimeError("Gemini API key is not configured.")

    from google.genai import types

    client = _get_client()
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=0.2,
            max_output_tokens=max_output_tokens,
        ),
    )

    response_text = getattr(response, "text", None)
    if not response_text:
        raise ValueError("Gemini returned an empty response.")

    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise ValueError("Gemini returned invalid JSON.") from error

    return response_schema.model_validate(payload)


def generate_insight(metrics: Dict[str, Any]) -> AIInsightContent:
    sector_str = ", ".join(
        f"{key}: {value * 100:.1f}%"
        for key, value in metrics["sector_allocations"].items()
    )
    holdings_str = "; ".join(
        f"{holding['ticker']} ({holding['sector']}): "
        f"wt={holding['weight'] * 100:.1f}%, "
        f"return={holding['percentage_return']:.1f}%"
        for holding in metrics["holdings"]
    )
    system_instruction = (
        "You are a professional financial analyst. Analyze portfolio statistics and "
        "generate plain-English, structured commentary. Keep summary, risk_commentary, "
        "and diversification_note to 2-3 concise sentences. Interpret the numbers "
        "instead of repeating them. Frame everything as educational, never as direct "
        "investment advice."
    )
    user_prompt = (
        "Analyze this portfolio:\n"
        f"Value: ₹{metrics['summary']['total_current_value']:,.2f} "
        f"(Basis: ₹{metrics['summary']['total_cost_basis']:,.2f}), "
        f"Returns: ₹{metrics['summary']['absolute_return']:,.2f} "
        f"({metrics['summary']['percentage_return']:.2f}%)\n"
        f"Concentration HHI: Stock={metrics['summary']['stock_hhi']:.3f}, "
        f"Sector={metrics['summary']['sector_hhi']:.3f}\n"
        f"Risk: Vol={metrics['risk_metrics']['volatility'] * 100:.1f}%, "
        f"Sharpe={metrics['risk_metrics']['sharpe_ratio']:.2f}, "
        f"Beta={metrics['risk_metrics']['beta']:.2f}, "
        f"MaxDD={metrics['risk_metrics']['max_drawdown'] * 100:.1f}%\n"
        f"Sectors: {sector_str}\n"
        f"Holdings: {holdings_str}"
    )
    return generate_structured(
        system_instruction,
        user_prompt,
        AIInsightContent,
        max_output_tokens=700,
    )


def generate_rebalance(
    weakest_ticker: str,
    weakest_sector: str,
    weakest_return: float,
    weakest_buy_price: float,
) -> RebalanceResponse:
    system_instruction = (
        "You are GrowwPro Smart Rebalancer, an advanced portfolio optimizer advisor. "
        "Identify strong alternative stock tickers from NSE/BSE belonging to the SAME "
        "sector as the underperforming stock. Respond strictly in structured JSON. "
        "Frame recommendations educationally and never promise returns."
    )
    user_prompt = (
        f"The underperforming stock is {weakest_ticker} in the {weakest_sector} sector. "
        f"It generated a return of {weakest_return:.1f}% on a buy price of "
        f"₹{weakest_buy_price:,.2f}. Recommend 2 strong alternatives in the "
        f"{weakest_sector} sector."
    )
    return generate_structured(
        system_instruction,
        user_prompt,
        RebalanceResponse,
        max_output_tokens=700,
    )


def generate_chat(
    message: str,
    history: List[Dict[str, str]],
    metrics: Dict[str, Any],
    holdings_str: str,
    sector_str: str,
) -> str:
    if not is_gemini_configured():
        raise RuntimeError("Gemini API key is not configured.")

    from google.genai import types

    system_instruction = (
        "You are GrowwPro AI Advisor, a professional financial analyst.\n"
        "Use the portfolio context below. Greetings and general financial questions "
        "are welcome. For direct buy, sell, or hold recommendations, say that you "
        "cannot provide individual-stock recommendations and suggest consulting a "
        "registered investment advisor. For off-topic questions, say you only assist "
        "with portfolio-related questions. Otherwise answer in 2-3 concise sentences "
        "and always end with a short disclaimer.\n\n"
        f"Value: ₹{metrics['summary']['total_current_value']:,.2f}, "
        f"Basis: ₹{metrics['summary']['total_cost_basis']:,.2f}, "
        f"Return: ₹{metrics['summary']['absolute_return']:,.2f} "
        f"({metrics['summary']['percentage_return']:.2f}%)\n"
        f"Risk: Volatility={metrics['risk_metrics']['volatility'] * 100:.1f}%, "
        f"Sharpe={metrics['risk_metrics']['sharpe_ratio']:.2f}, "
        f"Beta={metrics['risk_metrics']['beta']:.2f}, "
        f"MaxDD={metrics['risk_metrics']['max_drawdown'] * 100:.1f}%\n"
        f"Sectors: {sector_str}\n"
        f"Holdings: {holdings_str}"
    )
    history_text = "\n".join(
        f"{item.get('role', 'user').capitalize()}: {item.get('content', '')}"
        for item in history[-4:]
        if isinstance(item, dict) and isinstance(item.get("content"), str)
    )
    prompt = f"{history_text}\nUser: {message}" if history_text else message

    response = _get_client().models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
            max_output_tokens=150,
        ),
    )
    response_text = getattr(response, "text", None)
    if not response_text:
        raise ValueError("Gemini returned an empty chat response.")
    return response_text
