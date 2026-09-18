"""MongoDB persistence with one reused client for the long-running API."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

_client: MongoClient[dict[str, Any]] | None = None


class MongoUnavailableError(RuntimeError):
    """The configured MongoDB instance cannot currently serve requests."""


def _database():
    global _client
    uri = os.getenv("MONGODB_URI")
    if not uri:
        return None
    if _client is None:
        _client = MongoClient(
            uri,
            maxPoolSize=10,
            minPoolSize=0,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
        )
    return _client[os.getenv("MONGODB_DATABASE", "traceguard")]


def _users() -> Collection[dict[str, Any]] | None:
    database = _database()
    return database["users"] if database is not None else None


def upsert_user(profile: dict[str, Any]) -> dict[str, Any]:
    collection = _users()
    now = datetime.now(timezone.utc)
    profile = {**profile, "updated_at": now}
    if collection is None:
        return profile
    collection.update_one(
        {"firebase_uid": profile["firebase_uid"]},
        {"$set": profile, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    return profile


def get_user(firebase_uid: str) -> dict[str, Any] | None:
    collection = _users()
    if collection is None:
        return None
    return collection.find_one({"firebase_uid": firebase_uid}, {"_id": 0})


def save_scan(scan: dict[str, Any], firebase_uid: str) -> None:
    database = _database()
    if database is None:
        return
    scans = database["scans"]
    try:
        scans.update_one(
            {"scan_id": scan["scan_id"], "firebase_uid": firebase_uid},
            {
                "$set": {
                    **scan,
                    "firebase_uid": firebase_uid,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
    except PyMongoError as error:
        raise MongoUnavailableError("MongoDB is configured but unavailable") from error


def list_scans(firebase_uid: str) -> list[dict[str, Any]]:
    database = _database()
    if database is None:
        return []
    try:
        return list(database["scans"].find({"firebase_uid": firebase_uid}, {"_id": 0}).sort("started_at", -1))
    except PyMongoError as error:
        raise MongoUnavailableError("MongoDB is configured but unavailable") from error


def get_scan(scan_id: str, firebase_uid: str) -> dict[str, Any] | None:
    database = _database()
    if database is None:
        return None
    try:
        return database["scans"].find_one({"scan_id": scan_id, "firebase_uid": firebase_uid}, {"_id": 0})
    except PyMongoError as error:
        raise MongoUnavailableError("MongoDB is configured but unavailable") from error


def list_findings(firebase_uid: str) -> list[dict[str, Any]]:
    database = _database()
    if database is None:
        return []
    records: list[dict[str, Any]] = []
    try:
        for scan in database["scans"].find({"firebase_uid": firebase_uid}, {"_id": 0}):
            for finding in scan.get("report", {}).get("findings", []):
                records.append(
                    {
                        "finding": finding,
                        "repository": scan.get("repository_url", ""),
                        "branch": scan.get("branch", "main"),
                        "scan_id": scan.get("scan_id", ""),
                        "detected_at": scan.get("started_at"),
                    }
                )
    except PyMongoError as error:
        raise MongoUnavailableError("MongoDB is configured but unavailable") from error
    return records
