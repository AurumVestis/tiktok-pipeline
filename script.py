import asyncio
import json
import random
from datetime import datetime, timedelta
from TikTokApi import TikTokApi

# YOUR PROXY
PROXY = "http://zmhoeair-1:kkw665jgb491@p.webshare.io:80"

TARGETS = ["khaby.lame", "mrbeast"]

MAX_RESULTS = 20
FOLLOWER_THRESHOLD = 1000
DAYS_ACTIVE_THRESHOLD = 7


def score_user(followers, engagement):
    return (engagement * 0.6) + ((1 / (followers + 1)) * 0.4)


async def process_user(api, username):
    user = api.user(username=username)
    results = []

    try:
        async for video in user.videos(count=30):
            try:
                data = video.as_dict

                author = data.get("author", {})
                stats = data.get("stats", {})

                uname = author.get("uniqueId")
                followers = stats.get("followerCount", 0)
                likes = stats.get("diggCount", 0)

                if followers >= FOLLOWER_THRESHOLD:
                    continue

                create_time = data.get("createTime", 0)
                post_time = datetime.fromtimestamp(create_time)

                if datetime.now() - post_time > timedelta(days=DAYS_ACTIVE_THRESHOLD):
                    continue

                engagement = likes / (followers + 1)

                results.append({
                    "username": uname,
                    "followers": followers,
                    "likes": likes,
                    "engagement": engagement,
                    "score": score_user(followers, engagement)
                })

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
            browser="chromium",
            proxy=PROXY
        )

        all_results = []

        for target in TARGETS:
            res = await process_user(api, target)
            all_results.extend(res)

            await asyncio.sleep(random.uniform(4, 8))

        try:
            with open("results.json") as f:
                existing = {u["username"]: u for u in json.load(f)}
        except:
            existing = {}

        for user in all_results:
            if user["username"] not in existing:
                existing[user["username"]] = user

        final_list = sorted(
            existing.values(),
            key=lambda x: x["score"],
            reverse=True
        )[:MAX_RESULTS]

        with open("results.json", "w") as f:
            json.dump(final_list, f, indent=2)

        for u in final_list:
            print(u["username"], u["score"])


if __name__ == "__main__":
    asyncio.run(main())