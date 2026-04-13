import asyncio
import json
import random
from datetime import datetime, timedelta
from TikTokApi import TikTokApi

TARGETS = [
    "cnn",
    "bbcnews",
    "foxnews",
    "aljazeeraenglish"
]

MAX_RESULTS = 20
FOLLOWER_THRESHOLD = 100000
DAYS_ACTIVE_THRESHOLD = 120


def score_user(followers, engagement):
    return (engagement * 0.6) + (1 / (followers + 1))


async def process_user(api, username):
    user = api.user(username=username)
    results = []

    try:
        async for video in user.videos(count=100):
            try:
                data = video.as_dict

                author = data.get("author", {})
                stats = data.get("stats", {})

                uname = author.get("uniqueId")
                followers = author.get("followerCount", 0)
                likes = stats.get("diggCount", 0)

                if followers >= FOLLOWER_THRESHOLD:
                    continue

                ts = data.get("createTime")
                if not ts:
                    continue

                post_time = datetime.fromtimestamp(ts)
                if datetime.now() - post_time > timedelta(days=DAYS_ACTIVE_THRESHOLD):
                    continue

                engagement = likes / (followers + 1)
                score = score_user(followers, engagement)

                results.append({
                    "username": uname,
                    "followers": followers,
                    "likes": likes,
                    "score": score
                })

                if len(results) >= MAX_RESULTS:
                    break

            except:
                continue

    except:
        pass

    return results


async def main():
    async with TikTokApi() as api:
        await api.create_sessions(
            num_sessions=1,
            headless=True,
            browser="chromium"
        )

        all_results = []

        for target in TARGETS:
            res = await process_user(api, target)
            all_results.extend(res)
            await asyncio.sleep(random.uniform(4, 8))

        try:
            with open("results.json", "r") as f:
                existing_list = json.load(f)
                existing = {u["username"]: u for u in existing_list}
        except:
            existing = {}

        for user in all_results:
            existing[user["username"]] = user

        final_list = sorted(existing.values(), key=lambda x: x["score"], reverse=True)

        with open("results.json", "w") as f:
            json.dump(final_list, f, indent=2)

        print(f"Done. Saved {len(final_list)} users.")


if __name__ == "__main__":
    asyncio.run(main())