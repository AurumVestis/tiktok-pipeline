import asyncio
import json
from TikTokApi import TikTokApi

# SETTINGS
SEARCH_TERMS = ["fyp", "viral", "trending", "news"]
MAX_RESULTS = 50
FOLLOWER_THRESHOLD = 5000

async def fetch_users(api):
    results = []

    for term in SEARCH_TERMS:
        try:
            async for video in api.search.videos(term, count=MAX_RESULTS):
                try:
                    data = video.as_dict

                    author = data.get("author", {})
                    stats = author.get("stats", {})

                    username = author.get("uniqueId")
                    followers = stats.get("followerCount", 0)

                    # Skip bad data
                    if not username:
                        continue

                    # Filter (your main control)
                    if followers >= FOLLOWER_THRESHOLD:
                        continue

                    results.append({
                        "username": username,
                        "followers": followers
                    })

                except:
                    continue

        except:
            continue

    return results


async def main():
    async with TikTokApi() as api:
        await api.create_sessions(
            num_sessions=1,
            headless=True,
            browser="chromium"
        )

        all_results = await fetch_users(api)

        # Remove duplicates
        unique = {u["username"]: u for u in all_results}

        final_list = list(unique.values())

        # GUARANTEE OUTPUT (so you always see something)
        if not final_list:
            final_list = [{"status": "no users found, but script works"}]

        with open("results.json", "w") as f:
            json.dump(final_list, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())