#!/usr/bin/env python3
import os
import re
import sys
import json
import urllib.request
import urllib.parse

TVMAZE_CACHE = {}

def clean_series_name(name: str) -> str:
    s = re.sub(r'\(\d{4}\)', '', name)
    s = re.sub(r'[^\w\s]', ' ', s)
    return ' '.join(s.split()).strip()

def fetch_tvmaze_episodes(series_name: str) -> dict:
    q = clean_series_name(series_name)
    if not q:
        return {}
    if q in TVMAZE_CACHE:
        return TVMAZE_CACHE[q]
    
    encoded = urllib.parse.quote_plus(q)
    url = f"https://api.tvmaze.com/singlesearch/shows?q={encoded}&embed=episodes"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                episodes = {}
                for ep in data.get("_embedded", {}).get("episodes", []):
                    s_num = ep.get("season")
                    e_num = ep.get("number")
                    ep_name = ep.get("name")
                    if s_num and e_num and ep_name:
                        episodes[(int(s_num), int(e_num))] = ep_name
                TVMAZE_CACHE[q] = episodes
                return episodes
    except Exception as e:
        print(f"[TVMAZE] Error fetching episodes for '{series_name}' ({q}): {e}")
    
    TVMAZE_CACHE[q] = {}
    return {}

def heal_episodes_via_api(base_url="https://jishnupg-filetolink.hf.space", username="root", password="Jishnu2005"):
    print(f"[HEAL-API] Authenticating with Jellyfin at {base_url}...")
    auth_url = f"{base_url}/jellyfin/Users/AuthenticateByName"
    auth_data = json.dumps({"Username": username, "Pw": password}).encode("utf-8")
    req = urllib.request.Request(
        auth_url,
        data=auth_data,
        headers={
            "Authorization": 'MediaBrowser Client="Jellyfin Web", Device="CloudScript", DeviceId="heal-script", Version="10.8.13"',
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            auth_res = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[HEAL-API] Auth failed: {e}")
        return False

    token = auth_res["AccessToken"]
    user_id = auth_res["User"]["Id"]
    auth_hdr = f'MediaBrowser Client="Jellyfin Web", Device="CloudScript", DeviceId="heal-script", Version="10.8.13", Token="{token}"'

    shows_url = f"{base_url}/jellyfin/Users/{user_id}/Items?IncludeItemTypes=Series&Recursive=true"
    req = urllib.request.Request(shows_url, headers={"Authorization": auth_hdr})
    with urllib.request.urlopen(req, timeout=10) as resp:
        shows = json.loads(resp.read().decode("utf-8")).get("Items", [])

    print(f"[HEAL-API] {len(shows)} Series found.")
    total_healed = 0

    for show in shows:
        show_id = show["Id"]
        show_name = show["Name"]
        episodes_map = fetch_tvmaze_episodes(show_name)
        if not episodes_map:
            print(f"[HEAL-API] No guide for show: {show_name}")
            continue

        eps_url = f"{base_url}/jellyfin/Shows/{show_id}/Episodes?UserId={user_id}"
        req = urllib.request.Request(eps_url, headers={"Authorization": auth_hdr})
        with urllib.request.urlopen(req, timeout=10) as resp:
            episodes = json.loads(resp.read().decode("utf-8")).get("Items", [])

        for ep in episodes:
            cur_name = ep.get("Name", "")
            s_num = ep.get("ParentIndexNumber") or 1
            e_num = ep.get("IndexNumber")
            if not e_num:
                m = re.search(r'S(\d+)E(\d+)', cur_name, re.I)
                if m:
                    s_num = int(m.group(1))
                    e_num = int(m.group(2))

            if s_num and e_num and (int(s_num), int(e_num)) in episodes_map:
                real = episodes_map[(int(s_num), int(e_num))]
                if cur_name != real:
                    ep_id = ep["Id"]
                    det_url = f"{base_url}/jellyfin/Users/{user_id}/Items/{ep_id}"
                    req = urllib.request.Request(det_url, headers={"Authorization": auth_hdr})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        full = json.loads(resp.read().decode("utf-8"))
                    full["Name"] = real
                    full["IndexNumber"] = int(e_num)
                    full["ParentIndexNumber"] = int(s_num)
                    upd_url = f"{base_url}/jellyfin/Items/{ep_id}"
                    up_req = urllib.request.Request(
                        upd_url,
                        data=json.dumps(full).encode("utf-8"),
                        headers={"Authorization": auth_hdr, "Content-Type": "application/json"},
                        method="POST"
                    )
                    with urllib.request.urlopen(up_req, timeout=10) as up_resp:
                        pass
                    print(f'  Healed {show_name} S{s_num:02d}E{e_num:02d}: "{cur_name}" -> "{real}"')
                    total_healed += 1

    print(f"[HEAL-API] Healed {total_healed} episode(s).")
    return True

if __name__ == "__main__":
    heal_episodes_via_api()
