import tweepy
from app.ai.models import TweetModel, TweetThreadModel

class TwitterClient:
    def __init__(self, api_key, api_secret, access_token, access_token_secret):
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True,
        )

    def post_tweet(self, tweet: TweetModel):
        self.client.create_tweet(
            text=tweet.text,
            quote_tweet_id=tweet.quote_tweet_id,
        )

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
            text=tweets[0].tweet.text,
            quote_tweet_id=tweets[0].tweet.quote_tweet_id,
        )
        previous_id = response.data["id"]

        # Post rest of thread in reply to previous tweet
        for tweet in tweets[1:]:
            response = self.client.create_tweet(
                text=tweet.tweet.text,
                quote_tweet_id=tweet.tweet.quote_tweet_id,
                in_reply_to_tweet_id=previous_id,
            )
            previous_id = response.data["id"]

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
                "username": "LeonidasNFT",
                "text": "RT @cryptolution101: $DOG is backed by Bitcoin  https://t.co/k8Msf7aK8p",
                "id": "1864611111111111143",
            },
            {
                "username": "LeonidasNFT",
                "text": "RT @polis_btc: Gm $DOG Army https://t.co/siTSEP8NLv",
                "id": "1864611111111111144",
            },
            {
                "username": "LeonidasNFT",
                "text": "RT @JOHNRICK17XX: youre not ready. $DOG (Bitcoin) https://t.co/aVHR0eQjq8",
                "id": "1864611111111111145",
            },
            {
                "username": "LeonidasNFT",
                "text": "RT @CoinsWeb3: Not sleeping \n\nI have a good feeling \n\n$DOG",
                "id": "1864611111111111146",
            },
            {
                "username": "LeonidasNFT",
                "text": "RT @CoinsWeb3: When $DOG (Bitcoin) hits 1 billion market cap, everyone will claim they saw it coming. \n\nBut the real question is, did they",
                "id": "1864611111111111147",
            },
            {
                "username": "GigelNFT",
                "text": "Hey @PermanentLoss, what's up?",
                "id": "1864611111111111148",
            },
        ]

        return sample_timeline
