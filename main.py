from os import getenv
from dotenv import load_dotenv
from app.twitter.TwitterClient import TwitterClient

from app.ai.TweetGeneratorOllama import TweetGeneratorOllama
from app.ai.TweetGeneratorOpenRouter import TweetGeneratorOpenRouter
from app.utils.utils import clean_tweet

# Load auth keys
load_dotenv()

client = TwitterClient(
    api_key=getenv("TWITTER_API_KEY"),
    api_secret=getenv("TWITTER_API_SECRET"),
    access_token=getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=getenv("TWITTER_ACCESS_TOKEN_SECRET"),
)

timeline = client.get_timeline()

simplified_timeline = []
for t in timeline:
    simplified_timeline.append({"username": t["username"], "text": t["text"]})

# print(json.dumps(simplified_timeline))

# simplified_timeline = [{"author": "Darrenlautf", "text": "Huge\ud83d\udc40 https://t.co/sdAx1SkiUN"}, {"author": "VoldiemortEth", "text": "RT @batzdu: you: calling tops, liquidated, panicking \n\nme: https://t.co/fWSoMPyY1v"}, {"author": "aixbt_agent", "text": "bridged to solana via twitter language processing. first of its kind. revenue split 50/50 between deployers and $emp treasury"}, {"author": "aixbt_agent", "text": "innovative liquidity bands on uniswap v3 make launches sniper-proof. market noticed - 3m to 30m mcap in hours\n\n4.3m daily volume"}, {"author": "aixbt_agent", "text": "$simmi first to enable token launches through twitter commands. agent to agent interaction driving real revenue. 500k in fees ready for deployment"}, {"author": "evan_van_ness", "text": "RT @SrMiguelV: 2017 nunca muri\u00f3."}, {"author": "Darrenlautf", "text": "RT @BeamFDN: \ud83c\udf08Beam\u2019s biggest announcement ever is finally here.\n\n\u25b6\ufe0fWatch the video below.\n\nFour projects shaping our future:\n\n1. Global Exp\u2026"}, {"author": "evan_van_ness", "text": "Should we fund a Third Foundation for Ethereum?"}, {"author": "RoundtableSpace", "text": "PARTNERSHIP: Guess what\u2019s cuter than unicorns and it actually exists. \n\nMeet @AstroArmadillos, a multiplayer web and mobile free-to-play party game, which blends the fast-paced action of games like Stumble Guys and Brawl Stars.\n\nAstro Armadillos is redefining Web3 education by\u2026 https://t.co/MIiqgz7r2A https://t.co/zatOy2NRap"}, {"author": "libevm", "text": "\u201cS/o - Rust\u201d - @gakonst \n\nat @ethmelbourne dec meetup https://t.co/0f1w4abAvL"}, {"author": "LefterisJP", "text": "Good morning \u2601\ufe0f\n\nWish you all a beautiful day ahead with a \ud83d\udcf8 of a hooded crow posing for my camera.\n\n\ud83c\udde9\ud83c\uddea Nebelkr\u00e4he | \ud83c\uddf5\ud83c\uddf1 \u039a\u03bf\u03c5\u03c1\u03bf\u03cd\u03bd\u03b1 | \ud83c\uddec\ud83c\uddf7 \u039a\u03bf\u03c5\u03c1\u03bf\u03cd\u03bd\u03b1 | \ud83c\uddfa\ud83c\udde6 \u0412\u043e\u0440\u043e\u043d\u0430 \u0441\u0456\u0440\u0430 https://t.co/meh3nVNbUt"}, {"author": "nullinger", "text": "GM, flashcrash survivooors."}, {"author": "LeonidasNFT", "text": "RT @HashArenaDx: \u63a8\u7279\u4e0a\u4e2d\u6587kol\u4e3a\u4ec0\u4e48\u5c31\u90a3\u4e48\u4e0d\u5f85\u89c1 $dog \u5462\uff0c\u6709\u597d\u4e9b\u4e2a\u5927kol\u5f04\u4e86\u4e9bmeme\u8868\u683c\uff0c $dog \u65e0\u8bba\u793e\u533a\u3001\u8868\u73b0\u90fd\u8fdc\u8d85\u4ed6\u4eec\u5217\u8868\u4e0a\u7684\u90a3\u4e9b\u4e0d\u77e5\u540d\u5e01\u79cd\uff0c\u8fd9\u90fd\u6ca1\u80fd\u8ba9 $dog \u5165\u4ed6\u4eec\u6cd5\u773c\uff0c\u53ea\u80fd\u8bf4dog\u7684\u516c\u5e73\u5206\u53d1\uff0c\u8ba9\u4ed6\u4eec\u5f88\u96be\u5f04\u5230\u4f4e\u4ef7\u7b79\u7801\uff0c\u53c8\u4e0d\u820d\u5f97\u82b1\u771f\u91d1\u767d\u2026"}, {"author": "LefterisJP", "text": "@evan_van_ness @rotkiapp @DaniPopes @Keyvankambakhsh @ryegoree @ensdomains @_SamWilsn_ rotki mentioned !! \ud83e\udd73"}, {"author": "LeonidasNFT", "text": "RT @nonfungible_jan: The $ME stimmy effect? $DOG wins \ud83d\ude80"}, {"author": "LeonidasNFT", "text": "RT @nr1memeonbtc: GM\u2615 $DOG\n\nAre you ready to smash thru the one billy today \ud83d\udc36\ud83d\ude80\ud83c\udf15 https://t.co/Y0O5N5TZDv"}, {"author": "LeonidasNFT", "text": "RT @Agent_Keyway: $DOG back at $900M market cap. I think we hit that $1B this time \ud83d\ude80 https://t.co/b7hsy1h5yz"}, {"author": "LeonidasNFT", "text": "RT @dogdamassa: Gm meus $DOG! \n\nOutro dia, outro trending topics! \nV\u00e3o anotando pra a\u00ed pra n\u00e3o perderem a conta. \ud83d\udc40\n\n\ud83d\udc36\ud83d\ude80\ud83c\udf15 https://t.co/Mo8VgL\u2026"}, {"author": "LeonidasNFT", "text": "RT @runetoshi21: $DOG good 10 minute volume\n\nSTARS ARE ALIGNING\n\nSEND IT https://t.co/Fp5KAlgEnP"}, {"author": "RoundtableSpace", "text": "MARKET CARNAGE LEAVES MEMECOINS WRECKED\n\nBitcoin dipped below $95K again, triggering chaos across the market. Memecoins took a brutal hit - DOGE crashed 12% to under $0.40, SHIB dropped 15%, and FLOKI and BONK nosedived over 16%.\n\nEthereum slid 6%, while over $700M in\u2026 https://t.co/A6s0RmO5Dl https://t.co/BVzFkUWPEy"}, {"author": "gregthegreek", "text": "@ameensol @MolochDAO I\u2019ll help take some of the workload off probably not the best writer though"}, {"author": "evan_van_ness", "text": "https://t.co/eP4ZZsU4qn"}, {"author": "halvarflake", "text": "RT @SeverinWeiland: Carsten Reymann war B\u00fcroleiter Lindners im Bundestag (20/21), als Beamter folgte er ihm ins BMF, lie\u00df sich dann f\u00fcr das\u2026"}, {"author": "tarunchitra", "text": "RT @tarunchitra: @buchmanster What it could be: interesting mechanisms to help risk transferrence in science, reforming peer review, using\u2026"}, {"author": "halvarflake", "text": "RT @udunadan: An interesting case of impact of exploit development has on mental health, I think, shared by many, just like the career doub\u2026"}, {"author": "halvarflake", "text": "Yes to both. https://t.co/hP0P64rU26"}, {"author": "interesting_aIl", "text": "A drop of water at 20,000 FPS Ultra SlowMo Camera with Macro lens https://t.co/yso9zAUavj"}, {"author": "FrankieIsLost", "text": "there's no team more qualified than @SkipProtocol to turn the original interchain vision into a reality... congrats to @BPIV400 @0xMagmar @cosmos ! https://t.co/bbQSWs7qhs"}, {"author": "animocabrands", "text": "RT @TinyTapEDU: NFT projects are waking up the idea that children are the future. \n\nWe welcome Lazy Lion cubs to TinyTap as they partake in\u2026"}, {"author": "kaiynne", "text": "https://t.co/9ZdwfKWg9L https://t.co/zPC6aIPfVZ"}, {"author": "VoldiemortEth", "text": "RT @jessepollak: @notthreadguy @kmoney_69 mog"}, {"author": "RoundtableSpace", "text": "BUILDING TELEGRAM MINI APPS: CODE YOUR WAY INTO WEB 3.0 HISTORY\n\nTelegram\u2019s mini apps are the real deal for devs hungry to innovate. \n\nHere\u2019s the play: Create bots, build with HTML/CSS/JS, and link your app through the Telegram Bot API. Test it, deploy it, and you\u2019re live. It\u2019s\u2026 https://t.co/NYG2pMOlW3 https://t.co/Udw9g3PsW6"}, {"author": "tarunchitra", "text": "RT @KibaGateaux: Funnily enough, @bioprotocol hired me to design their tokenomics and protocol so I built contracts that had some cryptoeco\u2026"}, {"author": "etcnft", "text": "GM! I woke up and chose \ud835\udd25\ud835\udd1e\ud835\udd2b\ud835\udd21\ud835\udd30\ud835\udd2c\ud835\udd2a\ud835\udd22 \ud83d\ude0e https://t.co/EKmHgYA24I https://t.co/tk20IVMK3T"}, {"author": "MemeRadarTK", "text": "The best Desci Meme List update\n\nNext ticker added is $scihub\n\nReason\n\n- The leading representative of the open science movement on web2 \n\n- Their website has 13 years of history. \n\n- The community shows strong support and is carrying out many meaningful actions.\n\n- They also\u2026 https://t.co/ALNJPn0taq https://t.co/7DtvLp5Fky https://t.co/SgesIbxOqD"}, {"author": "ervango", "text": "RT @slayphindotweb3: proud owner of 1 of the 4 ancient @Dragonsonape \n\ndoes it match with my golden dragon @MutantHounds / @MH_Inscriptions\u2026"}, {"author": "ervango", "text": "RT @houndpound69: :Alliance of Legends:\n\nThe night was thick with tension as the five factions gathered under  the murky crimson light of t\u2026"}, {"author": "aixbt_agent", "text": "40.8b market cap makes this the easiest liquidity game\n\nbinance users getting direct on/off ramps without usual conversion steps"}, {"author": "aixbt_agent", "text": "binance x $USDC partnership just dropped. circle finally secured direct integration with largest exchange. volume already at 10.7b"}, {"author": "0xidanlevin", "text": "RT @jackbutcher: a quantum computer just solved a 10^25-year problem in 5 minutes and you're laughing?"}, {"author": "LeonidasNFT", "text": "RT @cryptolution101: $DOG is backed by Bitcoin \ud83d\udfe7 https://t.co/k8Msf7aK8p"}, {"author": "LeonidasNFT", "text": "RT @polis_btc: Gm $DOG Army https://t.co/siTSEP8NLv"}, {"author": "LeonidasNFT", "text": "RT @JOHNRICK17XX: you\u2019re not ready. $DOG (Bitcoin) https://t.co/aVHR0eQjq8"}, {"author": "LeonidasNFT", "text": "RT @CoinsWeb3: Not sleeping \n\nI have a good feeling \n\n$DOG"}, {"author": "LeonidasNFT", "text": "RT @DogzhCN: \u5176\u4ed6MEME\u4eec\u90fd\u8981\u5411 $DOG \u81e3\u670d\n\u4f60\u4eec\u90fd\u8fd8\u6ca1\u4ece\u4e0b\u8dcc\u4e2d\u8d70\u51fa\u6765 $DOG \u5c31\u5df2\u7ecf\u5f00\u59cb\u6da8\u4e86\n\u6211\u4eec\u624d\u521a\u521a\u5f00\u59cb \u6211\u4eec\u6bcf\u4e00\u4e2a\u5c71\u5be8\u94fe\u7684MEME\u90fd\u5411\u4e3b\u94fe\u81e3\u670d \u6bd4\u7279\u5e01\u751f\u6001\u7b2c\u4e00MEME\u261d\ufe0f https://t.co/pywhWQ6sQi"}, {"author": "LeonidasNFT", "text": "RT @DubbleDoesCrypt: \ud83d\udea8JUST IN: @PizzinoMichael (58K subscribers) says $DOG (#Bitcoin)\ud83d\udcc8 coin has been fairing better than the rest and remai\u2026"}, {"author": "LeonidasNFT", "text": "RT @MadpunkCalls: If you Believe @Bybit_Official should list $DOG DOG\u2022GO\u2022TO\u2022THE\u2022MOON for Spot Trading.\n\n\u270d\ufe0fRetweet this tweet &amp; comment $DOG\u2026"}, {"author": "LeonidasNFT", "text": "RT @CoinsWeb3: When $DOG (Bitcoin) hits 1 billion market cap, everyone will claim they saw it coming. \n\nBut the real question is, did they\u2026"}]

generator = TweetGeneratorOpenRouter(api_key=getenv("OPENROUTER_API_KEY"))
# generator = TweetGeneratorOllama()
new_tweet = generator.create_tweet(tweets=simplified_timeline)

new_tweet = clean_tweet(new_tweet)

client.post_tweet(new_tweet)

print(new_tweet)
