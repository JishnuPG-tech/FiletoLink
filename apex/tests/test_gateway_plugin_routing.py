import pytest
import httpx
from starlette.datastructures import Headers
from unittest.mock import AsyncMock, patch

from gateway.main import app, route_catch_all

@pytest.mark.asyncio
async def test_skinmanager_and_plugin_routes_forward_to_jellyfin():
    with patch("gateway.main.proxy_http_request", new_callable=AsyncMock) as mock_proxy:
        # Mock Request for /api/SkinManager/Resource
        request = AsyncMock()
        request.url.path = "/api/SkinManager/Resource"
        request.headers = Headers({})
        
        await route_catch_all("api/SkinManager/Resource", request)
        
        assert mock_proxy.called
        call_args = mock_proxy.call_args[0]
        target_url = call_args[0]
        assert "8096" in target_url, f"Expected port 8096 for SkinManager, got {target_url}"
        assert "/api/SkinManager/Resource" in target_url

@pytest.mark.asyncio
async def test_inplayerpreview_route_forwards_to_jellyfin():
    with patch("gateway.main.proxy_http_request", new_callable=AsyncMock) as mock_proxy:
        request = AsyncMock()
        request.url.path = "/InPlayerPreview/ClientScript"
        request.headers = Headers({})
        
        await route_catch_all("InPlayerPreview/ClientScript", request)
        
        assert mock_proxy.called
        call_args = mock_proxy.call_args[0]
        target_url = call_args[0]
        assert "8096" in target_url, f"Expected port 8096 for InPlayerPreview, got {target_url}"
        assert "/InPlayerPreview/ClientScript" in target_url

@pytest.mark.asyncio
async def test_jellyfin_referer_forwards_to_jellyfin():
    with patch("gateway.main.proxy_http_request", new_callable=AsyncMock) as mock_proxy:
        request = AsyncMock()
        request.url.path = "/custom_theme_asset.css"
        request.headers = Headers({"referer": "https://jishnupg-filetolink.hf.space/jellyfin/web/#/home"})
        
        await route_catch_all("custom_theme_asset.css", request)
        
        assert mock_proxy.called
        call_args = mock_proxy.call_args[0]
        target_url = call_args[0]
        assert "8096" in target_url, f"Expected port 8096 when referer is Jellyfin, got {target_url}"

@pytest.mark.asyncio
async def test_filetolink_fallback_routes_correctly():
    with patch("gateway.main.proxy_http_request", new_callable=AsyncMock) as mock_proxy:
        request = AsyncMock()
        request.url.path = "/watch/f/abc12345/video.mp4"
        request.headers = Headers({})
        
        await route_catch_all("watch/f/abc12345/video.mp4", request)
        
        assert mock_proxy.called
        call_args = mock_proxy.call_args[0]
        target_url = call_args[0]
        assert "8081" in target_url, f"Expected port 8081 for FileToLink watch path, got {target_url}"

@pytest.mark.asyncio
async def test_ui_assets_route_to_jellyfin_web():
    with patch("gateway.main.proxy_http_request", new_callable=AsyncMock) as mock_proxy:
        request = AsyncMock()
        request.url.path = "/ui/spotlight.html"
        request.headers = Headers({})
        
        await route_catch_all("ui/spotlight.html", request)
        
        assert mock_proxy.called
        target_url = mock_proxy.call_args[0][0]
        assert "8096" in target_url
        assert "/web/ui/spotlight.html" in target_url

@pytest.mark.asyncio
async def test_jellyfin_ui_assets_rewrite_to_web():
    with patch("gateway.main.proxy_http_request", new_callable=AsyncMock) as mock_proxy:
        request = AsyncMock()
        request.url.path = "/jellyfin/ui/abyss.css"
        request.headers = Headers({})
        
        await route_catch_all("jellyfin/ui/abyss.css", request)
        
        assert mock_proxy.called
        target_url = mock_proxy.call_args[0][0]
        assert "8096" in target_url
        assert "/web/ui/abyss.css" in target_url


@pytest.mark.asyncio
async def test_keepalive_endpoints():
    from gateway.main import keepalive_ping
    resp = await keepalive_ping()
    assert resp.status_code == 200
    import json
    data = json.loads(resp.body.decode("utf-8"))
    assert data["status"] == "ok"
    assert data["alive"] is True


@pytest.mark.asyncio
async def test_playbackinfo_directplay_override():
    import json
    from unittest.mock import MagicMock
    from gateway.utils import proxy_http_request

    # Mock response with MediaSources having SupportsDirectPlay=False
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = httpx.Headers({"content-type": "application/json"})
    payload = {
        "MediaSources": [
            {
                "Id": "item1",
                "Path": "/data/media/Movies/Spider-Man.strm",
                "SupportsDirectPlay": False,
                "SupportsDirectStream": False,
            }
        ]
    }
    mock_resp.aread = AsyncMock(return_value=json.dumps(payload).encode("utf-8"))
    mock_resp.aclose = AsyncMock()

    mock_client = MagicMock()
    mock_client.build_request.return_value = MagicMock()
    mock_client.send = AsyncMock(return_value=mock_resp)

    with patch("gateway.utils.get_http_client", return_value=mock_client):
        from starlette.datastructures import QueryParams
        req = AsyncMock()
        req.url.path = "/jellyfin/Items/123/PlaybackInfo"
        req.headers = Headers({"accept": "application/json"})
        req.method = "POST"
        req.body = AsyncMock(return_value=b"{}")
        req.query_params = QueryParams([])

        result = await proxy_http_request("http://127.0.0.1:8096/Items/123/PlaybackInfo", req)
        assert result.status_code == 200
        out_data = json.loads(result.body.decode("utf-8"))
        src = out_data["MediaSources"][0]
        assert src["SupportsDirectPlay"] is True
        assert src["SupportsDirectStream"] is True
