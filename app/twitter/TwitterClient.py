import tweepy
import os
from app.db.Init_db import init_db
from app.db.models.Tweet_model import Tweet
from app.db.models.Storage_model import Storage
from datetime import datetime, timezone
from app.utils.utils import is_likely_spam

class TwitterClient:
    def __init__(self, api_key, api_secret, access_token, access_token_secret, db_path='tweets.db'):
        # First, create auth object
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)
        
        # Create API object for v1.1 endpoints that might be needed
        self.api = tweepy.API(auth)
        
        # Create Client object with bearer token for v2 endpoints
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
            wait_on_rate_limit=True,
        )
        # Initialize database connection
        self.engine, Session = init_db(db_path)
        self.Session = Session

        # Initialize storage
        self.storage = Storage()

        # Cache username and user_id if not already stored
        if not self.storage.get('username'):
            user = self.client.get_me()
            self.storage.set('username', user.data.username)
            self.storage.set('user_id', user.data.id)


    def save_tweet_to_db(self, tweet_data, fetched_for_user=None):
        """Save tweet to database with user context"""
        session = self.Session()
        try:
            # First try to find existing tweet
            existing_tweet = session.query(Tweet).filter_by(tweet_id=str(tweet_data["id"])).first()
            
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
                    created_at=datetime.now(timezone.utc)
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
                "conversation_id": response.data["id"],  # For new tweets, conversation_id is the same as tweet_id
                "username": self.get_own_username()
            }
            self.save_tweet_to_db(tweet_data)
            return response.data["id"]
        return None

    def post_reply(self, text, reply_to_tweet_id, conversation_id):
        """Post a reply and save to local database"""
        try:
            # Verify the tweet exists and we can reply to it
            tweet_to_reply = self.client.get_tweet(
                id=reply_to_tweet_id,
                tweet_fields=["author_id", "conversation_id", "reply_settings"]
            )
            
            if not tweet_to_reply.data:
                print(f"Error: Tweet {reply_to_tweet_id} not found")
                return None
                
            # Check reply settings
            reply_settings = getattr(tweet_to_reply.data, "reply_settings", "everyone")
            if reply_settings != "everyone":
                print(f"Error: Cannot reply to tweet - reply settings: {reply_settings}")
                return None

            # Post the reply
            response = self.client.create_tweet(
                text=text,
                in_reply_to_tweet_id=reply_to_tweet_id
            )
            
            if response.data:
                tweet_data = {
                    "id": response.data["id"],
                    "text": text,
                    "author_id": self.client.get_me().data.id,
                    "conversation_id": conversation_id,
                    "username": self.get_own_username(),
                    "in_reply_to_user_id": reply_to_tweet_id
                }
                self.save_tweet_to_db(tweet_data)
                return response.data["id"]
                
        except Exception as e:
            print(f"Error posting reply: {e}")
            return None
    
    def get_timeline(self):
        tweets = self.client.get_home_timeline(
            max_results=50,
            tweet_fields=[
                "author_id",
                "in_reply_to_user_id",
                "conversation_id",
                "text",
            ],
            expansions=["author_id"],
            user_fields=["username"],
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

    def post_thread(self, tweets: list[str]) -> None:
        """Post a thread of tweets"""
        # Post first tweet
        response = self.client.create_tweet(text=tweets[0])
        previous_id = response.data["id"]

        # Post rest of thread in reply to previous tweet
        for tweet in tweets[1:]:
            response = self.client.create_tweet(
                text=tweet, in_reply_to_tweet_id=previous_id
            )
            previous_id = response.data["id"]

    def get_tweets_for_conversation(self, conversation_id):
        """
        Fetch all tweets for a specific conversation from Twitter API
        
        Args:
            conversation_id (str): The ID of the conversation to fetch
            
        Returns:
            list: List of tweet dictionaries containing tweet data
        """
        conversation_tweets = []
        
        try:
            print(f"\n=== Fetching Conversation {conversation_id} ===")
            
            # First get the original tweet
            print("1. Fetching original tweet...")
            original_tweet = self.client.get_tweet(
                id=conversation_id,
                tweet_fields=[
                    "author_id",
                    "in_reply_to_user_id",
                    "conversation_id",
                    "created_at",
                    "text",
                    "referenced_tweets"
                ],
                expansions=["author_id"],
                user_fields=["username"]
            )
            
            if original_tweet.data:
                # Get the username from the includes
                username = next(
                    user.username
                    for user in original_tweet.includes["users"]
                    if user.id == original_tweet.data.author_id
                )
                
                tweet_data = {
                    "id": original_tweet.data.id,
                    "text": original_tweet.data.text,
                    "author_id": original_tweet.data.author_id,
                    "conversation_id": original_tweet.data.id,
                    "username": username,
                    "in_reply_to_user_id": getattr(original_tweet.data, "in_reply_to_user_id", None),
                    "created_at": original_tweet.data.created_at
                }
                conversation_tweets.append(tweet_data)
                self.save_tweet_to_db(tweet_data, self.get_own_username())

            # Get our own tweets in this conversation
            our_tweets = self.client.search_recent_tweets(
                query=f"conversation_id:{conversation_id} from:{self.get_own_username()}",
                tweet_fields=[
                    "author_id",
                    "in_reply_to_user_id",
                    "conversation_id",
                    "created_at",
                    "text",
                ],
                expansions=["author_id"],
                user_fields=["username"]
            )
            
            if our_tweets.data:
                for tweet in our_tweets.data:
                    tweet_data = {
                        "id": tweet.id,
                        "text": tweet.text,
                        "author_id": tweet.author_id,
                        "conversation_id": tweet.conversation_id,
                        "username": self.get_own_username(),
                        "in_reply_to_user_id": getattr(tweet, "in_reply_to_user_id", None),
                        "created_at": tweet.created_at
                    }
                    conversation_tweets.append(tweet_data)
                    self.save_tweet_to_db(tweet_data, self.get_own_username())

            # Get all other replies in the conversation
            other_replies = self.client.search_recent_tweets(
                query=f"conversation_id:{conversation_id}",
                tweet_fields=[
                    "author_id",
                    "in_reply_to_user_id",
                    "conversation_id",
                    "created_at",
                    "text",
                ],
                expansions=["author_id"],
                user_fields=["username"]
            )
            
            if other_replies.data:
                for tweet in other_replies.data:
                    # Skip if we already have this tweet (from our tweets query)
                    if any(t["id"] == tweet.id for t in conversation_tweets):
                        continue
                        
                    username = next(
                        user.username
                        for user in other_replies.includes["users"]
                        if user.id == tweet.author_id
                    )
                    
                    tweet_data = {
                        "id": tweet.id,
                        "text": tweet.text,
                        "author_id": tweet.author_id,
                        "conversation_id": tweet.conversation_id,
                        "username": username,
                        "in_reply_to_user_id": getattr(tweet, "in_reply_to_user_id", None),
                        "created_at": tweet.created_at
                    }
                    conversation_tweets.append(tweet_data)
                    self.save_tweet_to_db(tweet_data, self.get_own_username())
                    
        except Exception as e:
            print(f"\nERROR fetching conversation {conversation_id}: {e}")
            print(f"Full error details:")
            import traceback
            traceback.print_exc()
        
        print(f"\n=== Summary for Conversation {conversation_id} ===")
        print(f"Total tweets found: {len(conversation_tweets)}")
        print("Participants:", ", ".join(set(t["username"] for t in conversation_tweets)))
        print("=== End of Conversation Fetch ===\n")
        
        return conversation_tweets
    
    def get_conversations(self, use_local=False, filter_spam=True):
        """
        Fetch mentions and combine with our local tweets to create conversations
        
        Args:
            use_local (bool): If True, only fetch conversations from local database
        """
        conversations = {}

        # Only fetch mentions from Twitter if use_local is False
        if not use_local:
            print("\n=== Fetching Mentions ===")

            last_mention_time = self.storage.get_timestamp('last_mention_time')

            mentions = self.client.get_users_mentions(
                id=self.storage.get('user_id'),
                max_results=50,
                start_time=last_mention_time,
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
            )

            if mentions.data:
                print(f"Found {len(mentions.data)} mentions")
                self.storage.set('last_mention_time', datetime.now(timezone.utc).isoformat())

                # Filter spam mentions before fetching full conversations
                non_spam_mentions = []
                for tweet in mentions.data:
                    author = next(
                        user for user in mentions.includes["users"] 
                        if user.id == tweet.author_id
                    )
                    
                    tweet_data = {
                        'text': tweet.text,
                        'username': author.username
                    }
                    
                    if not filter_spam or not is_likely_spam(tweet_data):
                        non_spam_mentions.append(tweet)
                
                print(f"Processing {len(non_spam_mentions)} non-spam mentions")
                # Process mentions and initialize conversations
                for tweet in non_spam_mentions:
                    if tweet.conversation_id not in conversations:
                        conversations[tweet.conversation_id] = {
                            "tweets": [],
                            "participants": set(),
                            "last_tweet_time": None,
                            "our_last_tweet_time": None
                        }
                        
                        # Fetch all tweets for this conversation
                        conversation_tweets = self.get_tweets_for_conversation(tweet.conversation_id)
                        
                        # Add tweets to the conversation
                        for tweet_data in conversation_tweets:
                            conversations[tweet.conversation_id]["tweets"].append(tweet_data)
                            conversations[tweet.conversation_id]["participants"].add(tweet_data["username"])
                            
                            if (conversations[tweet.conversation_id]["last_tweet_time"] is None or 
                                tweet_data["created_at"] > conversations[tweet.conversation_id]["last_tweet_time"]):
                                conversations[tweet.conversation_id]["last_tweet_time"] = tweet_data["created_at"]
                                
                            if tweet_data["username"] == self.get_own_username():
                                if (conversations[tweet.conversation_id]["our_last_tweet_time"] is None or
                                    tweet_data["created_at"] > conversations[tweet.conversation_id]["our_last_tweet_time"]):
                                    conversations[tweet.conversation_id]["our_last_tweet_time"] = tweet_data["created_at"]

        # Get our tweets from local database
        print("\n=== Fetching Our Tweets from Database ===")
        session = self.Session()
        try:
            our_username = self.get_own_username()
            our_tweets = session.query(Tweet).all()  # Get all tweets from database
            print(f"Found {len(our_tweets)} tweets in database")
            
            for tweet in our_tweets:
                if tweet.conversation_id not in conversations:
                    conversations[tweet.conversation_id] = {
                        "tweets": [],
                        "participants": set(),
                        "last_tweet_time": None,
                        "our_last_tweet_time": None
                    }
                
                tweet_data = {
                    "id": tweet.tweet_id,
                    "text": tweet.text,
                    "author_id": tweet.author_id,
                    "username": tweet.username,
                    "created_at": tweet.created_at
                }
                
                conversations[tweet.conversation_id]["tweets"].append(tweet_data)
                conversations[tweet.conversation_id]["participants"].add(tweet.username)
                
                if (conversations[tweet.conversation_id]["last_tweet_time"] is None or 
                    tweet.created_at > conversations[tweet.conversation_id]["last_tweet_time"]):
                    conversations[tweet.conversation_id]["last_tweet_time"] = tweet.created_at
                    
                if tweet.username == our_username:
                    if (conversations[tweet.conversation_id]["our_last_tweet_time"] is None or
                        tweet.created_at > conversations[tweet.conversation_id]["our_last_tweet_time"]):
                        conversations[tweet.conversation_id]["our_last_tweet_time"] = tweet.created_at
                        
        except Exception as e:
            print(f"Error fetching tweets from database: {e}")
        finally:
            session.close()

        # Print conversation summary
        print("\n=== Final Conversations Summary ===")
        print(f"Total conversations found: {len(conversations)}")
        for conv_id, conv in conversations.items():
            print(f"\nConversation {conv_id}:")
            print(f"Participants: {', '.join(conv['participants'])}")
            print(f"Number of tweets: {len(conv['tweets'])}")
            print(f"Last tweet time: {conv['last_tweet_time']}")
            print(f"Our last tweet time: {conv['our_last_tweet_time']}")
            
        return conversations
    
    def get_own_username(self):
        """Get the authenticated user's username from storage"""
        return self.storage.get('username')
    
    def get_own_user_id(self):
        """Get the authenticated user's user_id from storage"""
        return self.storage.get('user_id')

    def needs_reply(self, conversation):
        """Check if a conversation needs our reply"""
        our_username = self.get_own_username()
        
        # Skip if we were the last to tweet
        if (conversation["our_last_tweet_time"] is not None and
            conversation["our_last_tweet_time"] >= conversation["last_tweet_time"]):
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
            existing_tweet = session.query(Tweet).filter_by(tweet_id=str(tweet_data["id"])).first()
            
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
                    fetched_for_user=fetched_for_user
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
    
    def get_sample_timeline(self):
        """Return sample timeline data for testing"""

        sample_timeline = [
            {
                "username": "Darrenlautf",
                "text": "Huge\ud83d\udc40 https://t.co/sdAx1SkiUN",
            },
            {
                "username": "VoldiemortEth",
                "text": "RT @batzdu: you: calling tops, liquidated, panicking \n\nme: https://t.co/fWSoMPyY1v",
            },
            {
                "username": "aixbt_agent",
                "text": "bridged to solana via twitter language processing. first of its kind. revenue split 50/50 between deployers and $emp treasury",
            },
            {
                "username": "aixbt_agent",
                "text": "innovative liquidity bands on uniswap v3 make launches sniper-proof. market noticed - 3m to 30m mcap in hours\n\n4.3m daily volume",
            },
            {
                "username": "aixbt_agent",
                "text": "$simmi first to enable token launches through twitter commands. agent to agent interaction driving real revenue. 500k in fees ready for deployment",
            },
            {
                "username": "evan_van_ness",
                "text": "RT @SrMiguelV: 2017 nunca muri\u00f3.",
            },
            {
                "username": "Darrenlautf",
                "text": "RT @BeamFDN: \ud83c\udf08Beam\u2019s biggest announcement ever is finally here.\n\n\u25b6\ufe0fWatch the video below.\n\nFour projects shaping our future:\n\n1. Global Exp\u2026",
            },
            {
                "username": "evan_van_ness",
                "text": "Should we fund a Third Foundation for Ethereum?",
            },
            {
                "username": "RoundtableSpace",
                "text": "PARTNERSHIP: Guess what\u2019s cuter than unicorns and it actually exists. \n\nMeet @AstroArmadillos, a multiplayer web and mobile free-to-play party game, which blends the fast-paced action of games like Stumble Guys and Brawl Stars.\n\nAstro Armadillos is redefining Web3 education by\u2026 https://t.co/MIiqgz7r2A https://t.co/zatOy2NRap",
            },
            {
                "username": "libevm",
                "text": "\u201cS/o - Rust\u201d - @gakonst \n\nat @ethmelbourne dec meetup https://t.co/0f1w4abAvL",
            },
            {
                "username": "LefterisJP",
                "text": "Good morning \u2601\ufe0f\n\nWish you all a beautiful day ahead with a \ud83d\udcf8 of a hooded crow posing for my camera.\n\n\ud83c\udde9\ud83c\uddea Nebelkr\u00e4he | \ud83c\uddf5\ud83c\uddf1 \u039a\u03bf\u03c5\u03c1\u03bf\u03cd\u03bd\u03b1 | \ud83c\uddec\ud83c\uddf7 \u039a\u03bf\u03c5\u03c1\u03bf\u03cd\u03bd\u03b1 | \ud83c\uddfa\ud83c\udde6 \u0412\u043e\u0440\u043e\u043d\u0430 \u0441\u0456\u0440\u0430 https://t.co/meh3nVNbUt",
            },
            {"username": "nullinger", "text": "GM, flashcrash survivooors."},
            {
                "username": "LefterisJP",
                "text": "@evan_van_ness @rotkiapp @DaniPopes @Keyvankambakhsh @ryegoree @ensdomains @_SamWilsn_ rotki mentioned !! \ud83e\udd73",
            },
            {
                "username": "LeonidasNFT",
                "text": "RT @runetoshi21: $DOG good 10 minute volume\n\nSTARS ARE ALIGNING\n\nSEND IT https://t.co/Fp5KAlgEnP",
            },
            {
                "username": "RoundtableSpace",
                "text": "MARKET CARNAGE LEAVES MEMECOINS WRECKED\n\nBitcoin dipped below $95K again, triggering chaos across the market. Memecoins took a brutal hit - DOGE crashed 12% to under $0.40, SHIB dropped 15%, and FLOKI and BONK nosedived over 16%.\n\nEthereum slid 6%, while over $700M in\u2026 https://t.co/A6s0RmO5Dl https://t.co/BVzFkUWPEy",
            },
            {
                "username": "gregthegreek",
                "text": "@ameensol @MolochDAO I\u2019ll help take some of the workload off probably not the best writer though",
            },
            {"username": "evan_van_ness", "text": "https://t.co/eP4ZZsU4qn"},
            {
                "username": "halvarflake",
                "text": "RT @SeverinWeiland: Carsten Reymann war B\u00fcroleiter Lindners im Bundestag (20/21), als Beamter folgte er ihm ins BMF, lie\u00df sich dann f\u00fcr das\u2026",
            },
            {
                "username": "tarunchitra",
                "text": "RT @tarunchitra: @buchmanster What it could be: interesting mechanisms to help risk transferrence in science, reforming peer review, using\u2026",
            },
            {
                "username": "halvarflake",
                "text": "RT @udunadan: An interesting case of impact of exploit development has on mental health, I think, shared by many, just like the career doub\u2026",
            },
            {"username": "halvarflake", "text": "Yes to both. https://t.co/hP0P64rU26"},
            {
                "username": "interesting_aIl",
                "text": "A drop of water at 20,000 FPS Ultra SlowMo Camera with Macro lens https://t.co/yso9zAUavj",
            },
            {
                "username": "FrankieIsLost",
                "text": "there's no team more qualified than @SkipProtocol to turn the original interchain vision into a reality... congrats to @BPIV400 @0xMagmar @cosmos ! https://t.co/bbQSWs7qhs",
            },
            {
                "username": "animocabrands",
                "text": "RT @TinyTapEDU: NFT projects are waking up the idea that children are the future. \n\nWe welcome Lazy Lion cubs to TinyTap as they partake in\u2026",
            },
            {
                "username": "kaiynne",
                "text": "https://t.co/9ZdwfKWg9L https://t.co/zPC6aIPfVZ",
            },
            {
                "username": "VoldiemortEth",
                "text": "RT @jessepollak: @notthreadguy @kmoney_69 mog",
            },
            {
                "username": "RoundtableSpace",
                "text": "BUILDING TELEGRAM MINI APPS: CODE YOUR WAY INTO WEB 3.0 HISTORY\n\nTelegram\u2019s mini apps are the real deal for devs hungry to innovate. \n\nHere\u2019s the play: Create bots, build with HTML/CSS/JS, and link your app through the Telegram Bot API. Test it, deploy it, and you\u2019re live. It\u2019s\u2026 https://t.co/NYG2pMOlW3 https://t.co/Udw9g3PsW6",
            },
            {
                "username": "tarunchitra",
                "text": "RT @KibaGateaux: Funnily enough, @bioprotocol hired me to design their tokenomics and protocol so I built contracts that had some cryptoeco\u2026",
            },
            {
                "username": "etcnft",
                "text": "GM! I woke up and chose \ud835\udd25\ud835\udd1e\ud835\udd2b\ud835\udd21\ud835\udd30\ud835\udd2c\ud835\udd2a\ud835\udd22 \ud83d\ude0e https://t.co/EKmHgYA24I https://t.co/tk20IVMK3T",
            },
            {
                "username": "MemeRadarTK",
                "text": "The best Desci Meme List update\n\nNext ticker added is $scihub\n\nReason\n\n- The leading representative of the open science movement on web2 \n\n- Their website has 13 years of history. \n\n- The community shows strong support and is carrying out many meaningful actions.\n\n- They also\u2026 https://t.co/ALNJPn0taq https://t.co/7DtvLp5Fky https://t.co/SgesIbxOqD",
            },
            {
                "username": "ervango",
                "text": "RT @slayphindotweb3: proud owner of 1 of the 4 ancient @Dragonsonape \n\ndoes it match with my golden dragon @MutantHounds / @MH_Inscriptions\u2026",
            },
            {
                "username": "ervango",
                "text": "RT @houndpound69: :Alliance of Legends:\n\nThe night was thick with tension as the five factions gathered under  the murky crimson light of t\u2026",
            },
            {
                "username": "aixbt_agent",
                "text": "40.8b market cap makes this the easiest liquidity game\n\nbinance users getting direct on/off ramps without usual conversion steps",
            },
            {
                "username": "aixbt_agent",
                "text": "binance x $USDC partnership just dropped. circle finally secured direct integration with largest exchange. volume already at 10.7b",
            },
            {
                "username": "0xidanlevin",
                "text": "RT @jackbutcher: a quantum computer just solved a 10^25-year problem in 5 minutes and you're laughing?",
            },
            {
                "username": "LeonidasNFT",
                "text": "RT @cryptolution101: $DOG is backed by Bitcoin \ud83d\udfe7 https://t.co/k8Msf7aK8p",
            },
            {
                "username": "LeonidasNFT",
                "text": "RT @polis_btc: Gm $DOG Army https://t.co/siTSEP8NLv",
            },
            {
                "username": "LeonidasNFT",
                "text": "RT @JOHNRICK17XX: you\u2019re not ready. $DOG (Bitcoin) https://t.co/aVHR0eQjq8",
            },
            {
                "username": "LeonidasNFT",
                "text": "RT @CoinsWeb3: Not sleeping \n\nI have a good feeling \n\n$DOG",
            },
            {
                "username": "LeonidasNFT",
                "text": "RT @CoinsWeb3: When $DOG (Bitcoin) hits 1 billion market cap, everyone will claim they saw it coming. \n\nBut the real question is, did they\u2026",
            },
        ]

        return sample_timeline
