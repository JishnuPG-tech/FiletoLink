import os
import pytest

# Ensure dummy test environment variables exist before importing Thunder modules
os.environ.setdefault("API_ID", "123456")
os.environ.setdefault("API_HASH", "abcdef1234567890abcdef1234567890")
os.environ.setdefault("BOT_TOKEN", "123456789:ABCDefghIJklmnOPqrstUVwxyz123456789")
os.environ.setdefault("BIN_CHANNEL", "-1001234567890")
os.environ.setdefault("DATABASE_URL", "mongodb://localhost:27017/test")
os.environ.setdefault("OWNER_ID", "987654321")

from Thunder.vars import parse_channel_target, Var
from Thunder.utils.commands import get_commands

def test_parse_channel_target():
    # Username with @
    assert parse_channel_target("@flashfilez") == "@flashfilez"
    
    # Username without @
    assert parse_channel_target("flashfilez") == "@flashfilez"
    
    # t.me link
    assert parse_channel_target("https://t.me/flashfilez") == "@flashfilez"
    assert parse_channel_target("t.me/flashfilez/") == "@flashfilez"
    
    # Negative channel ID
    assert parse_channel_target("-1001234567890") == -1001234567890
    
    # Positive channel ID requiring -100 prefix
    assert parse_channel_target("1234567890") == -1001234567890
    
    # Fallback to default
    assert parse_channel_target(None, default="@flashfilez") == "@flashfilez"
    assert parse_channel_target("", default="-1001234567890") == -1001234567890
    
    # Empty with no default
    assert parse_channel_target(None) is None
    assert parse_channel_target("") is None


def test_command_registration():
    commands = get_commands()
    cmd_map = {cmd.command: cmd.description for cmd in commands}
    
    assert "test_channel" in cmd_map
    assert "post_ott" in cmd_map
    assert "ott_status" in cmd_map
    assert "post_milestone" in cmd_map
    assert "preview_milestone" in cmd_map
    assert "status" in cmd_map
    assert "help" in cmd_map


def test_channel_defaults():
    # FORCE_CHANNEL_ID should never be None by default
    assert Var.FORCE_CHANNEL_ID is not None
    assert Var.OTT_CHANNEL_ID is not None
    assert Var.MILESTONE_CHANNEL_ID is not None
