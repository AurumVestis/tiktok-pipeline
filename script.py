import asyncio
import json
import random
from TikTokApi import TikTokApi

# ========= CONFIG =========
TARGETS = [
    "breaking news",
    "viral news",
    "public interviews",
    "street reactions",
    "trending topics"
]

FOLLOWER_THRESHOLD = 10000
MAX_RESULTS = 30


# ========= CORE =========
async def fetch_users(api, keyword):
    results = []

    try:
        async for user in api.search.users(keyword, count=50):
            try:
                info = await user.info()

                stats = info.get("stats", {})
                user_data = info.get("user", {})

                followers = stats.get("followerCount", 0)
                username = user_data.get("uniqueId")

                if not username:
                    continue

                if followers >= FOLLOWER_THRESHOLD:
                    continue

                results.append({
                    "username": username,
                    "followers": followers
                })

                if len(results) >= MAX_RESULTS:
                    break

                # small delay to reduce blocking
                await asyncio.sleep(random.uniform(1, 2))

            except Exception:
                continue

    except Exception:
        return []

    return results


# ========= MAIN =========
async def main():
    all_results = []

    try:
        async with TikTokApi() as api:
            await api.create_sessions(
                num_sessions=1,
                sleep_after=3,
                browser="chromium"
            )

            for keyword in TARGETS:
                users = await fetch_users(api, keyword)
                all_results.extend(users)

                if len(all_results) >= MAX_RESULTS:
                    break

    except Exception as e:
        with open("results.json", "w") as f:
            json.dump({
                "status": "error",
                "message": str(e)
            }, f, indent=2)
        return

    # remove duplicates
    unique = {}
    for user in all_results:
        unique[user["username"]] = user

    final_results = list(unique.values())[:MAX_RESULTS]

    # fallback output (never empty file)
    if not final_results:
        final_results = [{
            "username": "no_results_found",
            "reason": "likely_environment_limited"
        }]

    with open("results.json", "w") as f:
        json.dump(final_results, f, indent=2)


# ========= RUN =========
if __name__ == "__main__":
    asyncio.run(main())