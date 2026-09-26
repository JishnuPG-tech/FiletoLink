"""Unit tests for apex_stream.tmdb_meta — parsing, matching & NFO builders."""

import pytest

from apex_stream.tmdb_meta import (
    best_tmdb_match,
    build_episode_nfo,
    build_movie_nfo,
    build_tvshow_nfo,
    parse_media_meta,
    tmdb_image_url,
)


class TestParseMediaMeta:
    def test_movie_basic(self):
        meta = parse_media_meta("SpiderMan Homecoming 2017 720p BluRay x264")
        assert meta["is_tv"] is False
        assert meta["year"] == 2017
        assert "2017" not in meta["clean_title"]
        assert meta["search_title"] == "spiderman homecoming"

    def test_movie_group_tag_stripped(self):
        meta = parse_media_meta("[WMR] Manjummel Boys 2023 Malayalam 1080p WEB-DL")
        assert meta["is_tv"] is False
        assert meta["year"] == 2023
        assert "malayalam" not in meta["search_title"]
        assert "wmr" not in meta["search_title"]

    def test_tv_sxe(self):
        meta = parse_media_meta("Breaking Bad S01E01 720p x264")
        assert meta["is_tv"] is True
        assert meta["show_name"] == "Breaking Bad"
        assert meta["season"] == 1
        assert meta["episode"] == 1
        assert meta["title"] == "Breaking Bad - S01E01"

    def test_tv_season_episode_words(self):
        meta = parse_media_meta("Game of Thrones Season 1 Episode 5")
        assert meta["is_tv"] is True
        assert meta["show_name"] == "Game Of Thrones"
        assert meta["season"] == 1
        assert meta["episode"] == 5

    def test_tv_1x02(self):
        meta = parse_media_meta("Some Show 3x09 PROPER")
        assert meta["is_tv"] is True
        assert meta["season"] == 3
        assert meta["episode"] == 9

    def test_tv_year_kept_for_query(self):
        meta = parse_media_meta("The Last of Us 2023 S01E02")
        assert meta["is_tv"] is True
        assert meta["year"] == 2023

    def test_empty_fallback(self):
        meta = parse_media_meta(None)
        assert meta["title"] == "Unknown_Media"
        assert meta["is_tv"] is False

    def test_handle_stripped(self):
        meta = parse_media_meta("@ApexStore Movie Title 2021")
        assert "apexstore" not in meta["search_title"]
        assert meta["year"] == 2021

    def test_dots_become_spaces(self):
        meta = parse_media_meta("Spider-Man.Far.From.Home.2021.1080p.WEB-DL")
        assert meta["is_tv"] is False
        assert meta["year"] == 2021
        assert meta["clean_title"] == "Spider-Man Far From Home"
        assert meta["search_title"] == "spider-man far from home"

    def test_dot_run_and_release_group(self):
        meta = parse_media_meta("Spider-Man.No.Way.Home. . . . -Tinymkv.Xyz (2021).mkv")
        assert meta["is_tv"] is False
        assert meta["year"] == 2021
        assert meta["clean_title"] == "Spider-Man No Way Home"
        assert meta["search_title"] == "spider-man no way home"

    def test_trailing_dash_group_stripped(self):
        meta = parse_media_meta("Spider-Man Far From Home -Pah")
        assert meta["clean_title"] == "Spider-Man Far From Home"
        assert meta["search_title"] == "spider-man far from home"

    def test_hyphenated_series_part_kept(self):
        meta = parse_media_meta("Mission Impossible - Dead Reckoning Part 1 2023")
        assert meta["year"] == 2023
        assert "dead reckoning" in meta["search_title"]

    def test_dotted_release_group_stripped(self):
        meta = parse_media_meta("Premam.2015.Malayalam.1080p.x264.Pah")
        assert meta["is_tv"] is False
        assert meta["year"] == 2015
        assert meta["search_title"] == "premam"
        assert meta["clean_title"] == "Premam"

    def test_dotted_group_after_bluray_anchor(self):
        meta = parse_media_meta("Inception.2010.1080p.BluRay.x264.DTS-WiKi")
        assert meta["search_title"] == "inception"
        assert "wiki" not in meta["search_title"]

    def test_short_stop_tokens_removed(self):
        meta = parse_media_meta("Njan.Gandharvan.2023.1080p.Malayalam.HQ")
        assert meta["search_title"] == "njan gandharvan"
        assert "hq" not in meta["search_title"]

    def test_numeric_only_title_recovered(self):
        meta = parse_media_meta("2018.2018.Malayalam.1080p")
        assert meta["is_tv"] is False
        assert meta["title"] == "2018"
        assert meta["search_title"] == "2018"
        assert meta["year"] == 2018

    def test_numeric_title_with_release_year(self):
        meta = parse_media_meta("1917.2019.1080p.x264")
        assert meta["is_tv"] is False
        assert meta["title"] == "1917"
        assert meta["search_title"] == "1917"

    def test_ott_brand_audio_tail_stripped(self):
        meta = parse_media_meta("I Nobody Jiohotstar Dd+5.1 H (2026).mkv")
        assert meta["is_tv"] is False
        assert meta["year"] == 2026
        assert meta["search_title"] == "i nobody"

    def test_ott_brand_with_glued_channel_count(self):
        meta = parse_media_meta("I Nobody Jiohotstar Dd5.1 H (2026).mkv")
        assert meta["search_title"] == "i nobody"
        assert "jiohotstar" not in meta["search_title"]
        assert "dd5" not in meta["search_title"]
        assert "h" not in meta["search_title"]

    def test_series_part_number_kept(self):
        meta = parse_media_meta("K.G.F.Chapter.2.2022.1080p.mkv")
        assert meta["year"] == 2022
        assert meta["search_title"] == "k g f chapter 2"

    def test_channel_marker_stripped(self):
        meta = parse_media_meta(
            "Obsession.2025.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA.mkv"
        )
        assert meta["is_tv"] is False
        assert meta["year"] == 2025
        assert meta["search_title"] == "obsession"
        assert "6ch" not in meta["search_title"]

    def test_channel_marker_lower_and_glued(self):
        meta = parse_media_meta("Thudakkam.2026.720p.WEB-DL.DD+5.1.5.1ch.mkv")
        assert meta["search_title"] == "thudakkam"
        assert "ch" not in meta["search_title"].split()

    def test_channel_marker_mid_run(self):
        meta = parse_media_meta("Movie.2024.1080p.6CH.HEVC.mkv")
        assert meta["search_title"] == "movie"

    def test_codec_ma_tail_stripped(self):
        meta = parse_media_meta("Interstellar (2014) 1080p DTS-MA Hindi.mkv")
        assert meta["year"] == 2014
        assert meta["search_title"] == "interstellar"

    def test_audio_channel_count_lang_stripped(self):
        meta = parse_media_meta("Vikram.2022.1080p.DDP5.1.Tamil.mkv")
        assert meta["year"] == 2022
        assert meta["search_title"] == "vikram"

    def test_ott_brand_malayalam_tail_stripped(self):
        meta = parse_media_meta("Bharath.Circus.2023.1080p.JioHotstar.DD+5.1.Malayalam.mkv")
        assert meta["year"] == 2023
        assert meta["search_title"] == "bharath circus"

    def test_ott_brand_short_isocode_tail_stripped(self):
        meta = parse_media_meta("Kaathal.The.Core.2023.1080p.Hotstar.Mal.mkv")
        assert meta["year"] == 2023
        assert meta["search_title"] == "kaathal the core"

    def test_webdl_audio_tail_stripped(self):
        meta = parse_media_meta("Manjummel.Boys.2024.720p.Hotstar.WEB-DL.x265.DDP5.1.Hindi.mkv")
        assert meta["year"] == 2024
        assert meta["search_title"] == "manjummel boys"

    def test_hdr_bit_audio_tail_stripped(self):
        meta = parse_media_meta("Deadpool.and.Wolverine.2024.1080p.JioHotstar.HDR.10bit.DD+.Mal.mkv")
        assert meta["year"] == 2024
        assert meta["search_title"] == "deadpool and wolverine"

    def test_search_candidates_present_and_ordered(self):
        meta = parse_media_meta("Bharath.Circus.2023.1080p.JioHotstar.DD+5.1.Malayalam.mkv")
        cands = meta["search_candidates"]
        assert cands
        assert cands[0] == "bharath circus"
        assert "bharath" in cands

    def test_search_candidates_fallback_no_pollution(self):
        meta = parse_media_meta("I Nobody Jiohotstar Dd+5.1 H (2026).mkv")
        assert "i nobody" in meta["search_candidates"]
        # Fragments ripped off release tokens must not become search queries.
        for cand in meta["search_candidates"]:
            for frag in (" dd", " h", " p", " ma", " jiohotstar"):
                assert frag not in cand


class TestBestTmdbMatch:
    def test_exact_film(self):
        results = [
            {"id": 1, "title": "Spider-Man: Homecoming", "release_date": "2017-07-07"},
            {"id": 2, "title": "Spider-Man", "release_date": "2002-05-03"},
            {"id": 3, "title": "The Amazing Spider-Man", "release_date": "2012-06-23"},
        ]
        hit = best_tmdb_match(results, "spiderman homecoming", "movie", 2017)
        assert hit is not None
        assert hit["id"] == 1

    def test_type_filter_excludes_wrong_media(self):
        results = [
            {"id": 1, "title": "Breaking Bad", "media_type": "tv", "first_air_date": "2008-01-20"},
        ]
        assert best_tmdb_match(results, "breaking bad", "movie") is None

    def test_no_match_returns_none(self):
        assert best_tmdb_match([{"id": 9, "title": "Avatar"}], "Interstellar", "movie") is None

    def test_year_boost(self):
        results = [
            {"id": 1, "title": "Dune Part Two", "release_date": "2024-02-27"},
            {"id": 2, "title": "Dune", "release_date": "2021-10-22"},
        ]
        hit = best_tmdb_match(results, "dune part two", "movie", 2024)
        assert hit["id"] == 1

    def test_empty_results(self):
        assert best_tmdb_match([], "Whatever", "movie") is None

    def test_numeric_title_matches(self):
        results = [
            {"id": 451048, "title": "2018", "release_date": "2023-05-05", "original_language": "ml"},
            {"id": 999, "title": "Player", "release_date": "2018-06-14"},
        ]
        hit = best_tmdb_match(results, "2018", "movie", 2018)
        assert hit is not None
        assert hit["id"] == 451048

    def test_expected_none_no_match(self):
        # A lone 4-digit token that matches nothing still returns None.
        assert best_tmdb_match(
            [{"id": 7, "title": "Dune", "release_date": "2021-10-22"}],
            "2099", "movie",
        ) is None


class TestNfoBuilders:
    def test_movie_nfo(self):
        data = {
            "id": 315635,
            "title": "Spider-Man: Homecoming",
            "original_title": "Spider-Man: Homecoming",
            "release_date": "2017-07-07",
            "vote_average": 7.3,
            "overview": "A young Peter Parker fights crime.",
            "genres": [{"name": "Action"}, {"name": "Adventure"}],
            "production_countries": [{"iso_3166_1": "US"}],
        }
        nfo = build_movie_nfo(data)
        assert "<movie>" in nfo
        assert "Spider-Man: Homecoming" in nfo
        assert "<uniqueid type=\"tmdb\">315635</uniqueid>" in nfo
        assert "<genre>Action</genre>" in nfo
        assert "<country>US</country>" in nfo
        assert "poster.jpg" in nfo

    def test_tvshow_nfo(self):
        data = {
            "id": 1396,
            "name": "Breaking Bad",
            "first_air_date": "2008-01-20",
            "vote_average": 8.9,
            "overview": "A high school chemistry teacher.",
            "genres": [{"name": "Drama"}, {"name": "Crime"}],
        }
        nfo = build_tvshow_nfo(data)
        assert "<tvshow>" in nfo
        assert "<uniqueid type=\"tmdb\">1396</uniqueid>" in nfo
        assert "<genre>Drama</genre>" in nfo

    def test_episode_nfo(self):
        data = {
            "id": 621961,
            "name": "Pilot",
            "overview": "Walt turns fifty.",
            "season_number": 1,
            "episode_number": 1,
            "air_date": "2008-01-20",
        }
        nfo = build_episode_nfo(data)
        assert "<episodedetails>" in nfo
        assert "<season>1</season>" in nfo
        assert "<episode>1</episode>" in nfo
        assert "<uniqueid type=\"tmdb\">621961</uniqueid>" in nfo

    def test_image_url(self):
        assert tmdb_image_url("/abc123.jpg") == "https://image.tmdb.org/t/p/w500/abc123.jpg"
        assert tmdb_image_url(None) is None