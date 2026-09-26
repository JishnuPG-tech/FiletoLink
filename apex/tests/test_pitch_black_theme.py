import os
import xml.etree.ElementTree as ET
import pytest

def test_pitch_black_theme_exists_and_valid():
    theme_path = os.path.join(os.path.dirname(__file__), "..", "theme", "pitch-black.css")
    assert os.path.exists(theme_path), "pitch-black.css must exist"
    
    with open(theme_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Assert pure pitch black and red accent tokens
    assert "#000000" in content, "Must enforce pure pitch black background"
    assert "#e50914" in content.lower(), "Must use Netflix red accent"
    
    # Assert core components styled
    assert "#loginPage" in content, "Must style login page in pure black"
    assert "backgroundContainer" in content, "Must style background container"
    assert "itemProgressBarForeground" in content, "Must style playback progress bar"

def test_branding_xml_is_valid():
    xml_path = os.path.join(os.path.dirname(__file__), "..", "theme", "branding.xml")
    assert os.path.exists(xml_path), "branding.xml must exist"
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    assert root.tag == "BrandingOptions"
    custom_css = root.find("CustomCss")
    assert custom_css is not None
    assert "#000000" in (custom_css.text or "")
    assert "#e50914" in (custom_css.text or "").lower()
