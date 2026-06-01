import instaloader

print("Initializing Instaloader...")
# Using a clean instance without login credentials first
L = instaloader.Instaloader(
    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
)

shortcode = "DZDCiMrCu3y"
print(f"Fetching post metadata for shortcode: {shortcode} ...")

try:
    # 1. Fetch the Reel (Post)
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    
    print("\n✅ --- REEL RESULTS ---")
    print(f"Creator Username: @{post.owner_username}")
    print(f"Likes: {post.likes}")
    print(f"Comments: {post.comments}")
    print(f"Views: {post.video_view_count}")
    print(f"Duration: {post.video_duration} seconds")
    print(f"Caption: {post.caption[:50]}...")
    
    # 2. Fetch the Creator's Profile using the username we just got
    print(f"\nFetching Profile metadata for @{post.owner_username} ...")
    profile = instaloader.Profile.from_username(L.context, post.owner_username)
    
    print("\n✅ --- PROFILE RESULTS ---")
    print(f"Followers: {profile.followers}")
    print(f"Following: {profile.followees}")
    print(f"Total Posts: {profile.mediacount}")

except Exception as e:
    print(f"\n❌ Instaloader failed with error: {e}")
    print("If you see a '403 Forbidden' or 'JSON Query to graphql', Instagram is still actively blocking your IP.")