class TradingBotError(Exception):
    """Base error for trading bot failures."""


class ConfigError(TradingBotError):
    """Invalid or missing configuration."""


class ValidationError(TradingBotError):
    """Invalid user input or exchange constraints."""


class ApiError(TradingBotError):
    """Binance API returned an error."""


class NetworkError(TradingBotError):
    """Network or timeout errors."""
