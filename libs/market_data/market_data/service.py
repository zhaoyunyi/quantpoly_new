"""市场数据应用服务（含缓存与限流）。"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any

from market_data.cache import InMemoryTTLCache
from market_data.domain import (
    BatchQuoteItem,
    MarketAsset,
    MarketCandle,
    MarketDataError,
    MarketQuote,
    RateLimitExceededError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from market_data.provider import MarketDataProvider
from market_data.rate_limit import SlidingWindowRateLimiter
from market_data.pipeline_store import InMemoryMarketDataPipelineStore


@dataclass
class QuoteResult:
    quote: MarketQuote
    cache_hit: bool
    source: str = "provider"


@dataclass
class BatchQuoteResult:
    items: list[BatchQuoteItem]
    timestamp: int


class MarketDataService:
    def __init__(
        self,
        *,
        provider: MarketDataProvider,
        quote_cache_ttl_seconds: int = 3,
        rate_limit_max_requests: int = 20,
        rate_limit_window_seconds: int = 10,
        cache: InMemoryTTLCache | None = None,
        quote_rate_limiter: SlidingWindowRateLimiter | None = None,
        pipeline_store: InMemoryMarketDataPipelineStore | None = None,
    ) -> None:
        self._provider = provider
        self._quote_cache_ttl_seconds = quote_cache_ttl_seconds
        self._cache = cache or InMemoryTTLCache()
        self._quote_rate_limiter = quote_rate_limiter or SlidingWindowRateLimiter(
            max_requests=rate_limit_max_requests,
            window_seconds=rate_limit_window_seconds,
        )
        self._pipeline_store = pipeline_store or InMemoryMarketDataPipelineStore()

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        return symbol.strip().upper()

    def _normalize_symbols(self, symbols: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for symbol in symbols:
            normalized = self._normalize_symbol(symbol)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return result

    def _consume_quote_limit(self, *, user_id: str) -> None:
        limit_key = f"quote:{user_id}"
        if not self._quote_rate_limiter.consume(limit_key):
            raise RateLimitExceededError()

    def _map_provider_error(self, exc: Exception) -> MarketDataError:
        if isinstance(exc, MarketDataError):
            return exc
        if isinstance(exc, TimeoutError):
            return UpstreamTimeoutError(str(exc))
        return UpstreamUnavailableError(str(exc))

    def search_assets(self, *, user_id: str, keyword: str, limit: int = 10) -> list[MarketAsset]:
        del user_id
        return self._provider.search(keyword=keyword, limit=limit)

    def list_catalog(self, *, user_id: str, limit: int = 100) -> list[MarketAsset]:
        del user_id
        if hasattr(self._provider, "list_assets"):
            items = self._provider.list_assets(limit=limit)
        else:
            items = self._provider.search(keyword="", limit=limit)

        result: list[MarketAsset] = []
        for item in items:
            normalized = self._normalize_symbol(item.symbol)
            if not normalized:
                continue
            if normalized != item.symbol:
                item = MarketAsset(
                    symbol=normalized,
                    name=item.name,
                    exchange=item.exchange,
                    currency=item.currency,
                    asset_class=item.asset_class,
                    tradable=item.tradable,
                    fractionable=item.fractionable,
                )
            result.append(item)

        return result[:limit]

    def list_symbols(self, *, user_id: str, limit: int = 100) -> list[str]:
        items = self.list_catalog(user_id=user_id, limit=limit)
        return [item.symbol for item in items]

    def get_latest_quote(self, *, user_id: str, symbol: str) -> QuoteResult:
        normalized_symbol = self._normalize_symbol(symbol)
        self._consume_quote_limit(user_id=user_id)

        cache_key = f"quote:{normalized_symbol}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return QuoteResult(quote=cached, cache_hit=True, source="cache")

        try:
            quote = self._provider.quote(symbol=normalized_symbol)
        except Exception as exc:  # noqa: BLE001
            raise self._map_provider_error(exc) from exc

        self._cache.set(cache_key, quote, ttl_seconds=self._quote_cache_ttl_seconds)
        return QuoteResult(quote=quote, cache_hit=False, source="provider")

    def get_quote(self, *, user_id: str, symbol: str) -> QuoteResult:
        return self.get_latest_quote(user_id=user_id, symbol=symbol)

    def get_quotes(self, *, user_id: str, symbols: list[str]) -> BatchQuoteResult:
        normalized_symbols = self._normalize_symbols(symbols)
        timestamp = int(time.time())
        if not normalized_symbols:
            return BatchQuoteResult(items=[], timestamp=timestamp)

        self._consume_quote_limit(user_id=user_id)

        cached_quotes: dict[str, MarketQuote] = {}
        missed_symbols: list[str] = []
        for symbol in normalized_symbols:
            cache_key = f"quote:{symbol}"
            cached = self._cache.get(cache_key)
            if cached is not None:
                cached_quotes[symbol] = cached
            else:
                missed_symbols.append(symbol)

        fetched_quotes: dict[str, MarketQuote] = {}
        if missed_symbols:
            try:
                if hasattr(self._provider, "batch_quote"):
                    fetched_quotes = self._provider.batch_quote(symbols=missed_symbols)
                else:
                    fetched_quotes = {symbol: self._provider.quote(symbol=symbol) for symbol in missed_symbols}
            except Exception as exc:  # noqa: BLE001
                raise self._map_provider_error(exc) from exc

            for symbol, quote in fetched_quotes.items():
                cache_key = f"quote:{self._normalize_symbol(symbol)}"
                self._cache.set(cache_key, quote, ttl_seconds=self._quote_cache_ttl_seconds)

        items: list[BatchQuoteItem] = []
        for symbol in normalized_symbols:
            if symbol in cached_quotes:
                items.append(
                    BatchQuoteItem(
                        symbol=symbol,
                        quote=cached_quotes[symbol],
                        status="ok",
                        cache_hit=True,
                        source="cache",
                    )
                )
                continue

            quote = fetched_quotes.get(symbol)
            if quote is None:
                items.append(
                    BatchQuoteItem(
                        symbol=symbol,
                        status="error",
                        error_code="QUOTE_NOT_AVAILABLE",
                        error_message=f"quote not available for {symbol}",
                        cache_hit=False,
                        source="provider",
                    )
                )
                continue

            items.append(
                BatchQuoteItem(
                    symbol=symbol,
                    quote=quote,
                    status="ok",
                    cache_hit=False,
                    source="provider",
                )
            )

        return BatchQuoteResult(items=items, timestamp=timestamp)

    def provider_health(self, *, user_id: str) -> dict:
        del user_id
        payload: dict = {
            "provider": self._provider.__class__.__name__.replace("Provider", "").lower() or "unknown",
            "healthy": False,
            "status": "unknown",
            "message": "provider health not available",
        }

        if hasattr(self._provider, "health"):
            try:
                raw = self._provider.health()
                if isinstance(raw, dict):
                    payload.update(raw)
            except Exception as exc:  # noqa: BLE001
                payload.update(
                    {
                        "healthy": False,
                        "status": "degraded",
                        "message": str(exc),
                    }
                )

        payload["timestamp"] = int(time.time())
        return payload

    def get_history(
        self,
        *,
        user_id: str,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str = "1Day",
        limit: int | None = None,
    ) -> list[MarketCandle]:
        del user_id
        return self._provider.history(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            limit=limit,
        )

    def sync_market_data(
        self,
        *,
        user_id: str,
        symbols: list[str],
        start_date: str,
        end_date: str,
        timeframe: str = "1Day",
    ) -> dict[str, Any]:
        """同步行情数据（迁移期：以 provider.history 抽样拉取）。"""

        normalized_symbols = self._normalize_symbols(symbols)
        results: list[dict[str, Any]] = []
        success_count = 0
        failure_count = 0

        for symbol in normalized_symbols:
            try:
                rows = self.get_history(
                    user_id=user_id,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=timeframe,
                )
                self._pipeline_store.record_synced_symbol(
                    user_id=user_id,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=timeframe,
                    row_count=len(rows),
                )
                results.append({"symbol": symbol, "status": "ok", "rowCount": len(rows)})
                success_count += 1
            except Exception as exc:  # noqa: BLE001
                mapped = self._map_provider_error(exc)
                results.append(
                    {
                        "symbol": symbol,
                        "status": "error",
                        "errorCode": mapped.code,
                        "errorMessage": mapped.message,
                        "retryable": mapped.retryable,
                    }
                )
                failure_count += 1

        return {
            "summary": {
                "totalSymbols": len(normalized_symbols),
                "successCount": success_count,
                "failureCount": failure_count,
                "startDate": start_date,
                "endDate": end_date,
                "timeframe": timeframe,
            },
            "items": results,
        }

    def record_sync_result(self, *, user_id: str, task_id: str, result: dict[str, Any]) -> None:
        self._pipeline_store.record_sync_result(user_id=user_id, task_id=task_id, result=result)

    def get_sync_result(self, *, user_id: str, task_id: str) -> dict[str, Any] | None:
        return self._pipeline_store.get_sync_result(user_id=user_id, task_id=task_id)

    @staticmethod
    def _parse_positive_int(raw_value: Any, *, default: int | None = None) -> int | None:
        candidate = raw_value if raw_value is not None else default
        if candidate is None:
            return None
        try:
            parsed = int(candidate)
        except (TypeError, ValueError):
            return None
        if parsed <= 0:
            return None
        return parsed

    @staticmethod
    def _parse_positive_float(raw_value: Any, *, default: float | None = None) -> float | None:
        candidate = raw_value if raw_value is not None else default
        if candidate is None:
            return None
        try:
            parsed = float(candidate)
        except (TypeError, ValueError):
            return None
        if parsed <= 0:
            return None
        return parsed

    @staticmethod
    def _ema_series(values: list[float], period: int) -> list[float]:
        if period <= 0 or len(values) < period:
            return []

        smoothing = 2.0 / (period + 1.0)
        seed = sum(values[:period]) / float(period)
        series = [seed]
        ema = seed
        for value in values[period:]:
            ema = (value - ema) * smoothing + ema
            series.append(ema)
        return series

    @staticmethod
    def _extract_indicator_parameters(spec: dict[str, Any]) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        for key in ('period', 'fast', 'slow', 'signal', 'stdDev', 'std_dev'):
            if key in spec and spec[key] is not None:
                normalized_key = 'stdDev' if key == 'std_dev' else key
                metadata[normalized_key] = spec[key]
        return metadata

    @classmethod
    def _build_unsupported_indicator(
        cls,
        *,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        output = {
            'name': name,
            'status': 'unsupported',
            'metadata': metadata or {},
        }
        period = cls._parse_positive_int((metadata or {}).get('period'))
        if period is not None:
            output['period'] = period
        return output

    @classmethod
    def _build_insufficient_indicator(
        cls,
        *,
        name: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        output = {
            'name': name,
            'status': 'insufficient_data',
            'metadata': metadata,
        }
        period = cls._parse_positive_int(metadata.get('period'))
        if period is not None:
            output['period'] = period
        return output

    @classmethod
    def _build_ok_indicator(
        cls,
        *,
        name: str,
        value: float,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        output = {
            'name': name,
            'status': 'ok',
            'value': float(value),
            'metadata': metadata,
        }
        period = cls._parse_positive_int(metadata.get('period'))
        if period is not None:
            output['period'] = period
        return output

    def _calculate_sma_indicator(self, *, close_prices: list[float], spec: dict[str, Any]) -> dict[str, Any]:
        period = self._parse_positive_int(spec.get('period'), default=20)
        if period is None:
            return self._build_unsupported_indicator(
                name='sma',
                metadata=self._extract_indicator_parameters(spec),
            )

        if len(close_prices) < period:
            return self._build_insufficient_indicator(
                name='sma',
                metadata={
                    'period': period,
                    'requiredDataPoints': period,
                    'actualDataPoints': len(close_prices),
                },
            )

        window = close_prices[-period:]
        value = sum(window) / float(period)
        return self._build_ok_indicator(name='sma', value=value, metadata={'period': period})

    def _calculate_ema_indicator(self, *, close_prices: list[float], spec: dict[str, Any]) -> dict[str, Any]:
        period = self._parse_positive_int(spec.get('period'), default=20)
        if period is None:
            return self._build_unsupported_indicator(
                name='ema',
                metadata=self._extract_indicator_parameters(spec),
            )

        ema_series = self._ema_series(close_prices, period)
        if not ema_series:
            return self._build_insufficient_indicator(
                name='ema',
                metadata={
                    'period': period,
                    'requiredDataPoints': period,
                    'actualDataPoints': len(close_prices),
                },
            )

        return self._build_ok_indicator(name='ema', value=ema_series[-1], metadata={'period': period})

    def _calculate_rsi_indicator(self, *, close_prices: list[float], spec: dict[str, Any]) -> dict[str, Any]:
        period = self._parse_positive_int(spec.get('period'), default=14)
        if period is None:
            return self._build_unsupported_indicator(
                name='rsi',
                metadata=self._extract_indicator_parameters(spec),
            )

        required_points = period + 1
        if len(close_prices) < required_points:
            return self._build_insufficient_indicator(
                name='rsi',
                metadata={
                    'period': period,
                    'requiredDataPoints': required_points,
                    'actualDataPoints': len(close_prices),
                },
            )

        prices = close_prices[-required_points:]
        deltas = [
            prices[idx] - prices[idx - 1]
            for idx in range(1, len(prices))
        ]
        gains = [max(delta, 0.0) for delta in deltas]
        losses = [abs(min(delta, 0.0)) for delta in deltas]

        average_gain = sum(gains) / float(period)
        average_loss = sum(losses) / float(period)

        if average_loss == 0 and average_gain == 0:
            rsi = 50.0
        elif average_loss == 0:
            rsi = 100.0
        else:
            relative_strength = average_gain / average_loss
            rsi = 100.0 - (100.0 / (1.0 + relative_strength))

        return self._build_ok_indicator(name='rsi', value=rsi, metadata={'period': period})

    def _calculate_macd_indicator(self, *, close_prices: list[float], spec: dict[str, Any]) -> dict[str, Any]:
        fast = self._parse_positive_int(spec.get('fast'), default=12)
        slow = self._parse_positive_int(spec.get('slow'), default=26)
        signal = self._parse_positive_int(spec.get('signal'), default=9)

        if fast is None or slow is None or signal is None or fast >= slow:
            return self._build_unsupported_indicator(
                name='macd',
                metadata=self._extract_indicator_parameters(spec),
            )

        if len(close_prices) < slow:
            return self._build_insufficient_indicator(
                name='macd',
                metadata={
                    'fast': fast,
                    'slow': slow,
                    'signal': signal,
                    'requiredDataPoints': slow,
                    'actualDataPoints': len(close_prices),
                },
            )

        macd_series: list[float] = []
        for index in range(slow - 1, len(close_prices)):
            prices = close_prices[: index + 1]
            fast_series = self._ema_series(prices, fast)
            slow_series = self._ema_series(prices, slow)
            if not fast_series or not slow_series:
                continue
            macd_series.append(fast_series[-1] - slow_series[-1])

        if not macd_series:
            return self._build_insufficient_indicator(
                name='macd',
                metadata={
                    'fast': fast,
                    'slow': slow,
                    'signal': signal,
                    'requiredDataPoints': slow,
                    'actualDataPoints': len(close_prices),
                },
            )

        signal_series = self._ema_series(macd_series, signal)
        macd_value = macd_series[-1]
        signal_value = signal_series[-1] if signal_series else macd_value
        histogram = macd_value - signal_value

        return self._build_ok_indicator(
            name='macd',
            value=macd_value,
            metadata={
                'fast': fast,
                'slow': slow,
                'signal': signal,
                'signalLine': signal_value,
                'histogram': histogram,
            },
        )

    def _calculate_bollinger_indicator(self, *, close_prices: list[float], spec: dict[str, Any]) -> dict[str, Any]:
        period = self._parse_positive_int(spec.get('period'), default=20)
        std_dev = self._parse_positive_float(spec.get('stdDev') or spec.get('std_dev'), default=2.0)

        if period is None or std_dev is None:
            return self._build_unsupported_indicator(
                name='bollinger',
                metadata=self._extract_indicator_parameters(spec),
            )

        if len(close_prices) < period:
            return self._build_insufficient_indicator(
                name='bollinger',
                metadata={
                    'period': period,
                    'stdDev': std_dev,
                    'requiredDataPoints': period,
                    'actualDataPoints': len(close_prices),
                },
            )

        window = close_prices[-period:]
        middle = sum(window) / float(period)
        variance = sum((price - middle) ** 2 for price in window) / float(period)
        deviation = math.sqrt(variance)
        upper = middle + std_dev * deviation
        lower = middle - std_dev * deviation

        return self._build_ok_indicator(
            name='bollinger',
            value=middle,
            metadata={
                'period': period,
                'stdDev': std_dev,
                'upperBand': upper,
                'lowerBand': lower,
            },
        )

    def calculate_indicators(
        self,
        *,
        user_id: str,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str,
        indicators: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """计算技术指标（SMA/EMA/RSI/MACD/BOLL）。"""

        normalized_symbol = self._normalize_symbol(symbol)
        rows = self.get_history(
            user_id=user_id,
            symbol=normalized_symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
        )
        close_prices = [float(row.close_price) for row in rows]

        calculators = {
            'sma': self._calculate_sma_indicator,
            'ema': self._calculate_ema_indicator,
            'rsi': self._calculate_rsi_indicator,
            'macd': self._calculate_macd_indicator,
            'bollinger': self._calculate_bollinger_indicator,
        }

        outputs: list[dict[str, Any]] = []
        for raw_spec in indicators:
            spec = raw_spec if isinstance(raw_spec, dict) else {}
            name = str(spec.get('name') or '').strip().lower() or 'unknown'
            calculator = calculators.get(name)
            if calculator is None:
                outputs.append(
                    self._build_unsupported_indicator(
                        name=name,
                        metadata=self._extract_indicator_parameters(spec),
                    )
                )
                continue

            outputs.append(calculator(close_prices=close_prices, spec=spec))

        return {
            'symbol': normalized_symbol,
            'startDate': start_date,
            'endDate': end_date,
            'timeframe': timeframe,
            'indicators': outputs,
        }

    def boundary_check(self, *, user_id: str, symbols: list[str]) -> dict[str, Any]:
        """边界一致性校验：对账预期 symbols 与已同步 symbols。"""

        from data_topology_boundary.reconciliation import reconcile_by_key

        normalized_symbols = self._normalize_symbols(symbols)
        before_rows = [{"symbol": symbol} for symbol in normalized_symbols]
        after_rows = [{"symbol": symbol} for symbol in self._pipeline_store.list_synced_symbols(user_id=user_id)]
        report = reconcile_by_key(before_rows=before_rows, after_rows=after_rows, key="symbol")

        return {
            "consistent": report.consistent,
            "missingIds": report.missing_ids,
            "extraIds": report.extra_ids,
            "mismatchCount": report.mismatch_count,
            "beforeCount": report.before_count,
            "afterCount": report.after_count,
        }
