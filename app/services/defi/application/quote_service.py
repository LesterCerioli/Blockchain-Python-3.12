import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from ..domain.entities.asset_quote import AssetQuote
from ..domain.exceptions import (
    NoPoolsForPairError,
    SlippageExceededError,
    TokenNotFoundError,
)
from ..domain.interfaces.market_data_provider import IMarketDataProvider
from ..domain.interfaces.pool_repository import IPoolRepository
from ..domain.interfaces.price_oracle import IPriceOracle
from ..domain.interfaces.quote_cache import IQuoteCache
from ..domain.interfaces.swap_service import ISwapService
from ..domain.interfaces.token_repository import ITokenRepository
from ..domain.value_objects.ohlcv_candle import OHLCVCandle
from ..domain.value_objects.price_point import PricePoint
from ..domain.value_objects.slippage import Slippage
from ..domain.value_objects.token_amount import TokenAmount


class SwapQuoteService:
    
    def __init__(
        self,
        token_repository: ITokenRepository,
        pool_repository: IPoolRepository,
        price_oracle: IPriceOracle,
        swap_service: ISwapService,
    ) -> None:
        self._tokens = token_repository
        self._pools = pool_repository
        self._oracle = price_oracle
        self._swap = swap_service

    async def get_quote(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in_raw: int,
        chain_id: int,
        slippage: Slippage,
    ) -> dict:
        token_in = await self._tokens.get_by_address(token_in_address, chain_id)
        if token_in is None:
            raise TokenNotFoundError(token_in_address, chain_id)

        token_out = await self._tokens.get_by_address(token_out_address, chain_id)
        if token_out is None:
            raise TokenNotFoundError(token_out_address, chain_id)

        pools = await self._pools.list_by_tokens(token_in_address, token_out_address, chain_id)
        if not pools:
            raise NoPoolsForPairError(token_in_address, token_out_address, chain_id)

        amount_in = TokenAmount(
            raw=amount_in_raw,
            decimals=token_in.decimals,
            token_address=token_in_address,
        )
        amount_out = await self._swap.get_quote(
            token_in_address, token_out_address, amount_in, chain_id
        )

        price_impact = await self._calculate_price_impact(
            token_in_address, token_out_address, amount_in, amount_out, chain_id
        )

        actual_bps = int(
            Decimal(str(price_impact))
            .scaleb(4)
            .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        if actual_bps > slippage.bps:
            raise SlippageExceededError(expected_bps=slippage.bps, actual_bps=actual_bps)

        return {
            "token_in": token_in_address,
            "token_out": token_out_address,
            "amount_in": str(amount_in.as_decimal),
            "amount_out": str(amount_out.as_decimal),
            "price_impact_bps": actual_bps,
            "slippage_bps": slippage.bps,
            "pool_count": len(pools),
        }

    async def _calculate_price_impact(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: TokenAmount,
        amount_out: TokenAmount,
        chain_id: int,
    ) -> Decimal:
        spot = await self._oracle.get_price(token_in_address, token_out_address, chain_id)
        if spot is None or spot.value == 0:
            return Decimal(0)
        expected_out = amount_in.as_decimal * spot.value
        if expected_out == 0:
            return Decimal(0)
        return abs(expected_out - amount_out.as_decimal) / expected_out


_CACHE_TTL = 60
_DEFAULT_CHAIN_ID = 1

_SYMBOL_MAP: dict[str, tuple[str, int]] = {
    "BTC": ("0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", 1),
    "ETH": ("0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", 1),
    "USDT": ("0xdac17f958d2ee523a2206206994597c13d831ec7", 1),
    "USDC": ("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", 1),
    "SOL": ("0xd31a59c85ae9d8edefec411d448f90841571b89c", 1),
    "BNB": ("0xB8c77482e45F1F44dE1745F52C74426C631bDD52", 1),
    "ADA": ("0x3EE2200Efb3400fAbB9AacF31297cBdD1d435D47", 1),
    "DOGE": ("0x42069309949aE87BeDefd91Cb29b3c6f3C5C8c7B", 1),
    "XRP": ("0x1D2F0da169ceB9fC7B3144628dB156f3F6c60dBE", 1),
    "DOT": ("0xb1A88c3309149021896572F539eEBb105D7FDa87", 1),
}


def _resolve(symbol: str) -> tuple[str, int]:
    upper = symbol.upper()
    return _SYMBOL_MAP.get(upper, (upper, _DEFAULT_CHAIN_ID))


class QuoteService:

    def __init__(
        self,
        provider: IMarketDataProvider,
        cache: IQuoteCache,
    ) -> None:
        self._provider = provider
        self._cache = cache

    async def get_quote(self, symbol: str) -> AssetQuote:
        cached = await self._cache.get(f"quote:{symbol.upper()}")
        if cached is not None:
            return cached
        return await self._fetch_and_cache(symbol)

    async def get_quotes(self, symbols: list[str]) -> list[AssetQuote]:
        if not symbols:
            return []

        keys = [f"quote:{s.upper()}" for s in symbols]
        cached_list = await self._cache.get_many(keys)

        result: list[AssetQuote] = []
        misses: list[str] = []
        miss_keys: list[str] = []

        for symbol, cached in zip(symbols, cached_list):
            if cached is not None:
                result.append(cached)
            else:
                misses.append(symbol)
                miss_keys.append(f"quote:{symbol.upper()}")

        if misses:
            tasks = [self._fetch_and_cache(s) for s in misses]
            fetched = await asyncio.gather(*tasks)
            result.extend(fetched)

        return result

    async def _fetch_and_cache(self, symbol: str) -> AssetQuote:
        address, chain_id = _resolve(symbol)
        price, change_24h, volume_24h, market_cap = await asyncio.gather(
            self._provider.get_token_price(address, chain_id),
            self._provider.get_price_change_24h(address, chain_id),
            self._provider.get_token_volume_24h(address, chain_id),
            self._provider.get_market_cap(address, chain_id),
        )

        quote = AssetQuote(
            symbol=symbol.upper(),
            price_usd=price.value if price is not None else Decimal(0),
            change_24h=change_24h,
            volume_24h=volume_24h if volume_24h is not None else Decimal(0),
            market_cap=market_cap if market_cap is not None else Decimal(0),
            fetched_at=datetime.now(tz=timezone.utc),
        )

        await self._cache.set(f"quote:{symbol.upper()}", quote, _CACHE_TTL)
        return quote

    async def get_ohlcv(
        self,
        symbol: str,
        interval: str,
        from_ts: datetime,
        to_ts: datetime,
    ) -> list[OHLCVCandle]:
        cache_key = f"ohlcv:{symbol.upper()}:{interval}:{int(from_ts.timestamp())}:{int(to_ts.timestamp())}"

        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached

        address, chain_id = _resolve(symbol)
        price_points = await self._provider.get_historical_prices(
            address,
            chain_id,
            from_timestamp=int(from_ts.timestamp()),
            to_timestamp=int(to_ts.timestamp()),
        )

        interval_secs = _interval_to_seconds(interval)
        candles = _price_points_to_candles(price_points, interval_secs)

        await self._cache.set(cache_key, candles, _CACHE_TTL)
        return candles


def _interval_to_seconds(interval: str) -> int:
    unit = interval[-1:]
    value = int(interval[:-1])
    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 3600
    if unit == "d":
        return value * 86400
    if unit == "w":
        return value * 604800
    return 3600


def _price_points_to_candles(
    price_points: list[PricePoint],
    interval_secs: int,
) -> list[OHLCVCandle]:
    buckets: dict[int, list[Decimal]] = defaultdict(list)
    for pp in price_points:
        bucket_ts = (pp.timestamp // interval_secs) * interval_secs
        buckets[bucket_ts].append(pp.price.value)

    candles: list[OHLCVCandle] = []
    for ts in sorted(buckets):
        prices = buckets[ts]
        candles.append(
            OHLCVCandle(
                timestamp=datetime.fromtimestamp(ts, tz=timezone.utc),
                open=prices[0],
                high=max(prices),
                low=min(prices),
                close=prices[-1],
            )
        )
    return candles
