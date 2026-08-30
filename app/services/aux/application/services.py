from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import ClassVar

from app.services.aux.infrastructure.dynamodb_client import (
    TABLE_AUDIT,
    TABLE_KYC,
    TABLE_METADATA,
    TABLE_OHLCV,
    TABLE_POSITIONS,
    TABLE_RATE_LIMITS,
    TABLE_SESSIONS,
    TABLE_TOKEN_META,
    TABLE_USERS,
    DynamoDBClient,
    generate_id,
    now_ms,
)


def resolve_user_id_by_email(email: str) -> str:
    items = DynamoDBClient().query_index(
        TABLE_USERS, "email_index", "email", email.strip().lower()
    )
    if not items:
        raise ValueError("user not found for this email")
    return items[0]["user_id"]["S"]


class ApprovedAction(str, Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    KYC_SUBMIT = "KYC_SUBMIT"
    KYC_APPROVE = "KYC_APPROVE"
    KYC_REJECT = "KYC_REJECT"
    TOKEN_CREATE = "TOKEN_CREATE"
    SWAP = "SWAP"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SESSION_REFRESH = "SESSION_REFRESH"


class SessionService:
    INACTIVITY_LIMIT_MS = 3 * 60 * 1000

    def __init__(self, client: DynamoDBClient | None = None) -> None:
        self._db = client or DynamoDBClient()

    def _resolve(self, session_id: str) -> dict | None:
        items = self._db.query_index(
            TABLE_SESSIONS, "session_id_index", "session_id", session_id
        )
        return items[0] if items else None

    def _resolve_by_email(self, email: str) -> dict | None:
        user_id = resolve_user_id_by_email(email)
        items = self._db.query_index(
            TABLE_SESSIONS, "user_id_index", "user_id", user_id
        )
        if not items:
            return None
        items.sort(
            key=lambda i: int(i.get("created_at", {"N": "0"})["N"]), reverse=True
        )
        return items[0]

    def create(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        max_duration_ms: int = 8 * 60 * 60 * 1000,
    ) -> str:
        user_id = resolve_user_id_by_email(email)
        ts = now_ms()
        session_id = generate_id()
        item = {
            "id": {"S": generate_id()},
            "session_id": {"S": session_id},
            "user_id": {"S": user_id},
            "expires_at": {"N": str(ts + max_duration_ms)},
            "ip_address": {"S": ip_address},
            "user_agent": {"S": user_agent},
            "created_at": {"N": str(ts)},
            "last_accessed": {"N": str(ts)},
        }
        return self._db.put_item(TABLE_SESSIONS, item)

    def get(self, session_id: str) -> dict | None:
        return self._resolve(session_id)

    def get_by_email(self, email: str) -> dict | None:
        return self._resolve_by_email(email)

    def is_active(self, session_id: str) -> bool:
        item = self._resolve(session_id)
        if not item:
            return False
        ts = now_ms()
        expires_at = int(item["expires_at"]["N"])
        last_accessed = int(item["last_accessed"]["N"])
        within_max = ts <= expires_at
        within_inactivity = ts <= last_accessed + self.INACTIVITY_LIMIT_MS
        return within_max and within_inactivity

    def is_active_by_email(self, email: str) -> bool:
        item = self._resolve_by_email(email)
        if not item:
            return False
        ts = now_ms()
        expires_at = int(item["expires_at"]["N"])
        last_accessed = int(item["last_accessed"]["N"])
        within_max = ts <= expires_at
        within_inactivity = ts <= last_accessed + self.INACTIVITY_LIMIT_MS
        return within_max and within_inactivity

    def refresh(self, session_id: str) -> None:
        item = self._resolve(session_id)
        if not item:
            raise ValueError("session not found")
        ts = now_ms()
        self._db.update_item(
            TABLE_SESSIONS,
            key={"id": {"S": item["id"]["S"]}},
            update_expression="SET #la = :ts, #ea = :ea",
            expr_names={"#la": "last_accessed", "#ea": "expires_at"},
            expr_values={
                ":ts": {"N": str(ts)},
                ":ea": {"N": str(ts + 8 * 60 * 60 * 1000)},
            },
        )

    def refresh_by_email(self, email: str) -> None:
        item = self._resolve_by_email(email)
        if not item:
            raise ValueError("session not found")
        ts = now_ms()
        self._db.update_item(
            TABLE_SESSIONS,
            key={"id": {"S": item["id"]["S"]}},
            update_expression="SET #la = :ts, #ea = :ea",
            expr_names={"#la": "last_accessed", "#ea": "expires_at"},
            expr_values={
                ":ts": {"N": str(ts)},
                ":ea": {"N": str(ts + 8 * 60 * 60 * 1000)},
            },
        )

    def delete(self, session_id: str) -> None:
        item = self._resolve(session_id)
        if not item:
            raise ValueError("session not found")
        self._db.delete_item(TABLE_SESSIONS, item["id"]["S"])

    def delete_by_email(self, email: str) -> None:
        item = self._resolve_by_email(email)
        if not item:
            raise ValueError("session not found")
        self._db.delete_item(TABLE_SESSIONS, item["id"]["S"])


class KycService:
    def __init__(self, client: DynamoDBClient | None = None) -> None:
        self._db = client or DynamoDBClient()

    def create(
        self,
        email: str,
        full_name: str,
        verification_level: str,
        identity_document: str,
        document_path: str,
        attached_documents: list[str] | None = None,
        version: int = 1,
    ) -> str:
        if version < 1:
            raise ValueError("KYC version must be >= 1")
        user_id = resolve_user_id_by_email(email)
        item = {
            "id": {"S": generate_id()},
            "user_id": {"S": user_id},
            "version": {"N": str(version)},
            "full_name": {"S": full_name},
            "verification_level": {"S": verification_level},
            "identity_document": {"S": identity_document},
            "document_path": {"S": document_path},
            "last_updated": {"N": str(now_ms())},
        }
        if attached_documents:
            item["attached_documents"] = {"SS": attached_documents}
        return self._db.put_item(TABLE_KYC, item)

    def get_by_user(self, user_id: str) -> list[dict]:
        return self._db.query_index(TABLE_KYC, "user_index", "user_id", user_id)

    def get_by_email(self, email: str) -> list[dict]:
        user_id = resolve_user_id_by_email(email)
        return self.get_by_user(user_id)

    def increment_version(
        self,
        email: str,
        full_name: str,
        verification_level: str,
        identity_document: str,
        document_path: str,
        attached_documents: list[str] | None = None,
    ) -> None:
        user_id = resolve_user_id_by_email(email)
        items = self.get_by_user(user_id)
        if not items:
            raise ValueError("KYC profile not found")
        latest = max(items, key=lambda i: int(i.get("version", {"N": "0"})["N"]))
        new_version = int(latest["version"]["N"]) + 1
        self._update_profile(
            latest["id"]["S"],
            full_name,
            verification_level,
            identity_document,
            document_path,
            attached_documents,
            new_version,
        )

    def _update_profile(
        self,
        item_id: str,
        full_name: str,
        verification_level: str,
        identity_document: str,
        document_path: str,
        attached_documents: list[str] | None,
        new_version: int,
    ) -> None:
        names = {
            "#v": "version",
            "#n": "full_name",
            "#l": "verification_level",
            "#d": "identity_document",
            "#p": "document_path",
            "#u": "last_updated",
        }
        values = {
            ":v": {"N": str(new_version)},
            ":n": {"S": full_name},
            ":l": {"S": verification_level},
            ":d": {"S": identity_document},
            ":p": {"S": document_path},
            ":u": {"N": str(now_ms())},
        }
        expression = "SET #v = :v, #n = :n, #l = :l, #d = :d, #p = :p, #u = :u"
        if attached_documents:
            names["#a"] = "attached_documents"
            values[":a"] = {"SS": attached_documents}
            expression += ", #a = :a"
        self._db.update_item(
            TABLE_KYC,
            key={"id": {"S": item_id}},
            update_expression=expression,
            expr_names=names,
            expr_values=values,
        )


class MetadataService:
    def __init__(self, client: DynamoDBClient | None = None) -> None:
        self._db = client or DynamoDBClient()

    def create(self, email: str, metadata_key: str, metadata_value: str) -> str:
        if not metadata_key or not metadata_key.strip():
            raise ValueError("metadata_key cannot be empty")
        user_id = resolve_user_id_by_email(email)
        item = {
            "id": {"S": generate_id()},
            "user_id": {"S": user_id},
            "metadata_key": {"S": metadata_key},
            "metadata_value": {"S": metadata_value},
            "updated_at": {"N": str(now_ms())},
        }
        return self._db.put_item(TABLE_METADATA, item)

    def get_by_user(self, user_id: str) -> list[dict]:
        return self._db.query_index(
            TABLE_METADATA, "user_meta_index", "user_id", user_id
        )

    def get_by_email(self, email: str) -> list[dict]:
        user_id = resolve_user_id_by_email(email)
        return self.get_by_user(user_id)


class AuditService:
    def __init__(self, client: DynamoDBClient | None = None) -> None:
        self._db = client or DynamoDBClient()

    def create(
        self,
        email: str,
        action: ApprovedAction | str,
        resource: str,
        details: str,
    ) -> str:
        if isinstance(action, ApprovedAction):
            action_value = action.value
        elif action in ApprovedAction._value2member_map_:
            action_value = action
        else:
            raise ValueError(f"Audit action not approved: {action}")
        user_id = resolve_user_id_by_email(email)
        item = {
            "id": {"S": generate_id()},
            "log_id": {"S": generate_id()},
            "user_id": {"S": user_id},
            "action": {"S": action_value},
            "resource": {"S": resource},
            "details": {"S": details},
            "created_at": {"N": str(now_ms())},
        }
        return self._db.put_item(TABLE_AUDIT, item)

    def get_by_user(self, user_id: str) -> list[dict]:
        return self._db.query_index(TABLE_AUDIT, "user_index", "user_id", user_id)

    def get_by_action(self, action: str) -> list[dict]:
        return self._db.query_index(TABLE_AUDIT, "action_index", "action", action)

    def get_by_email(self, email: str) -> list[dict]:
        user_id = resolve_user_id_by_email(email)
        return self.get_by_user(user_id)


class RateLimitService:
    def __init__(self, client: DynamoDBClient | None = None) -> None:
        self._db = client or DynamoDBClient()

    def increment(self, key: str, time_window_ms: int) -> int:
        ts = now_ms()
        existing = self._db.query_index(TABLE_RATE_LIMITS, "key_index", "key", key)
        if existing:
            item_id = existing[0]["id"]["S"]
            self._db._client.update_item(
                TableName=TABLE_RATE_LIMITS,
                Key={"id": {"S": item_id}},
                UpdateExpression="ADD #c :inc SET #r = :r, #w = :w",
                ExpressionAttributeNames={
                    "#c": "count",
                    "#r": "reset_at",
                    "#w": "time_window",
                },
                ExpressionAttributeValues={
                    ":inc": {"N": "1"},
                    ":r": {"N": str(ts + time_window_ms)},
                    ":w": {"N": str(time_window_ms)},
                },
            )
        else:
            item = {
                "id": {"S": generate_id()},
                "key": {"S": key},
                "count": {"N": "1"},
                "reset_at": {"N": str(ts + time_window_ms)},
                "time_window": {"N": str(time_window_ms)},
            }
            self._db.put_item(TABLE_RATE_LIMITS, item)
        return self._count_for(key)

    def _count_for(self, key: str) -> int:
        items = self._db.query_index(TABLE_RATE_LIMITS, "key_index", "key", key)
        if not items:
            return 0
        return sum(int(i.get("count", {"N": "0"})["N"]) for i in items)

    def get(self, key: str) -> list[dict]:
        return self._db.query_index(TABLE_RATE_LIMITS, "key_index", "key", key)

    def reset(self, key: str) -> None:
        for item in self._db.query_index(TABLE_RATE_LIMITS, "key_index", "key", key):
            self._db.delete_item(TABLE_RATE_LIMITS, item["id"]["S"])


class TokenMetaService:
    def __init__(self, client: DynamoDBClient | None = None) -> None:
        self._db = client or DynamoDBClient()

    def upsert(
        self,
        symbol: str,
        volume_24h: Decimal,
        max_price_24h: Decimal,
        min_price_24h: Decimal,
        current_price: Decimal,
        last_check: str,
    ) -> str:
        for name, value in (
            ("volume_24h", volume_24h),
            ("max_price_24h", max_price_24h),
            ("min_price_24h", min_price_24h),
            ("current_price", current_price),
        ):
            if value < 0:
                raise ValueError(f"{name} must be >= 0")
        item = {
            "id": {"S": generate_id()},
            "symbol": {"S": symbol},
            "updated_at": {"N": str(now_ms())},
            "volume_24h": {"N": str(volume_24h)},
            "max_price_24h": {"N": str(max_price_24h)},
            "min_price_24h": {"N": str(min_price_24h)},
            "current_price": {"N": str(current_price)},
            "last_check": {"S": last_check},
        }
        return self._db.put_item(TABLE_TOKEN_META, item)

    def get_by_symbol(self, symbol: str) -> list[dict]:
        return self._db.query_index(TABLE_TOKEN_META, "symbol_index", "symbol", symbol)


class OhlcvCandleService:
    def __init__(self, client: DynamoDBClient | None = None) -> None:
        self._db = client or DynamoDBClient()

    def insert(
        self,
        symbol: str,
        interval: str,
        open_time: int,
        open_price: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: Decimal,
    ) -> str:
        for name, value in (
            ("open_price", open_price),
            ("high", high),
            ("low", low),
            ("close", close),
            ("volume", volume),
        ):
            if value < 0:
                raise ValueError(f"{name} must be >= 0")
        item = {
            "id": {"S": generate_id()},
            "symbol": {"S": symbol},
            "interval": {"S": interval},
            "open_time": {"N": str(open_time)},
            "open_price": {"N": str(open_price)},
            "high": {"N": str(high)},
            "low": {"N": str(low)},
            "close": {"N": str(close)},
            "volume": {"N": str(volume)},
        }
        return self._db.put_item(TABLE_OHLCV, item)

    def get_by_symbol_interval(self, symbol: str, interval: str) -> list[dict]:
        resp = self._db._client.query(
            TableName=TABLE_OHLCV,
            IndexName="symbol_interval_index",
            KeyConditionExpression="#s = :s AND #i = :i",
            ExpressionAttributeNames={"#s": "symbol", "#i": "interval"},
            ExpressionAttributeValues={":s": {"S": symbol}, ":i": {"S": interval}},
        )
        return resp.get("Items", [])

    def get_by_symbol_time_range(
        self, symbol: str, from_ms: int, to_ms: int
    ) -> list[dict]:
        resp = self._db._client.query(
            TableName=TABLE_OHLCV,
            IndexName="symbol_time_index",
            KeyConditionExpression="#s = :s AND #t BETWEEN :from AND :to",
            ExpressionAttributeNames={"#s": "symbol", "#t": "open_time"},
            ExpressionAttributeValues={
                ":s": {"S": symbol},
                ":from": {"N": str(from_ms)},
                ":to": {"N": str(to_ms)},
            },
        )
        return resp.get("Items", [])


class PositionService:
    def __init__(self, client: DynamoDBClient | None = None) -> None:
        self._db = client or DynamoDBClient()

    def insert(
        self,
        email: str,
        pool_address: str,
        token0: str,
        token1: str,
        liquidity: Decimal,
        balance: Decimal,
    ) -> str:
        for name, value in (("liquidity", liquidity), ("balance", balance)):
            if value < 0:
                raise ValueError(f"{name} must be >= 0")
        user_id = resolve_user_id_by_email(email)
        ts = now_ms()
        item = {
            "id": {"S": generate_id()},
            "user_id": {"S": user_id},
            "pool_address": {"S": pool_address},
            "token0": {"S": token0},
            "token1": {"S": token1},
            "liquidity": {"N": str(liquidity)},
            "balance": {"N": str(balance)},
            "created_at": {"N": str(ts)},
            "updated_at": {"N": str(ts)},
        }
        return self._db.put_item(TABLE_POSITIONS, item)

    def get_by_user(self, user_id: str) -> list[dict]:
        return self._db.query_index(TABLE_POSITIONS, "user_index", "user_id", user_id)

    def get_by_email(self, email: str) -> list[dict]:
        user_id = resolve_user_id_by_email(email)
        return self.get_by_user(user_id)

    def get_by_pool(self, pool_address: str) -> list[dict]:
        return self._db.query_index(
            TABLE_POSITIONS, "pool_index", "pool_address", pool_address
        )


class UserService:
    VALID_STATUSES: ClassVar[set[str]] = {"ACTIVE", "INACTIVE", "BLOCKED"}

    def __init__(self, client: DynamoDBClient | None = None) -> None:
        self._db = client or DynamoDBClient()

    def _resolve_by_user_id(self, user_id: str) -> dict | None:
        items = self._db.query_index(TABLE_USERS, "user_id_index", "user_id", user_id)
        return items[0] if items else None

    def create(
        self,
        wallet_address: str,
        email: str,
        full_name: str,
        password_hash: str,
        status: str = "ACTIVE",
    ) -> str:
        user_id = wallet_address.strip().lower()
        if not user_id:
            raise ValueError("wallet_address cannot be empty")
        if not email or not email.strip():
            raise ValueError("email cannot be empty")
        if not password_hash:
            raise ValueError("password_hash cannot be empty")
        if status not in self.VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(self.VALID_STATUSES)}")
        if self._resolve_by_user_id(user_id):
            raise ValueError("user already exists for this wallet_address")
        if self.get_by_email(email):
            raise ValueError("email already registered")
        ts = now_ms()
        item = {
            "id": {"S": generate_id()},
            "user_id": {"S": user_id},
            "wallet_address": {"S": user_id},
            "email": {"S": email.strip().lower()},
            "full_name": {"S": full_name},
            "password_hash": {"S": password_hash},
            "status": {"S": status},
            "created_at": {"N": str(ts)},
            "updated_at": {"N": str(ts)},
        }
        return self._db.put_item(TABLE_USERS, item)

    def get_by_user_id(self, user_id: str) -> dict | None:
        return self._resolve_by_user_id(user_id)

    def get_by_email(self, email: str) -> dict | None:
        items = self._db.query_index(
            TABLE_USERS, "email_index", "email", email.strip().lower()
        )
        return items[0] if items else None

    def resolve_user_id(self, email: str) -> str:
        return resolve_user_id_by_email(email)

    def update_status(self, email: str, status: str) -> None:
        if status not in self.VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(self.VALID_STATUSES)}")
        user_id = resolve_user_id_by_email(email)
        item = self._resolve_by_user_id(user_id)
        if not item:
            raise ValueError("user not found")
        self._db.update_item(
            TABLE_USERS,
            key={"id": {"S": item["id"]["S"]}},
            update_expression="SET #s = :s, #u = :u",
            expr_names={"#s": "status", "#u": "updated_at"},
            expr_values={":s": {"S": status}, ":u": {"N": str(now_ms())}},
        )
