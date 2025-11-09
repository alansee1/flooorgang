"""
Twitter Poster
Handles posting graphics to @FlooorGang Twitter account
"""

import tweepy
import os
from dotenv import load_dotenv

load_dotenv()


class TwitterPoster:
    """Handles authentication and posting to Twitter"""

    def __init__(self):
        """Initialize Twitter API client with OAuth 1.0a credentials"""
        # Load credentials from environment
        api_key = os.getenv('TWITTER_API_KEY')
        api_secret = os.getenv('TWITTER_API_SECRET')
        access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

        # Validate credentials
        if not all([api_key, api_secret, access_token, access_token_secret]):
            raise ValueError(
                "Missing Twitter API credentials. Check your .env file for:\n"
                "TWITTER_API_KEY, TWITTER_API_SECRET, "
                "TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET"
            )

        # Authenticate with Twitter API v1.1 (for media upload)
        auth = tweepy.OAuth1UserHandler(
            api_key, api_secret,
            access_token, access_token_secret
        )
        self.api = tweepy.API(auth)

        # Also create v2 client for posting tweets
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )

    def post_with_image(self, text, image_path):
        """
        Post a tweet with an image

        Args:
            text: Tweet text (max 280 characters)
            image_path: Path to image file to attach

        Returns:
            Tweet ID if successful, None if failed
        """
        try:
            # Upload media using v1.1 API
            print(f"📤 Uploading image: {image_path}")
            media = self.api.media_upload(filename=image_path)
            media_id = media.media_id

            # Post tweet with media using v2 API
            print(f"🐦 Posting tweet: {text[:50]}...")
            response = self.client.create_tweet(
                text=text,
                media_ids=[media_id]
            )

            tweet_id = response.data['id']
            tweet_url = f"https://twitter.com/FlooorGang/status/{tweet_id}"

            print(f"✅ Tweet posted successfully!")
            print(f"🔗 {tweet_url}")

            return tweet_id

        except tweepy.TweepyException as e:
            print(f"❌ Error posting to Twitter: {e}")
            return None

    def verify_credentials(self):
        """
        Verify that Twitter API credentials are working

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            user = self.api.verify_credentials()
            print(f"✅ Authenticated as @{user.screen_name}")
            print(f"   Followers: {user.followers_count:,}")
            return True
        except tweepy.TweepyException as e:
            print(f"❌ Authentication failed: {e}")
            return False


def main():
    """Test Twitter API connection"""
    print("\n🐦 Testing Twitter API Connection\n")
    print("=" * 60)

    try:
        poster = TwitterPoster()

        # Verify credentials
        if poster.verify_credentials():
            print("\n✅ Twitter API is configured correctly!")
            print("   Ready to post automated picks to @FlooorGang")
        else:
            print("\n❌ Twitter API authentication failed")
            print("   Please check your credentials in .env")

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")

    print("=" * 60)


if __name__ == "__main__":
    main()
