import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_admin.jellyfin_client import JellyfinClient
from ai_admin.reconciler import (
    load_telegram_injected_catalog,
    audit_and_compare,
    reconcile_item,
    cleanup_rogue_and_duplicates,
    apply_artwork_from_url,
)


@pytest.fixture
def mock_jf_client():
    client = MagicMock(spec=JellyfinClient)
    client.get_all_library_items = AsyncMock()
    client.get_item = AsyncMock(return_value={"id": "item-123", "name": "Old Title", "path": "/data/jellyfin/media/Movies/Old.strm"})
    client.update_item_metadata = AsyncMock(return_value={"status": "ok"})
    client.set_item_image_bytes = AsyncMock(return_value=True)
    client.refresh_item = AsyncMock(return_value=True)
    client.refresh_library = AsyncMock(return_value=True)
    client.delete_item = AsyncMock(return_value=True)
    return client


def test_load_telegram_injected_catalog_nonexistent(tmp_path):
    res = load_telegram_injected_catalog(str(tmp_path / "nonexistent.json"))
    assert res == []


def test_load_telegram_injected_catalog_valid(tmp_path):
    cache_file = tmp_path / "file_ids.json"
    cache_data = {
        "-100123:456": {
            "chat_id": -100123,
            "message_id": 456,
            "file_name": "Khalifa.2026.1080p.mkv",
            "title": "Khalifa",
            "clean_title": "Khalifa",
            "year": 2026,
            "is_tv": False,
            "strm_path": "/data/jellyfin/media/Movies/Khalifa (2026)/Khalifa.strm",
            "tmdb_id": 1036081,
            "imdb_id": "tt22797990",
            "file_size": 1500000000,
            "poster_url": "https://images.metahub.space/poster/medium/tt22797990/img",
        }
    }
    cache_file.write_text(json.dumps(cache_data))

    catalog = load_telegram_injected_catalog(str(cache_file))
    assert len(catalog) == 1
    assert catalog[0]["title"] == "Khalifa"
    assert catalog[0]["tmdb_id"] == 1036081
    assert catalog[0]["strm_path"] == "/data/jellyfin/media/Movies/Khalifa (2026)/Khalifa.strm"


@pytest.mark.asyncio
async def test_audit_and_compare(mock_jf_client, tmp_path):
    cache_file = tmp_path / "file_ids.json"
    cache_data = {
        "-1001:1": {
            "chat_id": -1001,
            "message_id": 1,
            "file_name": "Inception.2010.mkv",
            "title": "Inception",
            "year": 2010,
            "is_tv": False,
            "strm_path": "/data/jellyfin/media/Movies/Inception (2010)/Inception.strm",
            "tmdb_id": 27205,
        }
    }
    cache_file.write_text(json.dumps(cache_data))

    # Mock Jellyfin returning:
    # 1. Matching movie (Inception) without poster
    # 2. Rogue movie (Random.strm)
    # 3. Duplicate series (Show A x2)
    mock_jf_client.get_all_library_items.return_value = [
        {
            "id": "item-1",
            "name": "Inception",
            "Type": "Movie",
            "path": "/data/jellyfin/media/Movies/Inception (2010)/Inception.strm",
            "has_poster": False,
            "provider_ids": {"Tmdb": "27205"},
        },
        {
            "id": "item-2",
            "name": "Rogue Movie",
            "Type": "Movie",
            "path": "/data/jellyfin/media/Movies/Rogue (2020)/Rogue.strm",
            "has_poster": True,
            "provider_ids": {},
        },
        {
            "id": "series-1",
            "name": "Dark",
            "Type": "Series",
            "path": "/data/jellyfin/media/TV Shows/Dark",
            "has_poster": True,
        },
        {
            "id": "series-2",
            "name": "Dark",
            "Type": "Series",
            "path": "/data/jellyfin/media/TV Shows/Dark Duplicate",
            "has_poster": True,
        },
    ]

    audit = await audit_and_compare(mock_jf_client, cache_path=str(cache_file))

    assert audit["total_telegram_injected"] == 1
    assert audit["total_jellyfin_items"] == 4
    assert audit["rogue_items_count"] == 1
    assert audit["rogue_items"][0]["id"] == "item-2"

    assert audit["duplicate_series_count"] == 1
    assert audit["duplicate_series"][0]["series_name"] == "Dark"
    assert audit["duplicate_series"][0]["count"] == 2

    assert audit["missing_artwork_count"] == 1
    assert audit["missing_artwork"][0]["id"] == "item-1"


@pytest.mark.asyncio
async def test_reconcile_item(mock_jf_client, tmp_path):
    cache_file = tmp_path / "file_ids.json"
    cache_data = {
        "-1001:1": {
            "title": "Old Title",
            "year": 2020,
            "tmdb_id": 100,
        }
    }
    cache_file.write_text(json.dumps(cache_data))

    res = await reconcile_item(
        mock_jf_client,
        item_id="item-123",
        title="Khalifa",
        year=2026,
        tmdb_id=1036081,
        imdb_id="tt22797990",
        cache_path=str(cache_file),
    )

    assert res["status"] == "reconciled"
    assert res["id"] == "item-123"
    assert res["title"] == "Khalifa"
    mock_jf_client.update_item_metadata.assert_called_once()
    mock_jf_client.refresh_item.assert_called_once_with("item-123", replace_all=True)

    # Check cache update
    updated_cache = json.loads(cache_file.read_text())
    entry = updated_cache["-1001:1"]
    assert entry["title"] == "Khalifa"
    assert entry["year"] == 2026
    assert entry["tmdb_id"] == 1036081
    assert entry["imdb_id"] == "tt22797990"


@pytest.mark.asyncio
async def test_cleanup_rogue_and_duplicates(mock_jf_client, tmp_path):
    cache_file = tmp_path / "file_ids.json"
    cache_file.write_text(json.dumps({}))

    mock_jf_client.get_all_library_items.return_value = [
        {
            "id": "rogue-1",
            "name": "Rogue",
            "Type": "Movie",
            "path": "/data/jellyfin/media/Movies/Rogue.strm",
            "has_poster": True,
        },
        {
            "id": "series-1",
            "name": "Breaking Bad",
            "Type": "Series",
            "path": "/data/jellyfin/media/TV Shows/Breaking Bad",
            "has_poster": True,
        },
        {
            "id": "series-2",
            "name": "Breaking Bad",
            "Type": "Series",
            "path": "/data/jellyfin/media/TV Shows/Breaking Bad (2)",
            "has_poster": True,
        },
    ]

    res = await cleanup_rogue_and_duplicates(
        mock_jf_client,
        remove_rogue=True,
        deduplicate_series=True,
        cache_path=str(cache_file),
    )

    assert res["status"] == "cleanup_complete"
    assert res["deleted_rogue_count"] == 1
    assert res["deleted_duplicate_series_count"] == 1

    # Verified delete calls
    deleted_ids = [call.args[0] for call in mock_jf_client.delete_item.call_args_list]
    assert "rogue-1" in deleted_ids
    assert "series-2" in deleted_ids
    assert "series-1" not in deleted_ids
    mock_jf_client.refresh_library.assert_called_once()


@pytest.mark.asyncio
async def test_apply_artwork_from_url_blocked_by_netguard(mock_jf_client):
    with pytest.raises(ValueError, match="Artwork URL rejected by NetGuard"):
        await apply_artwork_from_url(
            mock_jf_client,
            item_id="item-1",
            image_url="http://192.168.1.1/exploit.jpg",
        )
