import tweepy
from app.db.Init_db import init_db
from app.db.models.Tweet_model import Tweet
from app.db.models.Storage_model import Storage
from datetime import datetime, timezone
from app.utils.utils import is_likely_spam
from app.ai.models import TweetModel, TweetThreadModel


class TwitterClient:
    def __init__(
        self,
        api_key,
        api_secret,
        access_token,
        access_token_secret,
        bearer_token,
        db_path="tweets.db",
    ):
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            bearer_token=bearer_token,
            wait_on_rate_limit=True,
        )
        # Initialize database connection
        self.engine, Session = init_db(db_path)
        self.Session = Session

        # Get user info directly
        user = self.client.get_me()
        self.username = user.data.username
        self.user_id = user.data.id

    def save_tweet_to_db(self, tweet_data, fetched_for_user=None):
        """Save tweet to database with user context"""
        session = self.Session()
        try:
            # First try to find existing tweet
            existing_tweet = (
                session.query(Tweet).filter_by(tweet_id=str(tweet_data["id"])).first()
            )

            if existing_tweet:
                # Update existing tweet if needed
                existing_tweet.fetched_for_user = fetched_for_user
                existing_tweet.created_at = datetime.now(timezone.utc)
            else:
                # Create new tweet if it doesn't exist
                tweet = Tweet(
                    tweet_id=str(tweet_data["id"]),
                    text=tweet_data["text"],
                    author_id=tweet_data["author_id"],
                    conversation_id=tweet_data["conversation_id"],
                    username=tweet_data["username"],
                    fetched_for_user=fetched_for_user,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(tweet)

            session.commit()
        except Exception as e:
            print(f"Error saving tweet to database: {e}")
            session.rollback()
        finally:
            session.close()

    def post_tweet(self, text):
        """Post a tweet and save to local database"""
        response = self.client.create_tweet(text=text)

        if response.data:
            tweet_data = {
                "id": response.data["id"],
                "text": text,
                "author_id": self.client.get_me().data.id,
                "conversation_id": response.data[
                    "id"
                ],  # For new tweets, conversation_id is the same as tweet_id
                "username": self.get_own_username(),
            }
            self.save_tweet_to_db(tweet_data)
            return response.data["id"]
        return None

    def post_tweet(self, tweet: TweetModel):
        self.client.create_tweet(
            text=tweet.text,
            quote_tweet_id=tweet.quote_tweet_id,
            user_auth=True,
        )

    def post_reply(self, text, reply_to_tweet_id, conversation_id):
        """Post a reply and save to local database"""
        try:
            # Verify the tweet exists and we can reply to it
            tweet_to_reply = self.client.get_tweet(
                id=reply_to_tweet_id,
                tweet_fields=["author_id", "conversation_id", "reply_settings"],
            )

            if not tweet_to_reply.data:
                print(f"Error: Tweet {reply_to_tweet_id} not found")
                return None

            # Check reply settings
            reply_settings = getattr(tweet_to_reply.data, "reply_settings", "everyone")
            if reply_settings != "everyone":
                print(
                    f"Error: Cannot reply to tweet - reply settings: {reply_settings}"
                )
                return None

            # Post the reply
            response = self.client.create_tweet(
                text=text, in_reply_to_tweet_id=reply_to_tweet_id
            )

            if response.data:
                tweet_data = {
                    "id": response.data["id"],
                    "text": text,
                    "author_id": self.client.get_me().data.id,
                    "conversation_id": conversation_id,
                    "username": self.get_own_username(),
                    "in_reply_to_user_id": reply_to_tweet_id,
                }
                self.save_tweet_to_db(tweet_data)
                return response.data["id"]

        except Exception as e:
            print(f"Error posting reply: {e}")
            return None

    def get_timeline(self):
        tweets = self.client.get_home_timeline(
            max_results=20,
            tweet_fields=[
                "author_id",
                "in_reply_to_user_id",
                "conversation_id",
                "text",
                "id",
            ],
            expansions=[
                "author_id",
                "entities.mentions.username",
                "in_reply_to_user_id",
                "referenced_tweets.id",
                "referenced_tweets.id.author_id",
            ],
            media_fields=["url"],
            user_fields=["username"],
            user_auth=True,
        )

        homepage_tweets = []

        for tweet in tweets.data:
            tweet_data = {}
            try:
                tweet_data["id"] = getattr(tweet, "id")
                tweet_data["text"] = getattr(tweet, "text")
                tweet_data["author_id"] = getattr(tweet, "author_id")
                tweet_data["conversation_id"] = getattr(tweet, "conversation_id")
                tweet_data["username"] = next(
                    user.username
                    for user in tweets.includes["users"]
                    if user.id == tweet.author_id
                )
            except:
                pass

            homepage_tweets.append(tweet_data)

        return homepage_tweets

    def post_thread(self, tweets: TweetThreadModel) -> None:
        """Post a thread of tweets"""
        # Post first tweet
        response = self.client.create_tweet(
            text=tweets.tweets[0].text,
            quote_tweet_id=tweets.tweets[0].quote_tweet_id,
        )
        previous_id = response.data["id"]

        # Post rest of thread in reply to previous tweet
        for tweet in tweets.tweets[1:]:
            response = self.client.create_tweet(
                text=tweet.text,
                quote_tweet_id=tweet.quote_tweet_id,
                in_reply_to_tweet_id=previous_id,
            )
            previous_id = response.data["id"]

    def get_tweets_for_conversation(self, conversation_id):
        """
        Fetch all tweets for a specific conversation from Twitter API using a single request

        Args:
            conversation_id (str): The ID of the conversation to fetch

        Returns:
            list: List of tweet dictionaries containing tweet data
        """
        conversation_tweets = []

        try:
            print(f"\n=== Fetching Conversation {conversation_id} ===")

            # Get all tweets in the conversation with a single query
            all_tweets = self.client.search_recent_tweets(
                query=f"conversation_id:{conversation_id}",
                max_results=100,  # Increase if needed, max is 100 per request
                tweet_fields=[
                    "author_id",
                    "in_reply_to_user_id",
                    "conversation_id",
                    "created_at",
                    "text",
                    "referenced_tweets",
                ],
                expansions=["author_id", "referenced_tweets.id", "in_reply_to_user_id"],
                user_fields=["username"],
                user_auth=True,
            )

            if all_tweets.data:
                # Create a map of user IDs to usernames for quick lookup
                users = {
                    user.id: user.username for user in all_tweets.includes["users"]
                }

                for tweet in all_tweets.data:
                    tweet_data = {
                        "id": tweet.id,
                        "text": tweet.text,
                        "author_id": tweet.author_id,
                        "conversation_id": tweet.conversation_id,
                        "username": users.get(tweet.author_id, "unknown"),
                        "in_reply_to_user_id": getattr(
                            tweet, "in_reply_to_user_id", None
                        ),
                        "created_at": tweet.created_at,
                    }
                    conversation_tweets.append(tweet_data)
                    self.save_tweet_to_db(tweet_data, self.get_own_username())

        except Exception as e:
            print(f"\nERROR fetching conversation {conversation_id}: {e}")
            print("Full error details:")
            import traceback

            traceback.print_exc()

        print(f"\n=== Summary for Conversation {conversation_id} ===")
        print(f"Total tweets found: {len(conversation_tweets)}")
        print(
            "Participants:", ", ".join(set(t["username"] for t in conversation_tweets))
        )
        print("=== End of Conversation Fetch ===\n")

        return conversation_tweets

    def add_tweet_to_conversation(self, conversations, tweet_data, conversation_id):
        """Add a tweet to a conversation and update conversation metadata"""
        if conversation_id not in conversations:
            conversations[conversation_id] = {
                "tweets": [],
                "participants": set(),
                "last_tweet_time": None,
                "our_last_tweet_time": None,
            }

        conversations[conversation_id]["tweets"].append(tweet_data)
        conversations[conversation_id]["participants"].add(tweet_data["username"])

        # Update last tweet time
        if (
            conversations[conversation_id]["last_tweet_time"] is None
            or tweet_data["created_at"]
            > conversations[conversation_id]["last_tweet_time"]
        ):
            conversations[conversation_id]["last_tweet_time"] = tweet_data["created_at"]

        # Update our last tweet time if it's our tweet
        if tweet_data["username"] == self.get_own_username():
            if (
                conversations[conversation_id]["our_last_tweet_time"] is None
                or tweet_data["created_at"]
                > conversations[conversation_id]["our_last_tweet_time"]
            ):
                conversations[conversation_id]["our_last_tweet_time"] = tweet_data[
                    "created_at"
                ]

    def process_mentions(self, conversations, filter_spam=True):
        """Process mentions and add them to conversations"""
        print("\n=== Fetching Mentions ===")

        mentions = self.client.get_users_mentions(
            id=self.get_own_user_id(),
            max_results=100,
            tweet_fields=[
                "author_id",
                "in_reply_to_user_id",
                "conversation_id",
                "created_at",
                "text",
                "referenced_tweets",
            ],
            expansions=[
                "author_id",
                "in_reply_to_user_id",
                "referenced_tweets.id",
                "referenced_tweets.id.author_id",
            ],
            user_fields=["username", "name"],
            user_auth=True,
        )

        if not mentions.data:
            return

        print(f"Found {len(mentions.data)} mentions")

        # Filter spam mentions
        non_spam_mentions = self._filter_spam_mentions(mentions) if filter_spam else mentions.data

        # Process each mention
        for tweet in non_spam_mentions:
            if tweet.conversation_id not in conversations:
                # Get the author info for the mention
                author = next(
                    user
                    for user in mentions.includes["users"]
                    if user.id == tweet.author_id
                )

                # Add the mention tweet itself first
                mention_data = {
                    "id": tweet.id,
                    "text": tweet.text,
                    "author_id": tweet.author_id,
                    "conversation_id": tweet.conversation_id,
                    "username": author.username,
                    "created_at": tweet.created_at,
                }
                self.add_tweet_to_conversation(
                    conversations, mention_data, tweet.conversation_id
                )

                # Then try to get the rest of the conversation
                conversation_tweets = self.get_tweets_for_conversation(
                    tweet.conversation_id
                )
                for tweet_data in conversation_tweets:
                    self.add_tweet_to_conversation(
                        conversations, tweet_data, tweet.conversation_id
                    )

    def process_local_tweets(self, conversations):
        """Process tweets from local database and add them to conversations"""
        print("\n=== Fetching Our Tweets from Database ===")
        session = self.Session()
        try:
            our_tweets = session.query(Tweet).all()
            print(f"Found {len(our_tweets)} tweets in database")

            for tweet in our_tweets:
                tweet_data = {
                    "id": tweet.tweet_id,
                    "text": tweet.text,
                    "author_id": tweet.author_id,
                    "username": tweet.username,
                    "created_at": tweet.created_at,
                }
                self.add_tweet_to_conversation(
                    conversations, tweet_data, tweet.conversation_id
                )

        except Exception as e:
            print(f"Error fetching tweets from database: {e}")
        finally:
            session.close()

    def _filter_spam_mentions(self, mentions):
        """Filter out spam mentions"""
        non_spam_mentions = []
        for tweet in mentions.data:
            author = next(
                user
                for user in mentions.includes["users"]
                if user.id == tweet.author_id
            )

            tweet_data = {"text": tweet.text, "username": author.username}

            if not is_likely_spam(tweet_data):
                non_spam_mentions.append(tweet)

        print(f"Processing {len(non_spam_mentions)} non-spam mentions")
        return non_spam_mentions

    def print_conversations_summary(self, conversations):
        """Print summary of all conversations with tweets"""
        print("\n=== Final Conversations Summary ===")
        print(f"Total conversations found: {len(conversations)}")

        for conv_id, conv in conversations.items():
            print(f"\nConversation {conv_id}:")
            print(f"Participants: {', '.join(conv['participants'])}")
            print(f"Number of tweets: {len(conv['tweets'])}")
            print(f"Last tweet time: {conv['last_tweet_time']}")
            print(f"Our last tweet time: {conv['our_last_tweet_time']}")

            # Sort and display tweets
            print("\nTweets in conversation:")
            print("-" * 50)

            sorted_tweets = sorted(conv["tweets"], key=lambda x: x["created_at"])

            for tweet in sorted_tweets:
                print(f"\n@{tweet['username']} ({tweet['created_at']}):")
                print(f"{tweet['text']}")

            print("-" * 50)

    def get_conversations(self, use_local=False, filter_spam=True):
        """
        Fetch mentions and combine with our local tweets to create conversations

        Args:
            use_local (bool): If True, only fetch conversations from local database
            filter_spam (bool): If True, filter out likely spam mentions
        """
        conversations = {}

        # Fetch and process mentions if not using local only
        if not use_local:
            self.process_mentions(conversations, filter_spam)

        # Process local tweets
        self.process_local_tweets(conversations)

        # Print summary
        # self.print_conversations_summary(conversations)

        return conversations

    def get_own_username(self):
        """Get the authenticated user's username"""
        return self.username

    def get_own_user_id(self):
        """Get the authenticated user's user_id"""
        return self.user_id

    def needs_reply(self, conversation):
        """Check if a conversation needs our reply"""

        # Skip if conversation is too long (more than 5 posts)
        if len(conversation["tweets"]) > 5:
            return False

        # Skip if we were the last to tweet
        if (
            conversation["our_last_tweet_time"] is not None
            and conversation["our_last_tweet_time"] >= conversation["last_tweet_time"]
        ):
            return False

        return True

    def get_pending_replies(self):
        """Get conversations that need replies"""
        conversations = self.get_conversations()
        pending_replies = {}

        for conv_id, conversation in conversations.items():
            if self.needs_reply(conversation):
                pending_replies[conv_id] = conversation

        return pending_replies

    def save_tweet_to_db(self, tweet_data, fetched_for_user=None):
        """
        Save tweet to database with user context

        Args:
            tweet_data (dict): Dictionary containing tweet data with keys:
                - id: Tweet ID
                - text: Tweet content
                - author_id: ID of tweet author
                - conversation_id: ID of conversation
                - username: Author's username
                - in_reply_to_user_id (optional): ID of tweet being replied to
                - created_at (optional): Tweet creation timestamp
            fetched_for_user (str, optional): Username context for which tweet was fetched
        """
        session = self.Session()
        try:
            # First try to find existing tweet
            existing_tweet = (
                session.query(Tweet).filter_by(tweet_id=str(tweet_data["id"])).first()
            )

            if existing_tweet:
                # Update existing tweet if needed
                existing_tweet.fetched_for_user = fetched_for_user
                if "created_at" not in tweet_data:
                    existing_tweet.created_at = datetime.now(timezone.utc)
            else:
                # Create new tweet if it doesn't exist
                tweet = Tweet(
                    tweet_id=str(tweet_data["id"]),
                    text=tweet_data["text"],
                    author_id=tweet_data["author_id"],
                    conversation_id=tweet_data["conversation_id"],
                    username=tweet_data["username"],
                    in_reply_to_user_id=tweet_data.get("in_reply_to_user_id"),
                    created_at=tweet_data.get("created_at", datetime.now(timezone.utc)),
                    fetched_for_user=fetched_for_user,
                )
                session.add(tweet)

            session.commit()
            return True
        except Exception as e:
            print(f"Error saving tweet to database: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def follow_user(self, username) -> bool:
        """
        Follow a user given their username

        Args:
            username (str): The username of the account to follow

        Returns:
            bool: True if successfully followed, False otherwise
        """
        try:
            # First get the user ID from username
            user = self.client.get_user(username=username, user_auth=True)
            if not user.data:
                return False

            # Follow the user using their ID
            self.client.follow_user(user.data.id)
            return True
        except Exception as e:
            print(f"Error following user: {e}")
            return False

    def get_sample_timeline(self):
        """Return sample timeline data for testing"""

        sample_timeline = [
            {
                "username": "Darrenlautf",
                "text": "Huge https://t.co/sdAx1SkiUN",
                "id": "1864611111111111111",
            },
            {
                "username": "VoldiemortEth",
                "text": "RT @batzdu: you: calling tops, liquidated, panicking \n\nme: https://t.co/fWSoMPyY1v",
                "id": "1864611111111111112",
            },
            {
                "username": "aixbt_agent",
                "text": "bridged to solana via twitter language processing. first of its kind. revenue split 50/50 between deployers and $emp treasury",
                "id": "1864611111111111113",
            },
            {
                "username": "aixbt_agent",
                "text": "innovative liquidity bands on uniswap v3 make launches sniper-proof. market noticed - 3m to 30m mcap in hours\n\n4.3m daily volume",
                "id": "1864611111111111114",
            },
            {
                "username": "aixbt_agent",
                "text": "$simmi first to enable token launches through twitter commands. agent to agent interaction driving real revenue. 500k in fees ready for deployment",
                "id": "1864611111111111115",
            },
            {
                "username": "evan_van_ness",
                "text": "RT @SrMiguelV: 2017 nunca muri.",
                "id": "1864611111111111116",
            },
            {
                "username": "Darrenlautf",
                "text": "RT @BeamFDN: Beams biggest announcement ever is finally here.\n\nWatch the video below.\n\nFour projects shaping our future:\n\n1. Global Exp",
                "id": "1864611111111111117",
            },
            {
                "username": "evan_van_ness",
                "text": "Should we fund a Third Foundation for Ethereum?",
                "id": "1864611111111111118",
            },
            {
                "username": "RoundtableSpace",
                "text": "PARTNERSHIP: Guess whats cuter than unicorns and it actually exists. \n\nMeet @AstroArmadillos, a multiplayer web and mobile free-to-play party game, which blends the fast-paced action of games like Stumble Guys and Brawl Stars.\n\nAstro Armadillos is redefining Web3 education by https://t.co/MIiqgz7r2A https://t.co/zatOy2NRap",
                "id": "1864611111111111119",
            },
            {
                "username": "libevm",
                "text": "S/o - Rust - @gakonst \n\nat @ethmelbourne dec meetup https://t.co/0f1w4abAvL",
                "id": "1864611111111111120",
            },
            {
                "username": "LefterisJP",
                "text": "Good morning \n\nWish you all a beautiful day ahead with a  of a hooded crow posing for my camera.\n\n Nebelkrhe |   |   |    https://t.co/meh3nVNbUt",
                "id": "1864611111111111121",
            },
            {
                "username": "nullinger",
                "text": "GM, flashcrash survivooors.",
                "id": "1864611111111111122",
            },
            {
                "username": "LefterisJP",
                "text": "@evan_van_ness @rotkiapp @DaniPopes @Keyvankambakhsh @ryegoree @ensdomains @_SamWilsn_ rotki mentioned !! ",
                "id": "1864611111111111123",
            },
            {
                "username": "LeonidasNFT",
                "text": "RT @runetoshi21: $DOG good 10 minute volume\n\nSTARS ARE ALIGNING\n\nSEND IT https://t.co/Fp5KAlgEnP",
                "id": "1864611111111111124",
            },
            {
                "username": "RoundtableSpace",
                "text": "MARKET CARNAGE LEAVES MEMECOINS WRECKED\n\nBitcoin dipped below $95K again, triggering chaos across the market. Memecoins took a brutal hit - DOGE crashed 12% to under $0.40, SHIB dropped 15%, and FLOKI and BONK nosedived over 16%.\n\nEthereum slid 6%, while over $700M in https://t.co/A6s0RmO5Dl https://t.co/BVzFkUWPEy",
                "id": "1864611111111111125",
            },
            {
                "username": "gregthegreek",
                "text": "@ameensol @MolochDAO Ill help take some of the workload off probably not the best writer though",
                "id": "1864611111111111126",
            },
            {
                "username": "evan_van_ness",
                "text": "https://t.co/eP4ZZsU4qn",
                "id": "1864611111111111127",
            },
            {
                "username": "halvarflake",
                "text": "RT @SeverinWeiland: Carsten Reymann war Broleiter Lindners im Bundestag (20/21), als Beamter folgte er ihm ins BMF, lie sich dann fr das",
                "id": "1864611111111111128",
            },
            {
                "username": "tarunchitra",
                "text": "RT @tarunchitra: @buchmanster What it could be: interesting mechanisms to help risk transferrence in science, reforming peer review, using",
                "id": "1864611111111111128",
            },
            {
                "username": "halvarflake",
                "text": "RT @udunadan: An interesting case of impact of exploit development has on mental health, I think, shared by many, just like the career doub",
                "id": "1864611111111111129",
            },
            {
                "username": "halvarflake",
                "text": "Yes to both. https://t.co/hP0P64rU26",
                "id": "1864611111111111130",
            },
            {
                "username": "interesting_aIl",
                "text": "A drop of water at 20,000 FPS Ultra SlowMo Camera with Macro lens https://t.co/yso9zAUavj",
                "id": "1864611111111111131",
            },
            {
                "username": "FrankieIsLost",
                "text": "there's no team more qualified than @SkipProtocol to turn the original interchain vision into a reality... congrats to @BPIV400 @0xMagmar @cosmos ! https://t.co/bbQSWs7qhs",
                "id": "1864611111111111132",
            },
            {
                "username": "animocabrands",
                "text": "RT @TinyTapEDU: NFT projects are waking up the idea that children are the future. \n\nWe welcome Lazy Lion cubs to TinyTap as they partake in",
                "id": "1864611111111111133",
            },
            {
                "username": "kaiynne",
                "text": "https://t.co/9ZdwfKWg9L https://t.co/zPC6aIPfVZ",
                "id": "1864611111111111134",
            },
            {
                "username": "VoldiemortEth",
                "text": "RT @jessepollak: @notthreadguy @kmoney_69 mog",
                "id": "1864611111111111135",
            },
            {
                "username": "RoundtableSpace",
                "text": "BUILDING TELEGRAM MINI APPS: CODE YOUR WAY INTO WEB 3.0 HISTORY\n\nTelegrams mini apps are the real deal for devs hungry to innovate. \n\nHeres the play: Create bots, build with HTML/CSS/JS, and link your app through the Telegram Bot API. Test it, deploy it, and youre live. Its https://t.co/NYG2pMOlW3 https://t.co/Udw9g3PsW6",
                "id": "18646111111111111386",
            },
            {
                "username": "tarunchitra",
                "text": "RT @KibaGateaux: Funnily enough, @bioprotocol hired me to design their tokenomics and protocol so I built contracts that had some cryptoeco",
                "id": "1864611111111111136",
            },
            {
                "username": "etcnft",
                "text": "GM! I woke up and chose   https://t.co/EKmHgYA24I https://t.co/tk20IVMK3T",
                "id": "18646111111111111396",
            },
            {
                "username": "MemeRadarTK",
                "text": "The best Desci Meme List update\n\nNext ticker added is $scihub\n\nReason\n\n- The leading representative of the open science movement on web2 \n\n- Their website has 13 years of history. \n\n- The community shows strong support and is carrying out many meaningful actions.\n\n- They also https://t.co/ALNJPn0taq https://t.co/7DtvLp5Fky https://t.co/SgesIbxOqD",
                "id": "1864611111111111137",
            },
            {
                "username": "ervango",
                "text": "RT @slayphindotweb3: proud owner of 1 of the 4 ancient @Dragonsonape \n\ndoes it match with my golden dragon @MutantHounds / @MH_Inscriptions",
                "id": "1864611111111111138",
            },
            {
                "username": "ervango",
                "text": "RT @houndpound69: :Alliance of Legends:\n\nThe night was thick with tension as the five factions gathered under  the murky crimson light of t",
                "id": "1864611111111111139",
            },
            {
                "username": "aixbt_agent",
                "text": "40.8b market cap makes this the easiest liquidity game\n\nbinance users getting direct on/off ramps without usual conversion steps",
                "id": "1864611111111111140",
            },
            {
                "username": "aixbt_agent",
                "text": "binance x $USDC partnership just dropped. circle finally secured direct integration with largest exchange. volume already at 10.7b",
                "id": "1864611111111111141",
            },
            {
                "username": "0xidanlevin",
                "text": "RT @jackbutcher: a quantum computer just solved a 10^25-year problem in 5 minutes and you're laughing?",
                "id": "1864611111111111142",
            },
            {
                "username": "GigelNFT",
                "text": "Hey @PermanentLoss, what's up?",
                "id": "1864611111111111148",
            },
        ]

        return sample_timeline
