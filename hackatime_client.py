import aiohttp


HACKATIME_TODAY_URL = "https://hackatime.hackclub.com/api/hackatime/v1/users/current/statusbar/today"

async def fetch_today_coding_data(api_key: str) -> dict:
    """
    Queries Hack Club's Hackatime API for today's coding telemetry.
    Returns a standardized dictionary with status, total_seconds, and projects.
    """
    if not api_key or len(api_key.strip()) < 5:
        return {"ok": False, "error": "Missing or invalid API key format."}

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Accept": "application/json"
    }

    timeout_cfg = aiohttp.ClientTimeout(total=8)

    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        try:
            async with session.get(HACKATIME_TODAY_URL, headers=headers) as response:
                if response.status == 200:
                    payload = await response.json()
                    raw_data = payload.get("data", {})
                    grand_total = raw_data.get("grand_total", {})
                    projects_list = raw_data.get("projects", [])
                    languages_list = raw_data.get("languages", [])

                    return {
                        "ok": True,
                        "total_seconds": int(grand_total.get("total_seconds", 0)),
                        "human_readable": grand_total.get("text", "0 mins"),
                        "projects": projects_list,
                        "languages": languages_list
                    }
                elif response.status == 401 or response.status == 403:
                    return {
                        "ok": False,
                        "error": "Unauthorized! Your Hackatime API key was rejected. Check hackatime.hackclub.com/settings."
                    }
                else:
                    return {
                        "ok": False,
                        "error": f"Hackatime server returned HTTP {response.status}."
                    }
        except Exception as err:
            return {
                "ok": False,
                "error": f"Network error connecting to Hackatime: {str(err)}"
            }

def find_project_in_today_log(projects_list: list, target_project_name: str) -> dict:
    """
    Uses Python's native for...else construct to search for a specific project
    in today's Hackatime heartbeat payload without using boolean flag variables.
    """
    clean_target = target_project_name.strip().lower()

    for proj in projects_list:
        current_name = str(proj.get("name", "")).lower()
        if clean_target in current_name:
            found_result = {
                "found": True,
                "name": proj.get("name", "Unknown"),
                "seconds": int(proj.get("total_seconds", 0)),
                "text": proj.get("text", "0 mins")
            }
            break
    else:
        # Runs ONLY if the loop completes without finding a matching project
        found_result = {
            "found": False,
            "name": target_project_name,
            "seconds": 0,
            "text": "0 mins"
        }

    return found_result