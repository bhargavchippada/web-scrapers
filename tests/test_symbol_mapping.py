# Version: v1.0
"""Unit tests for symbol mapping utilities."""

from web_scrapers.utils.symbol_mapping import (
    get_all_symbols,
    get_company_names,
    is_relevant_to_symbol,
)


class TestGetCompanyNames:
    """Tests for get_company_names function."""

    def test_known_symbol(self):
        """Test getting names for known symbol."""
        names = get_company_names("AAPL")
        assert "Apple" in names
        assert "iPhone" in names

    def test_unknown_symbol(self):
        """Test getting names for unknown symbol."""
        names = get_company_names("UNKN")
        assert names == ["UNKN"]

    def test_case_insensitive(self):
        """Test case insensitivity."""
        names_upper = get_company_names("MSFT")
        names_lower = get_company_names("msft")
        assert names_upper == names_lower

    def test_google_variants(self):
        """Test Google symbol variants."""
        googl_names = get_company_names("GOOGL")
        goog_names = get_company_names("GOOG")
        assert "Google" in googl_names
        assert "Google" in goog_names

    def test_meta_names(self):
        """Test Meta/Facebook names."""
        names = get_company_names("META")
        assert "Meta" in names
        assert "Facebook" in names
        assert "Instagram" in names


class TestIsRelevantToSymbol:
    """Tests for is_relevant_to_symbol function."""

    def test_direct_symbol_match(self):
        """Test direct symbol match."""
        assert is_relevant_to_symbol("AAPL stock rises 5%", "AAPL")
        assert is_relevant_to_symbol("Buy $AAPL now", "AAPL")
        assert is_relevant_to_symbol("(AAPL) earnings beat", "AAPL")

    def test_company_name_match(self):
        """Test company name match."""
        assert is_relevant_to_symbol("Apple announces new iPhone", "AAPL")
        assert is_relevant_to_symbol("Microsoft releases Windows update", "MSFT")
        assert is_relevant_to_symbol("Tesla Cybertruck deliveries begin", "TSLA")

    def test_ceo_mention(self):
        """Test CEO name matching."""
        assert is_relevant_to_symbol("Tim Cook announces Apple event", "AAPL")
        assert is_relevant_to_symbol("Elon Musk tweets about Tesla", "TSLA")
        assert is_relevant_to_symbol("Jensen Huang presents at GTC", "NVDA")

    def test_product_mention(self):
        """Test product name matching."""
        assert is_relevant_to_symbol("New iPhone 16 leaked", "AAPL")
        assert is_relevant_to_symbol("Xbox Series X review", "MSFT")
        assert is_relevant_to_symbol("AWS outage affects services", "AMZN")

    def test_no_match(self):
        """Test non-matching text."""
        assert not is_relevant_to_symbol("Random news about weather", "AAPL")
        assert not is_relevant_to_symbol("Sports game results", "MSFT")

    def test_case_insensitive_match(self):
        """Test case insensitivity."""
        assert is_relevant_to_symbol("apple stock", "AAPL")
        assert is_relevant_to_symbol("APPLE STOCK", "AAPL")
        assert is_relevant_to_symbol("Apple Stock", "AAPL")

    def test_avoid_partial_matches(self):
        """Test that partial matches are avoided."""
        # "AAPL" should not match "BAAPL"
        assert not is_relevant_to_symbol("BAAPL is not a stock", "AAPL")

    def test_multiple_mentions(self):
        """Test text with multiple relevant mentions."""
        text = "Apple iPhone sales boost AAPL stock, Tim Cook celebrates"
        assert is_relevant_to_symbol(text, "AAPL")


class TestGetAllSymbols:
    """Tests for get_all_symbols function."""

    def test_returns_list(self):
        """Test that function returns a list."""
        symbols = get_all_symbols()
        assert isinstance(symbols, list)

    def test_contains_common_symbols(self):
        """Test that common symbols are present."""
        symbols = get_all_symbols()
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" in symbols
        assert "AMZN" in symbols
        assert "TSLA" in symbols

    def test_no_duplicates(self):
        """Test that there are no duplicate symbols."""
        symbols = get_all_symbols()
        assert len(symbols) == len(set(symbols))


class TestPublicAPIExports:
    """Tests for symbol mapping exports in main package."""

    def test_exports_from_root(self):
        """Test that symbol mapping is exported from root module."""
        from web_scrapers import (
            get_all_symbols,
            get_company_names,
            is_relevant_to_symbol,
        )

        assert callable(get_company_names)
        assert callable(is_relevant_to_symbol)
        assert callable(get_all_symbols)

    def test_exports_from_utils(self):
        """Test that symbol mapping is exported from utils module."""
        from web_scrapers.utils import (
            get_all_symbols,
            get_company_names,
            is_relevant_to_symbol,
        )

        assert callable(get_company_names)
        assert callable(is_relevant_to_symbol)
        assert callable(get_all_symbols)
