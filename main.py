from os import getenv
from dotenv import load_dotenv
import json
from app.twitter.TwitterClient import TwitterClient

# from app.ai.TweetGeneratorOllama import TweetGeneratorOllama
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
# timeline = [{'id': 1864935852549271789, 'text': 'Why do I feel like I can do this https://t.co/GmKyV8WCjp', 'author_id': 1485068728412913666, 'conversation_id': 1864935852549271789}, {'id': 1864923157854863494, 'text': 'SOCKET has a bunch of bounties for chain abstraction at @ETHIndiaco \n\nI’m excited for the AI x Crypto bounty. If you’re a hacker and need any help feel free to reach out or tag a friend to let them know 🫡 https://t.co/ZuvzDW4WRZ', 'author_id': 66466835, 'conversation_id': 1864923157854863494}, {'id': 1864921919293972549, 'text': 'not a single person from Ethena felt compelled to reply https://t.co/ah45ZilPg2', 'author_id': 1646685096, 'conversation_id': 1864921919293972549}, {'id': 1864920779155972231, 'text': 'Human vs Steepest Roads in America https://t.co/rqzDWODpdp', 'author_id': 1485068728412913666, 'conversation_id': 1864920779155972231}, {'id': 1864919816634614264, 'text': 'RT @simanta_gautam: thanks hasu 🙏\n\nthis work builds on a collective effort of many ideas by many different bitcoiners over the years (e.g.…', 'author_id': 566534886, 'conversation_id': 1864919816634614264}, {'id': 1864918670063120883, 'text': 'licensed armed carry should allow for armed escort drones in case some well dressed asshole tries to shoot you in the back on your way home from work', 'author_id': 1646685096, 'conversation_id': 1864918670063120883}, {'id': 1864917165435949135, 'text': 'RT @Liv_Boeree: And this, kids, is why “hate speech” laws are a bad idea', 'author_id': 1646685096, 'conversation_id': 1864917165435949135}, {'id': 1864913163394732086, 'text': 'This is how baby owls sleep https://t.co/1Xk8QwIScz', 'author_id': 1485068728412913666, 'conversation_id': 1864913163394732086}, {'id': 1864913002866110464, 'text': 'tomorrow', 'author_id': 8705962, 'conversation_id': 1864913002866110464}, {'id': 1864905631775228276, 'text': 'This is the Chinese traditional sport of board-shoe racing https://t.co/FFpsROLwpd', 'author_id': 1485068728412913666, 'conversation_id': 1864905631775228276}, {'id': 1864903018690261355, 'text': 'RT @VivekVentures: Add $295mm to the ETH ETF tally…\n\nNearly $1bn in new inflows since Thanksgiving  🚀 https://t.co/IQyi0NOBGN', 'author_id': 189518354, 'conversation_id': 1864903018690261355}, {'id': 1864900548404875395, 'text': '&gt;$600M longs liquidated on hyperliquid today', 'author_id': 1073132650309726208, 'conversation_id': 1864900548404875395}, {'id': 1864898946834862125, 'text': 'RT @0xvanbeethoven: There is an additional $500 from @SorellaLabs  &amp; $500 from @bantg \n\n&amp; $100 from @yenicelik', 'author_id': 108172903, 'conversation_id': 1864898946834862125}, {'id': 1864893822846546254, 'text': 'RT @gakonst: $10K to whoever lands I256/U256 support in upstream pola-rs/polars release\n\nhttps://t.co/QkHL6LZRJq', 'author_id': 108172903, 'conversation_id': 1864893822846546254}, {'id': 1864890562672763096, 'text': 'Skin Flap Biogeometry https://t.co/Q6jtirQo23', 'author_id': 1485068728412913666, 'conversation_id': 1864890562672763096}, {'id': 1864875432253751311, 'text': 'British company 02 has launched Daisy, an Al-powered "granny" designed to waste scammers\' time with lifelike, rambling conversations https://t.co/9KFbLewuh3', 'author_id': 1485068728412913666, 'conversation_id': 1864875432253751311}, {'id': 1864873181833761178, 'text': '100% accurate. https://t.co/XfxyAc4AkY', 'author_id': 24809221, 'conversation_id': 1864873181833761178}, {'id': 1864872896834998401, 'text': 'RT @pythianism: Not sure how much sense it makes to compare current to 2020-2021 cycles. Prior cycle ended due to massive fraud (FTX/BlockF…', 'author_id': 24809221, 'conversation_id': 1864872896834998401}, {'id': 1864871759163306126, 'text': 'so now i need to pay $200/mo in order to find out whether o1 pro is still a virgin? https://t.co/vQJYwifhT3', 'author_id': 14253911, 'conversation_id': 1864871759163306126}, {'id': 1864866701457645840, 'text': 'Distribution, distribution, distribution https://t.co/JdKZKBAroV', 'author_id': 15411218, 'conversation_id': 1864866701457645840}]

simplified_timeline = []
for t in timeline:
    simplified_timeline.append({"author": "", "text": t["text"]})

# print(json.dumps(simplified_timeline))

generator = TweetGeneratorOpenRouter(api_key=getenv("OPENROUTER_API_KEY"))

new_tweet = generator.create_tweet(tweets=json.dumps(simplified_timeline))

new_tweet = clean_tweet(new_tweet)

client.post_tweet(new_tweet)

print(new_tweet)
