# Version: v1.0
"""Symbol to company name mapping for news/content relevance detection.

Shared utility for mapping stock ticker symbols to company names, products,
and related terms. Used for filtering news articles and social media posts
by stock symbol relevance.

Originally from agentic-trader, now shared via web-scrapers.
"""

from functools import lru_cache

# Common stock symbols to company names and related terms
SYMBOL_TO_COMPANY: dict[str, list[str]] = {
    # Technology - Mega Caps
    "AAPL": ["Apple", "Apple Inc", "iPhone", "iPad", "Mac", "MacBook", "Tim Cook"],
    "GOOGL": ["Google", "Alphabet", "YouTube", "Android", "Waymo", "DeepMind", "Sundar Pichai"],
    "GOOG": ["Google", "Alphabet", "YouTube", "Android", "Waymo", "DeepMind"],
    "MSFT": ["Microsoft", "Windows", "Azure", "Xbox", "LinkedIn", "GitHub", "Satya Nadella"],
    "AMZN": ["Amazon", "AWS", "Alexa", "Prime", "Andy Jassy", "Jeff Bezos"],
    "META": ["Meta", "Facebook", "Instagram", "WhatsApp", "Oculus", "Mark Zuckerberg"],
    "TSLA": ["Tesla", "Elon Musk", "SpaceX", "Cybertruck", "Model S", "Model 3", "Model Y"],
    "NVDA": ["Nvidia", "NVIDIA", "GeForce", "CUDA", "Jensen Huang", "H100", "A100"],
    "AMD": ["AMD", "Advanced Micro Devices", "Ryzen", "Radeon", "EPYC", "Lisa Su"],
    "INTC": ["Intel", "Core", "Xeon", "Pat Gelsinger"],
    # Technology - Software/Cloud
    "CRM": ["Salesforce", "Marc Benioff"],
    "ORCL": ["Oracle", "Larry Ellison"],
    "IBM": ["IBM", "International Business Machines", "Watson"],
    "ADBE": ["Adobe", "Photoshop", "Creative Cloud"],
    "SNOW": ["Snowflake"],
    "PLTR": ["Palantir", "Peter Thiel"],
    "NET": ["Cloudflare"],
    "DDOG": ["Datadog"],
    "MDB": ["MongoDB"],
    # Streaming/Media
    "NFLX": ["Netflix", "Ted Sarandos"],
    "DIS": ["Disney", "Disney+", "Marvel", "Pixar", "ESPN", "Bob Iger"],
    "WBD": ["Warner Bros", "Discovery", "HBO", "Max"],
    "PARA": ["Paramount", "CBS"],
    # E-commerce/Retail
    "WMT": ["Walmart", "Wal-Mart", "Doug McMillon"],
    "COST": ["Costco"],
    "TGT": ["Target"],
    "HD": ["Home Depot"],
    "LOW": ["Lowes", "Lowe's"],
    # Finance
    "JPM": ["JPMorgan", "JP Morgan", "Chase", "Jamie Dimon"],
    "BAC": ["Bank of America", "BofA"],
    "WFC": ["Wells Fargo"],
    "GS": ["Goldman Sachs", "Goldman"],
    "MS": ["Morgan Stanley"],
    "C": ["Citigroup", "Citibank", "Citi"],
    "V": ["Visa"],
    "MA": ["Mastercard", "MasterCard"],
    "PYPL": ["PayPal"],
    "SQ": ["Square", "Block Inc", "Jack Dorsey"],
    "COIN": ["Coinbase", "Brian Armstrong"],
    # Healthcare
    "JNJ": ["Johnson & Johnson", "J&J"],
    "UNH": ["UnitedHealth", "United Health"],
    "PFE": ["Pfizer"],
    "MRNA": ["Moderna"],
    "ABBV": ["AbbVie"],
    "LLY": ["Eli Lilly", "Lilly"],
    "MRK": ["Merck"],
    # Energy
    "XOM": ["Exxon", "ExxonMobil"],
    "CVX": ["Chevron"],
    "COP": ["ConocoPhillips"],
    "OXY": ["Occidental", "Occidental Petroleum"],
    # Automotive
    "F": ["Ford", "Ford Motor"],
    "GM": ["General Motors", "GM", "Chevy", "Chevrolet"],
    "RIVN": ["Rivian"],
    "LCID": ["Lucid", "Lucid Motors"],
    # Airlines
    "UAL": ["United Airlines", "United"],
    "DAL": ["Delta", "Delta Airlines"],
    "AAL": ["American Airlines", "American"],
    "LUV": ["Southwest", "Southwest Airlines"],
    # Consumer
    "KO": ["Coca-Cola", "Coke"],
    "PEP": ["Pepsi", "PepsiCo"],
    "MCD": ["McDonald's", "McDonalds"],
    "SBUX": ["Starbucks"],
    "NKE": ["Nike"],
    # Semiconductors
    "AVGO": ["Broadcom"],
    "QCOM": ["Qualcomm"],
    "TXN": ["Texas Instruments"],
    "AMAT": ["Applied Materials"],
    "LRCX": ["Lam Research"],
    "KLAC": ["KLA"],
    "ASML": ["ASML"],
    "TSM": ["TSMC", "Taiwan Semiconductor"],
    "MU": ["Micron"],
    # AI/ML focused
    "AI": ["C3.ai", "C3 AI"],
    "PATH": ["UiPath"],
    # Crypto
    "BTC": ["Bitcoin", "BTC"],
    "ETH": ["Ethereum", "ETH", "Ether"],
    "MSTR": ["MicroStrategy", "Michael Saylor"],
}


@lru_cache(maxsize=1000)
def get_company_names(symbol: str) -> list[str]:
    """Get company names and related terms for a symbol.

    Args:
        symbol: Stock ticker symbol (case insensitive)

    Returns:
        List of company names/terms to search for.
        Returns [symbol] if no mapping exists.
    """
    return SYMBOL_TO_COMPANY.get(symbol.upper(), [symbol.upper()])


def is_relevant_to_symbol(text: str, symbol: str) -> bool:
    """Check if text is relevant to a symbol.

    Searches for both the ticker symbol and company name/related terms.

    Args:
        text: Text to check (title, summary, etc.)
        symbol: Stock symbol

    Returns:
        True if text mentions the symbol or company
    """
    text_upper = text.upper()
    symbol_upper = symbol.upper()

    # Direct symbol match (with word boundaries to avoid false positives)
    # e.g., "AAPL" should match but not "BAAPL"
    symbol_patterns = [
        f" {symbol_upper} ",
        f" {symbol_upper}:",
        f" {symbol_upper},",
        f" {symbol_upper}.",
        f"({symbol_upper})",
        f"${symbol_upper}",
    ]

    for pattern in symbol_patterns:
        if pattern in f" {text_upper} ":
            return True

    # Company name matches
    for name in get_company_names(symbol):
        if name.upper() in text_upper:
            return True

    return False


def get_all_symbols() -> list[str]:
    """Get all symbols with company name mappings.

    Returns:
        List of all mapped symbols
    """
    return list(SYMBOL_TO_COMPANY.keys())


__all__ = ["get_company_names", "is_relevant_to_symbol", "get_all_symbols"]
