import pytest
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
