from apex_stream.media_catalog import EpisodeIdentity, MediaCatalog, MediaJob, MediaRecord


def test_initializes_wal_schema_and_round_trips_by_both_keys(tmp_path):
    path = tmp_path / "catalog.sqlite"
    with MediaCatalog(path) as catalog:
        assert catalog.connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        record = catalog.upsert(
            source_chat_id=-1001,
            source_message_id=42,
            canonical_key="movie:example",
            file_name="example.mkv",
            size_bytes=123,
        )
        assert record == catalog.find_by_source(-1001, 42)
        assert record == catalog.find_by_canonical_key("movie:example")
        assert catalog.list_records() == [record]


def test_upsert_preserves_state_and_explicit_record_can_set_state(tmp_path):
    with MediaCatalog(tmp_path / "catalog.sqlite") as catalog:
        catalog.upsert(source_chat_id=1, source_message_id=2, canonical_key="a")
        assert catalog.mark_published(canonical_key="a")
        catalog.upsert(source_chat_id=1, source_message_id=2, canonical_key="a", file_id="new")
        assert catalog.find_by_canonical_key("a").published is True
        catalog.upsert(MediaRecord(1, 2, "a", file_id="new", published=False))
        assert catalog.find_by_canonical_key("a").published is False


def test_delete_unpublish_and_filtered_listing(tmp_path):
    with MediaCatalog(tmp_path / "catalog.sqlite") as catalog:
        catalog.upsert(source_chat_id=1, source_message_id=1, canonical_key="one", published=True)
        catalog.upsert(source_chat_id=1, source_message_id=2, canonical_key="two", published=True)
        assert catalog.mark_deleted(source_chat_id=1, source_message_id=1)
        assert catalog.unpublish(canonical_key="two")
        assert catalog.list_records(published_only=True) == []
        assert len(catalog.list_records()) == 1
        assert len(catalog.list_records(include_deleted=True)) == 2
        assert catalog.find_by_source(1, 1).deleted is True


def test_reopens_and_versions_duplicate_canonical_keys(tmp_path):
    path = tmp_path / "catalog.sqlite"
    with MediaCatalog(path) as catalog:
        catalog.upsert(source_chat_id=1, source_message_id=1, canonical_key="one")
        catalog.upsert(source_chat_id=1, source_message_id=1, canonical_key="one-renamed")
        variant = catalog.upsert(source_chat_id=2, source_message_id=2, canonical_key="one-renamed")
        assert variant.canonical_key == "one-renamed:variant-2-2"
    with MediaCatalog(path) as reopened:
        assert reopened.find_by_source(1, 1).canonical_key == "one-renamed"


def test_review_jobs_are_idempotent_and_keep_retry_state(tmp_path):
    path = tmp_path / "catalog.sqlite"
    with MediaCatalog(path) as catalog:
        job = catalog.upsert_job(
            source_chat_id=-1001,
            source_message_id=42,
            canonical_key="movie:unknown",
            status="review",
            confidence=0.2,
            last_error="unidentified_or_low_confidence",
            payload={"file_name": "Telegram_Media_42"},
        )
        assert job == catalog.find_job(-1001, 42)
        assert catalog.list_jobs() == [job]

        updated = catalog.upsert_job(MediaJob(
            source_chat_id=-1001,
            source_message_id=42,
            canonical_key="movie:example:2024:english",
            status="retry",
            confidence=0.8,
            retry_count=1,
            payload={"file_name": "Example.2024.mkv"},
        ))
        assert updated.id == job.id
        assert catalog.update_job(-1001, 42, status="published", retry_count=2)
        assert catalog.list_jobs(statuses=("published",))[0].retry_count == 2


def test_episode_identities_round_trip_and_report_completeness(tmp_path):
    with MediaCatalog(tmp_path / "catalog.sqlite") as catalog:
        first = catalog.record_episode(
            show_canonical_key="show:example", season=1, episode=1,
            title="Pilot", air_date="2024-01-01", runtime_minutes=40,
            source_chat_id=10, source_message_id=1, source_file_id="file-1",
        )
        catalog.record_episode(
            EpisodeIdentity("show:example", 1, 1, "Pilot duplicate",
                            source_chat_id=11, source_message_id=2)
        )
        catalog.record_episode(
            show_canonical_key="show:example", season=1, episode=3,
            source_chat_id=10, source_message_id=3,
        )
        assert first.runtime_minutes == 40
        assert len(catalog.list_episodes(canonical_key="show:example")) == 3
        report = catalog.report_episode_completeness(
            "show:example", season=1, expected=range(1, 4)
        )
        assert report["missing"] == [{"season": 1, "episode": 2}]
        assert [(item["season"], item["episode"]) for item in report["duplicates"]] == [(1, 1)]


def test_episode_schema_migrates_existing_catalog(tmp_path):
    path = tmp_path / "catalog.sqlite"
    with MediaCatalog(path) as catalog:
        catalog.connection.execute("PRAGMA user_version = 1")
    with MediaCatalog(path) as catalog:
        assert catalog.connection.execute("PRAGMA user_version").fetchone()[0] == 2
        catalog.record_episode(
            canonical_key="show:old", season=0, episode=1,
            source_chat_id=1, source_message_id=1,
        )
