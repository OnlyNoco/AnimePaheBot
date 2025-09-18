import requests
from datetime import datetime

# Genre to emoji mapping
GENRE_EMOJIS = {
    "Adventure": "🪂",
    "Fantasy": "🧞",
    "Romance": "💞",
    "Action": "⚔️",
    "Comedy": "😂",
    "Drama": "🎭",
    "Sci-Fi": "👽",
    "Mystery": "🕵️",
    "Slice of Life": "🌸",
    "Horror": "👻",
    "Sports": "🏅",
    # add more as needed
}

def get_anilist_info(title: str):
    url = "https://graphql.anilist.co"
    query = """
    query ($search: String) {
      Media(search: $search, type: ANIME) {
        id
        title { romaji english }
        season
        status
        averageScore
        episodes
        duration
        startDate { year month day }
        endDate { year month day }
        nextAiringEpisode { episode airingAt }
        studios { nodes { name } }
        genres
        description(asHtml: false)
      }
    }
    """
    variables = {"search": title}
    response = requests.post(url, json={"query": query, "variables": variables}).json()
    media = response.get("data", {}).get("Media")
    if not media:
        return None

    anime_id = media["id"]
    anime_cover_url = f"https://img.anili.st/media/{anime_id}"
    anime_title_eng = media["title"].get("english") or media["title"].get("romaji")
    season = media.get("season") or "Season 1"
    
    # Next episode release UTC
    next_ep_info = media.get("nextAiringEpisode")
    if next_ep_info:
        next_episode = next_ep_info["episode"]
        next_release_utc = datetime.utcfromtimestamp(next_ep_info["airingAt"])
    else:
        next_episode = None
        next_release_utc = None

    studios = [studio["name"] for studio in media.get("studios", {}).get("nodes", [])]
    genres = media.get("genres", [])
    genres_with_emoji = [f"{GENRE_EMOJIS.get(g, '')} #{g}" for g in genres]
    
    description = media.get("description", "")
    # Shorten synopsis if >1000 chars
    if len(description) > 1000:
        description = description[:997] + "..."
    
    start_date = media.get("startDate")
    end_date = media.get("endDate")
    def format_date(d):
        if not d: return "Unknown"
        return f"{d['year']}-{d['month']:02}-{d['day']:02}"
    
    return {
        "anime_cover_url": anime_cover_url,
        "anime_title_eng": anime_title_eng,
        "season": season,
        "status": media.get("status"),
        "averageScore": media.get("averageScore"),
        "episodes": media.get("episodes"),
        "duration": media.get("duration"),
        "first_aired": format_date(start_date),
        "last_aired": format_date(end_date),
        "next_episode": next_episode,
        "next_release_utc": next_release_utc,
        "studios": studios,
        "genres": genres_with_emoji,
        "description": description
    }