import asyncio
import json
import random
from TikTokApi import TikTokApi

# ================= CONFIG =================
TARGETS = [
    "breaking news",
    "street interviews",
    "viral clips",
    "public reactions",
    "news commentary"
]

FOLLOWER_THRESHOLD = 5000
MAX_RESULTS = 20
MIN_RESULTS_BEFORE_FALLBACK = 5

# ================ CORE ===================

async def fetch_users(api, keyword):
    results = []

    try:
        videos = api.search.videos(keyword, count=30)

        async for video in videos:
            try:
                user = video.author
                stats = await user.stats()

                followers = stats.get("followerCount", 0)

                if followers >= FOLLOWER_THRESHOLD:
                    continue

                results.append({
                    "username": user.unique_id,
                    "followers": followers
                })

                if len(results) >= MAX_RESULTS:
                    break

            except Exception:
                continue

    except Exception:
        return []

    return results


async def fallback_strategy(api):
    fallback_results = []

    fallback_keywords = ["fyp", "trending", "viral", "funny"]

    for keyword in fallback_keywords:
        data = await fetch_users(api, keyword)
        fallback_results.extend(data)

        if len(fallback_results) >= MAX_RESULTS:
            break

    return fallback_results[:MAX_RESULTS]


async def main():
    all_results = []

    try:
        async with TikTokApi() as api:
            await api.create_sessions(
                num_sessions=1,
                sleep_after=3,
                browser="chromium"
            )

            # PRIMARY STRATEGY
            for keyword in TARGETS:
                users = await fetch_users(api, keyword)
                all_results.extend(users)

                if len(all_results) >= MAX_RESULTS:
                    break

            # FALLBACK IF TOO EMPTY
            if len(all_results) < MIN_RESULTS_BEFORE_FALLBACK:
                fallback_users = await fallback_strategy(api)
                all_results.extend(fallback_users)

    except Exception as e:
        with open("results.json", "w") as f:
            json.dump({
                "status": "error",
                "message": str(e)
            }, f, indent=2)
        return

    # REMOVE DUPLICATES
    unique = {}
    for user in all_results:
        unique[user["username"]] = user

    final_results = list(unique.values())[:MAX_RESULTS]

    # FINAL SAFETY OUTPUT
    if not final_results:
        output = [{
            "username": "no_results_found",
            "reason": "filters_too_strict_or_no_data"
        }]
    else:
        output = final_results

    with open("results.json", "w") as f:
        json.dump(output, f, indent=2)


# =============== RUN =====================
if __name__ == "__main__":
    asyncio.run(main())