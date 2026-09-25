import ast
from pathlib import Path

from apex_stream.organize import strm_base
from apex_stream.tmdb_meta import parse_media_meta


def test_generic_telegram_name_uses_caption():
    source = Path(__file__).resolve().parents[1] / "tg_streamer.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "media_file_name")
    ns = {"re": __import__("re")}
    exec(compile(ast.Module([node], []), "<ast>", "exec"), ns)

    class Media:
        file_name = "Telegram_Media_14.mp4"

    class Message:
        caption = "Spider-Man Homecoming 2017 1080p"

    assert ns["media_file_name"](Message(), Media()) == "Spider-Man Homecoming 2017 1080p"


def test_spiderman_metadata_has_stable_movie_identity():
    meta = parse_media_meta("Spider-Man Homecoming 2017 1080p BluRay x264")
    assert meta["search_title"] == "spider-man homecoming"
    assert strm_base(meta) == "Spider-Man Homecoming (2017)"
