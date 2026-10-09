# AI authored file
import hashlib
import json
import time
from typing import NamedTuple

from valkey.exceptions import ResponseError, ConnectionError, TimeoutError
from valkey.commands.search.field import TagField
from valkey.commands.search.indexDefinition import IndexDefinition, IndexType

from .database import vk

VERSIONS_KEY = "quorra:index-versions"
LOCK_KEY = "quorra:index-lock"

class IndexSpec(NamedTuple):
    name: str
    path: str
    alias: str
    prefixes: list[str]


# Populated by Transaction subclasses as they are defined
INDEXES: dict[str, IndexSpec] = {}


def register_index(prefix, alias, path):
    name = f"idx:{prefix}:{alias}"
    INDEXES[name] = IndexSpec(name, path, alias, [f"{prefix}:"])
    return name


def _fingerprint(name, path, alias, prefixes):
    blob = json.dumps([name, path, alias, "TAG", "JSON", prefixes])
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _is_missing_index_error(e):
    msg = str(e).lower()
    return "no such index" in msg or "unknown index" in msg or "not found" in msg


def _is_already_exists_error(e):
    return "already exists" in str(e).lower()


def _index_exists(name):
    try:
        vk.ft(name).info()
        return True
    except ResponseError as e:
        if _is_missing_index_error(e):
            return False
        raise


def _create(name, path, alias, prefixes):
    try:
        vk.ft(name).create_index(
            (TagField(path, as_name=alias),),
            definition=IndexDefinition(prefix=prefixes, index_type=IndexType.JSON),
        )
    except ResponseError as e:
        if not _is_already_exists_error(e):
            raise


def _ensure_one(name, path, alias, prefixes):
    fp = _fingerprint(name, path, alias, prefixes)
    exists = _index_exists(name)
    if exists and vk.hget(VERSIONS_KEY, name) == fp:
        return
    if exists:
        print(f"Index {name} definition changed, rebuilding (documents are kept)")
        try:
            vk.ft(name).dropindex(delete_documents=False)
        except ResponseError as e:
            if not _is_missing_index_error(e):
                raise
    else:
        print(f"Creating index {name}")
    _create(name, path, alias, prefixes)
    vk.hset(VERSIONS_KEY, name, fp)


def _drop_stale():
    stale = set(vk.hkeys(VERSIONS_KEY)) - set(INDEXES)
    for name in stale:
        try:
            vk.ft(name).dropindex(delete_documents=False)
            print(f"Dropped stale index {name}")
        except ResponseError as e:
            if not _is_missing_index_error(e):
                raise
        vk.hdel(VERSIONS_KEY, name)


def ensure_indexes():
    """Idempotently create/rebuild all indexes. Safe to call from multiple workers."""
    # The lock only prevents workers from dropping each other's fresh index
    got_lock = vk.set(LOCK_KEY, "1", nx=True, ex=30)
    if not got_lock:
        # Another worker is on it; wait for it to finish
        for _ in range(60):
            if not vk.exists(LOCK_KEY):
                break
            time.sleep(0.5)
        return
    try:
        for spec in INDEXES.values():
            _ensure_one(*spec)
        _drop_stale()
    finally:
        vk.delete(LOCK_KEY)


def ensure_indexes_with_retry(attempts=30, delay=1.0):
    """For startup: wait for Valkey to become reachable."""
    for i in range(attempts):
        try:
            ensure_indexes()
            return
        except (ConnectionError, TimeoutError):
            if i == attempts - 1:
                raise
            print("Valkey not reachable, retrying...")
            time.sleep(delay)


def search(index_name, query):
    """FT.SEARCH that recovers if the index vanished (e.g. Valkey restarted empty)."""
    try:
        return vk.ft(index_name).search(query)
    except ResponseError as e:
        if not _is_missing_index_error(e):
            raise
        ensure_indexes()
        return vk.ft(index_name).search(query)
