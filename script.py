import asyncio
import json
from datetime import datetime, timedelta, timezone
from TikTokApi import TikTokApi

TARGETS = ["username1", "username2"]  # replace later

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
                author = video.as_dict.get("author", {})
                stats = video.as_dict.get("authorStats", {})

                uname = author.get("uniqueId", "")
                followers = stats.get("followerCount", 0)
                likes = stats.get("heartCount", 0)

                if followers >= FOLLOWER_THRESHOLD:
                    continue

                ts = video.as_dict.get("createTime", 0)
                post_time = datetime.fromtimestamp(ts, tz=timezone.utc)

                if post_time < datetime.now(timezone.utc) - timedelta(days=DAYS_ACTIVE_THRESHOLD):
                    continue

                engagement = likes / followers if followers else 0

                results.append({
                    "username": uname,
                    "followers": followers,
                    "likes": likes,
                    "engagement": engagement,
                    "score": score_user(followers, engagement)
                })

            except:
                continue

    except Exception as e:
        print(f"Error processing {username}: {e}")

    return results

    async for u in user.following(count=200):
        try:
            info = await u.info()
            stats = info["userInfo"]["stats"]
            user_data = info["userInfo"]["user"]

            followers = stats.get("followerCount", 0)
            likes = stats.get("heartCount", 0)
            uname = user_data.get("uniqueId", "")

            if followers >= FOLLOWER_THRESHOLD:
                continue

            active = False
            async for vid in u.videos(count=1):
                ts = vid.as_dict.get("createTime", 0)
                post_time = datetime.fromtimestamp(ts, tz=timezone.utc)

                if post_time >= datetime.now(timezone.utc) - timedelta(days=DAYS_ACTIVE_THRESHOLD):
                    active = True

            if not active:
                continue

            engagement = likes / followers if followers else 0

            results.append({
                "username": uname,
                "followers": followers,
                "likes": likes,
                "engagement": engagement,
                "score": score_user(followers, engagement)
            })

        except:
            continue

    return results


async def main():
    async with TikTokApi() as api:
        await api.create_sessions()

        all_results = []

        for target in TARGETS:
            res = await process_user(api, target)
            all_results.extend(res)

        # LOAD OLD DATA
        try:
            with open("results.json") as f:
                existing = {u["username"]: u for u in json.load(f)}
        except:
            existing = {}

        # MERGE
        for user in all_results:
            if user["username"] not in existing or user["score"] > existing[user["username"]]["score"]:
                existing[user["username"]] = user

        final_list = sorted(existing.values(), key=lambda x: x["score"], reverse=True)

        # SAVE
        with open("results.json", "w") as f:
            json.dump(final_list, f)

        # PRINT TOP
        for u in final_list[:MAX_RESULTS]:
            print(u["username"])


if __name__ == "__main__":
    asyncio.run(main())
