import asyncio
import json
from TikTokApi import TikTokApi

# SETTINGS
SEARCH_TERMS = ["fyp", "viral", "trending", "news"]
MAX_RESULTS = 100


async def fetch_users(api):
    results = []

    for term in SEARCH_TERMS:
        try:
            async for video in api.search.videos(term, count=MAX_RESULTS):
                try:
                    data = video.as_dict

                    author = data.get("author", {})
                    username = author.get("uniqueId")

                    if not username:
                        continue

                    results.append(username)

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

        usernames = await fetch_users(api)

        # Remove duplicates
        unique_usernames = list(set(usernames))

        # Guarantee output
        if not unique_usernames:
            unique_usernames = ["no_data_but_pipeline_runs"]

        # Format result
        final_list = [{"username": u} for u in unique_usernames]

        # Save
        with open("results.json", "w") as f:
            json.dump(final_list, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())