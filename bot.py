import discord
import asyncio
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from discord.ext import commands

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

#bot token
TOKEN = 'ODY2MTY3NDM5MDQ5NjIxNTA1.YPOnSg.3FD4_FFVj9pSyi_prZKukpnbYac'

client = commands.Bot(command_prefix=';')
client.remove_command('help')


@client.event
async def on_ready():
    print('Roboto is online!')


@client.command(aliases=['latency'])
async def ping(ctx):
    await ctx.send(f'Latency: {round(client.latency * 1000)}ms')


@client.command()
async def about(ctx):
    await ctx.send('I was created by Brian Do to find food places near you!')


@client.command(pass_context=True)
async def help(ctx):
    author = ctx.message.author

    embed = discord.Embed(
        colour=discord.Colour.red()
    )

    embed.set_author(name='Help')
    embed.add_field(name=';ping or ;latency', value='Returns latency in ms', inline=False)
    embed.add_field(name=';about', value='Returns bot information', inline=False)
    embed.add_field(name=';find', value='Finds food places on yelp', inline=False)

    await author.send(embed=embed)


@client.command(pass_context=True)
async def find(ctx):
    sender = ctx.message.author.id

    embedVar = discord.Embed(
        colour=discord.Colour.blue()
    )

    def check(m):
        return m.author.id == sender

    #Prompts user for food and location
    try:
        await ctx.send('Enter type of food:')
        food = await client.wait_for('message', check=check, timeout=20)
        food = food.content
        embedVar.set_author(name='🍽️' + food.upper())

        await ctx.send('Enter Location (City, State(Ex:CA) Zip Code):')
        loc = await client.wait_for('message', check=check, timeout=20)
        loc = loc.content
        locArray = loc.split(",")
        embedVar.add_field(name='Location', value=loc.upper(), inline=True)
        city = locArray[0]
        loc = locArray[1]
    except asyncio.TimeoutError:
        await ctx.send('Timed out after 20 seconds!')
    except IndexError:
        pass

    #displays yelp listings
    url = get_url(food, city, loc)
    embedVar.add_field(name='Listings', value=url, inline=True)

    await ctx.send('Loading!')
    places = get_places(url)

    #deletes sponsored results two before the list and one after
    places = places[2:]
    places = places[:10]

    #loop to add restaurants into the fields
    for place in places:
        embedVar.add_field(name=':fork_and_knife:' + place[0],
                           value=':star:' + place[2] + ' with ' + place[3] + ' reviews' + '\n' + place[1],
                           inline=False)

    embedVar.set_footer(text='Generated from Yelp Recommendations', icon_url='https://1000logos.net/wp-content/uploads/2018/01/logo-Yelp.jpg')
    embedVar.set_thumbnail(url='https://1000logos.net/wp-content/uploads/2018/01/logo-Yelp.jpg')
    await ctx.send(embed=embedVar)


#uses extract_places to return an array of places
def get_places(url):
    driver = create_webdriver()
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    results = soup.find_all('div', {'class': 'container__09f24__sxa9- hoverable__09f24__3HkY2 margin-t3__09f24__hHZ'
                                                'sm margin-b3__09f24__3h89A padding-t3__09f24__1VTAn padding-r3__09f24'
                                                '__11Xv2 padding-b3__09f24__2I83c padding-l3__09f24__1JEx9 border--top'
                                                '__09f24__37VAs border--right__09f24__Z9jGU border--bottom__09f24__3lE'
                                                'lq border--left__09f24__akfOa border-color--default__09f24__3Epto'})
    places = []
    for item in results:
        try:
            places.append(extract_places(item))
        except AttributeError:
            pass
    driver.close()
    return places


#extracts place information
def extract_places(item):

    #get name, URL
    atag = item.h4.span.a
    name = atag.text
    url = 'https://www.yelp.com' + atag.get('href')

    #get review count
    rcount = item.find('span', {'class': 'reviewCount__09f24__3GsGY css-e81eai'})
    rcount = rcount.text

    #get star rating
    ratings_parent = item.find('div', {'class': 'attribute__09f24__1La1D display--inline-block__09f24__3SvIn margin-r1_'
                                        '_09f24__3PebR border-color--default__09f24__3Epto'})
    ratings = ratings_parent.span.div.get('aria-label')

    result = (name, url, ratings, rcount)

    return result


#creates the url
def get_url(food, city, loc):
    template = 'https://www.yelp.com/search?find_desc={}&find_loc={}%2C{}&ns=1'
    food = food.replace(' ', '+')
    city = city.replace(' ', '+')
    loc = loc.replace(' ', '+')
    return template.format(food, city, loc)


#create webdriver
def create_webdriver():
    driver = webdriver.Chrome(options=chrome_options)
    return driver

client.run(TOKEN)
