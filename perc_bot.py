import csv
import configparser
import discord
import asyncio
import json
import re
import traceback
import sys
from ast import literal_eval

prefix = '!'
mtwow = '305508311892099072'#server id

config = configparser.ConfigParser()
config.read('config.ini')
encoding = config['DEFAULT']['Encoding']	

client = discord.Client()

help_mess = "I am Perc Bot! Here are my commands! \n\n"
help_mess+='Put (Round Brackets) around any multiple word arguments. Usually for item descriptions\n\n'
help_mess+='`{}help`-Displays this message.\n'.format(prefix)
help_mess+='`{}percs [user]`-See how many percs you have. Owners can ping someone in the message to see how many percs they have.\n'.format(prefix)
help_mess+='`{}tier [user]`-See your tier. Owners can ping someone in the message to see their tier.\n'.format(prefix)
help_mess+='`{}transacinfo [user]`-See transaction history. Owners can ping someone to see their history.\n'.format(prefix)
help_mess+='`{}allitems`-Lists all the items available in your tier.\n'.format(prefix)
help_mess+='`{}canbuy`-Lists all the items you can afford.\n'.format(prefix)
help_mess+='`{}iteminfo <item>`-Get info on an item\n'.format(prefix)
help_mess+='`{}myitems [user]`-DMs you your items. Owners can use this to see other people\'s items.\n'.format(prefix)
help_mess+='`{}buy <item>`-Buy an item from the shop\n'.format(prefix)
help_mess+='`{}useitem <item>`-Uses an item in your inventory. Then DMs nerd so he knows. \n'.format(prefix)
help_mess+='`{}getsource`-Get the bot\'s source code. \n\n'.format(prefix)
owner_help='**Owner Only**\n\n'
owner_help+='`{}transac <users> <amount>`-Give or take percs from mentioned users. Amount should be a negative number to remove percs.\n'.format(prefix)
owner_help+='`{}add <item> <cost> <tier> [amount] [description]`-Adds item with the price/tier specified. Sets amount not add. Amount defaults to infinity.\n'.format(prefix)
owner_help+='`{}edit <item> <attribute:value>` attribute = `amount`|`description`|`price`|`tier`. Edits an item\n'.format(prefix)
owner_help+='`{}alias <item> <add|remove> <alias>` adds an alias for an item\n'.format(prefix)
owner_help+='`{}nexttier <item> <tier>` make an item set a user to a tier when bought.\n'.format(prefix)
owner_help+='`{}maxtier <item> <tier>` set the highest tier at which a player can buy an item. (inclusive)\n'.format(prefix)
owner_help+='`{}usertiers <tier>` get the people at a tier.\n'.format(prefix)
owner_help+='`{}remove <item>`-Removes specified item. From shop and all inventories.\n'.format(prefix)
owner_help+='`{}blacklist [users]`-Prevents mentioned users from using bot commands. Run without arguments to show blacklist.\n' .format(prefix)
owner_help+='`{}whitelist <users>`-Unblacklists users.\n'.format(prefix)
owner_help+='`{}give <user> <item>`-Gives an item to a user free of charge.\n'.format(prefix)
owner_help+='`{}take <user> <item>`-Removes an item from a user\'s inventory.\n'.format(prefix)
owner_help+='`{}shopupdate`-Updates bot\'s record of the store.\n'.format(prefix)
owner_help+='`{}settier` <users> <tier>-Sets a user\'s tier.\n'.format(prefix)
owner_help+='`{}addtier` <users> <amount>-Adds to a user\'s tier.\n'.format(prefix)
owner_help+='`{}remind [message]` -Reminds potentially bankrupt people to submit.\n\n'.format(prefix)
suff_help='This bot was made by hanss314 and is hosted by some_nerd. Ping hanss314 if the bot acts strange and ping some_nerd if the bot doesn\'t act'

inventories = {}
items = {}
people = {}
blacklist = []

def add_perc(twowers,amount,everyone=False):
    encountered=False
    if not everyone:
        for twower in twowers:
            try:
                people[twower]['percs']+=amount
                people[twower]['transacts'].append(amount)
                encountered=True
            except KeyError:
                pass               
    else:
        encountered=True
        for user in people.values():
            user['percs']+=amount
            user['transacts'].append(amount)
        
    if not encountered:
        print('None found')
        return False
                
    write_shop_info()
    return True

def registered(twower):
    return twower in people.keys()

def get_sum(twower):
    try:
        people[twower]['percs']=sum(people[twower]['transacts'])
        return people[twower]['percs']
    except KeyError:
        return 0
    
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    get_shop_info()
    get_blacklist()
    await client.change_presence(game=discord.Game(name='{}help'.format(prefix)))
    
def get_shop_info():
    global people
    global items
    global inventories
    try:
        people=json.load(open('bot_data/people.json','r'))
    except FileNotFoundError:
        get_names()
    for user in people.values():
        should_haves = {'name':'','tier':0,'percs':0,'transacts':[]}
        for variable in should_haves.keys():
            if not variable in user.keys():
                user[variable]=should_haves[variable]
            
    with open('bot_data/people.json','w') as writer:
        writer.write(json.dumps(people,sort_keys=True,indent=4, separators=(',', ': ')))
        
    try:
        items=json.load(open('bot_data/items.json','r'))
    except FileNotFoundError:
        items={}
        with open('bot_data/items.json','w') as writer:
            writer.write(json.dumps(items,sort_keys=True,indent=4, separators=(',', ': ')))
    
    try:
        inventories=json.load(open('bot_data/inventories.json','r'))
    except FileNotFoundError:
        for uid in people.keys():
            inventories[uid]={}
            for tier in items:
                for item in tier.keys():
                    inventories[uid][item]=0
                    
        with open('bot_data/inventories.json','w') as writer:
            writer.write(json.dumps(inventories,sort_keys=True,indent=4, separators=(',', ': ')))
            
def write_shop_info():
    with open('bot_data/items.json','w') as writer:
        writer.write(json.dumps(items,sort_keys=True,indent=4, separators=(',', ': ')))
    with open('bot_data/inventories.json','w') as writer:
        writer.write(json.dumps(inventories,sort_keys=True,indent=4, separators=(',', ': ')))
    get_names()
    
def write_blacklist():
    global blacklist
    with open('bot_data/blacklist.json','w') as writer:
        writer.write(json.dumps(blacklist))
        
def get_blacklist():
    global blacklist
    try:
        blacklist=json.load(open('bot_data/blacklist.json','r'))
    except FileNotFoundError:
        pass
    
def get_names():
    global people
    for server in client.servers:
        client.request_offline_members(client.get_server(server))
    for member in client.get_all_members():
        try:
            people[member.id]['name'] = member.name
        except KeyError:
            people[member.id]={'name':member.name}
    open('bot_data/people.json','w').write(json.dumps(people,sort_keys=True,indent=4, separators=(',', ': ')))

def add_item(name,price,tier,amount=-1,description=''):
    global items
        
    items[name]={
        'price':price,
        'amount':amount,
        'tier':tier,
        'description':description
        }
    for user in inventories.values():
        user[name] = 0
        
    write_shop_info()
    return -1
    
def remove_item(item):
    global items
    global inventories
    success=False
    try:
        items.pop(item)
        success=True
    except KeyError:
        pass
                                    
    for user in inventories.values():
        try:
            user.pop(item)
        except KeyError:
            pass
    write_shop_info()
    return success

def give_item(name,item,tier_override=False):#return codes: 0=success,1=user not in database,2=item not in database,3=item out of stock, 4=bad tier
    global items
    usr_inv = {}
    try:
        usr_inv = inventories[name]
    except KeyError:
        return 1
    
    if not item in items.keys():
        return 2
    
    if items[item]['amount']==0:
        return 3
    else:
        items[item]['amount']-=1
        
    try:
        if (not tier_override) and items[item]['tier']>people[name]['tier']:
            return 4
    except KeyError:
        return 1

    try:
        inventories[name][item]+=1
    except KeyError:
        inventories[name][item]=1
        
    try:
        nexttier = items[item]['nexttier']
        if nexttier > people[name]['tier']:
            people[name]['tier'] = nexttier
    except KeyError:
        pass

    write_shop_info()
    return 0
    
def set_tier(names,tier,add=False,everyone=False):
    if not everyone:
        for name in names:
            try:
                if add:
                    people[name]['tier']+=tier
                else:
                    people[name]['tier']=tier
            except KeyError:
                pass
    else:
        for person in people.values():
            if add:
                person['tier']+=tier
            else:
                person['tier']=tier
    write_shop_info()
    
def parse_args(string):#a few special cases
    string = string.strip()
    args=[]
    current = ''
    dash_count = 0
    should_split = True
    for c in string:
        if c == '(':
            should_split = False
        elif c==')':
            should_split=True
        elif c==' ' and should_split:
            args.append(current)
            current=''
        else:
            current+=c
    args.append(current)            
    return args[1:]
        
def get_item(name):
    for key, value in items.items():
        try:
            if key == name or (name in value["aliases"]):
                return key
        except:
            pass
    raise KeyError

@client.event
async def on_message(message):
    global people
    global inventories
    global items
    if not message.content.startswith(prefix) or message.content.startswith(prefix+prefix):
        return
    
    command = message.content.split(' ')[0][len(prefix):].lower()
    is_owner = message.author.id in ['164152700496379904','240995021208289280','210285266814894081']
    args = parse_args(message.content)
    
    if message.author in blacklist and not is_owner:
        return
    
    try:
        if is_owner:#owner commands
            if command=='transac':
                if len(args)==0:
                    await client.send_message(message.channel,'Usage: `{}transac <users> <amount>`'.format(prefix))
                    return
                amount = 0
                ids=[]
                try:
                    amount = int(args[-1])
                except ValueError:
                    await client.send_message(message.channel,'{} is not a number'.format(args[-1]))
                    return

                if len(message.mentions) >0:
                    for mention in message.mentions:
                        ids.append(mention.id)
                else:
                    if len(args) > 1:
                        ids = [args[0]]
                    else:
                        ids = [message.author.id]
                    
                for id in ids:
                    if not id in people.keys():
                        name = id
                        await client.send_message(message.channel,'{} is not in the database.'.format(name))
                        return
                        
                if amount<0 and not message.mention_everyone:
                    for id in ids:
                        user_total = get_sum(id)
                        if user_total+amount < 0:
                            await client.send_message(message.channel,
                                '{} does not have enough percs! (¶{})'.format(people[id]['name'],user_total))
                            return
                    
                success = add_perc(ids,amount,everyone=message.mention_everyone)
                name_str = ''
                if message.mention_everyone:
                    name_str = 'Everyone'
                elif len(ids) == 1:
                    name_str = people[ids[0]]['name']
                else:
                    for id in ids[:-1]:
                        name_str += people[id]['name']+' '
                    name_str += 'and '
                    name_str += people[ids[-1]]['name']
                
                if success:
                    if amount>=0:
                        await client.send_message(message.channel,'Transaction recorded: {} gained {} percs.'.format(name_str,amount))
                    else:
                        await client.send_message(message.channel,'Transaction recorded: {} lost {} percs.'.format(name_str,-amount))
                else:
                    if len(ids) == 1:
                        await client.send_message(message.channel,
                            'Transaction unsuccessful: {} is not in the database or is not a user.'.format(name_str))
                    else:
                        await client.send_message(message.channel,
                            'Transaction unsuccessful: {} are not in the database or are not a users.'.format(name_str))
            
            elif command == 'blacklist':
                if len(message.mentions)==0:
                    await client.send_message(message.channel,str(blacklist))
                    return
                    
                for user in message.mentions:
                    blacklist.append(user.id)
                write_blacklist()
                names = [user.name for user in message.mentions]
                to_send = ''
                if len(names)==1:
                    to_send = names[0]
                else:
                    to_send = ', '.join(names[:-1])
                    to_send += ' and '
                    to_send += names[-1]
                await client.send_message(message.channel,'Blacklisted {}'.format(to_send))
                
            elif command == 'whitelist':
                if len(message.mentions)==0:
                    await client.send_message(message.channel,'Usage: `{}whitelist <users>'.format(prefix))
                    return
                    
                for user in message.mentions:
                    try:
                        blacklist.remove(user.id)
                    except ValueError:
                        pass
                write_blacklist()
                to_send = ''
                if len(names)==1:
                    to_send = names[0]
                else:
                    to_send = ', '.join(names[:-1])
                    to_send += ' and '
                    to_send += names[-1]
                await client.send_message(message.channel,'Whitelisted {}'.format(to_send))
                    
            elif command == 'add':
                success = False
                try:
                    if len(args) == 3:
                        success=add_item(args[0],int(args[1]),int(args[2]))
                        args.append('Unlimited')
                    elif len(args) == 4:
                        try:
                            success=add_item(args[0],int(args[1]),int(args[2]),amount=abs(int(args[3])))#treat as int
                        except ValueError:
                            success=add_item(args[0],int(args[1]),int(args[2]),description=args[3])#treat as string
                            args[3]='Unlimited'
                    elif len(args) == 5:
                        success=add_item(args[0],int(args[1]),int(args[2]),abs(int(args[3])),description=args[4])
                    else:
                        await client.send_message(message.channel,
                            'Usage: `{}add <item> <price> <tier> [amount] [description]`'.format(prefix))
                        return
                except ValueError:
                    await client.send_message(message.channel,'`price` and `tier` must be integers.')
                await client.send_message(message.channel,'`{}`x {} added to tier {}. It costs ¶{}.'.format(args[3],args[0],args[2],args[1]))
                
            elif command == 'edit':
                try:
                    item = None
                    try:
                        item = items[args[0]]
                    except KeyError:
                        await client.send_message(message.channel,args[0]+' is not an item.')
                        return
                    dict_str = "','".join(args[1:])
                    dict_str = re.sub(':', "':'", dict_str)
                    dict_str = "{'"+dict_str+"'}"
                    changes = literal_eval(dict_str)
                    if type(changes)==set:
                        await client.send_message(message.channel,'Whoops, did you forget a colon somewhere?')
                    for key,value in changes.items():
                        if key in ['amount','price','tier']:
                            try:
                                value = int(value)
                                if key in ['amount','price','description','tier']:
                                    item[key]=value
                            except ValueError:
                                await client.send_message(message.channel,
                                    '{} must be an integer.'.format(key))
                        
                    write_shop_info()
                except:
                    await client.send_message(message.channel,
                        'Usage: `{}edit <item> <attribute:value>` attribute = `amount`|`description`|`price`|`tier` '.format(prefix))
                    
            elif command == 'alias':
                if len(args) != 3:
                    await client.send_message(message.channel, 'Usage: `{}alias <item> <add|remove> <alias>`'.format(prefix))
                    return
                item = None
                try:
                    item = items[args[0]]
                except KeyError:
                    await client.send_message(message.channel,args[0]+' is not an item.')
                    return
                aliases = []
                try:
                    aliases = item["aliases"]
                except:
                    pass
                if args[1] == 'add':
                    aliases.append(args[2])
                elif args[1] == 'remove':
                    try:
                        aliases.remove(args[2])
                    except:
                        pass
                else:
                    await client.send_message(message.channel, 'Usage: `{}alias <item> <add|remove> <alias>`'.format(prefix))
                    return
                
                item["aliases"] = aliases
                write_shop_info()
            
            elif command == 'nexttier':
                if len(args) != 2:
                    await client.send_message(message.channel,'Usage: `{}nexttier <item> <tier>'.format(prefix))
                    
                item = None
                try:
                    item = items[args[0]]
                except KeyError:
                    await client.send_message(message.channel,args[0]+' is not an item.')
                    return
                value = 0
                try:
                    value = int(args[1])
                except ValueError:
                    await client.send_message(message.channel,args[1]+' is not a number.')
                    return
                
                item['nexttier']=value
                await client.send_message(message.channel,'Anyone who buys {} will be set to at least tier {}.'.format(args[0],args[1]))
                write_shop_info()
                
            elif command == 'maxtier':
                if len(args) != 2:
                    await client.send_message(message.channel,'Usage: `{}maxtier <item> <tier>'.format(prefix))
                    
                item = None
                try:
                    item = items[args[0]]
                except KeyError:
                    await client.send_message(message.channel,args[0]+' is not an item.')
                    return
                value = 0
                try:
                    value = int(args[1])
                except ValueError:
                    await client.send_message(message.channel,args[1]+' is not a number.')
                    return
                
                item['maxtier']=value
                await client.send_message(message.channel,'The highest tier to buy {} will be {}.'.format(args[0],args[1]))
                write_shop_info()
                
            elif command == 'usertiers':
                if len(args) != 1:
                    await client.send_message(message.channel,'Usage: `{}usertiers <tier>'.format(prefix))
                    return
                    
                tier = 0
                try:
                    tier = int(args[0])
                except ValueError:
                    await client.send_message(message.channel,args[1]+' is not a number.')
                    return
                
                to_send = ''
                await client.send_message(message.channel,'These people are at tier {}:'.format(tier))
                for person in people.values():
                    if person['tier']==tier:
                        if len(person['name'])+len(to_send)>1990:
                            await client.send_message(message.channel,to_send.format(tier))
                            to_send = ''
                        to_send += person['name']+'\n'
                        
                if to_send != '':
                    await client.send_message(message.channel,to_send.format(tier))
                    
            elif command == 'remove':
                if len(args)!=1:
                    await client.send_message(message.channel,'Usage: `{}remove <item>`'.format(prefix))
                    return
                item = args[0]
                success=remove_item(item)
                if success:
                    await client.send_message(message.channel,'{} removed from shop.'.format(args[0]))
                else:
                    await client.send_message(message.channel,'{} is not an item.'.format(args[0]))
                
            elif command == 'shopupdate':
                get_shop_info()
                await client.send_message(message.channel,'Shop updated.')
            
            elif command=='give':
                if len(args)!=2:
                    await client.send_message(message.channel,'Usage: `{}give <user> <item>`'.format(prefix))
                    return
                
                id = ''
                item = args[1]
                try:
                    id = message.mentions[0].id
                except IndexError:
                    id = args[0]
                
                success = give_item(id,item,tier_override=True)
                if success==0:
                    await client.send_message(message.channel,'Gave one {} to {}'.format(item,people[id]['name']))
                elif success==1:
                    await client.send_message(message.channel,'<@!{}> is not in the database'.format(id))
                elif success==2:
                    await client.send_message(message.channel,'{} is not an item, use `{}add` to make it one.'.format(item,prefix))
                elif success==3:
                    await client.send_message(message.channel,'{} is out of stock, use `{}add` to restock it.'.format(item,prefix))
                    
            elif command=='take':
                if len(args)!=2:
                    await client.send_message(message.channel,'Usage: `{}give <user> <item>`'.format(prefix))
                    return
                
                id = ''
                item = args[1]
                try:
                    id = message.mentions[0].id
                except IndexError:
                    id = args[0]
                    
                try:
                    usr_inv = inventories[id]
                except KeyError:
                    await client.send_message(message.channel,'<@!{}> is not in the database'.format(id))
                    return
                    
                try:
                    inventories[id][item] -= 1
                except KeyError:
                    await client.send_message(message.channel,'{} is not an item.'.format(item))
                    return
                
                if inventories[id][item] < 0:
                    inventories[id][item] = 0
                await client.send_message(message.channel, 'Took one {} from <@!{}>'.format(item,id))
                
            elif command=='settier' or command=='addtier':
                amount = 0
                ids=[]
                add=False
                everyone=False
                if len(args)==0:
                    if command=='addtier':
                        await client.send_message(message.channel,'Usage: `{}addtier [users] <amount>`'.format(prefix))
                    else:
                        await client.send_message(message.channel,'Usage: `{}settier [users] <amount>`'.format(prefix))
                    return
                try:
                    amount = int(args[-1])
                except ValueError:
                    await client.send_message(message.channel,'{} is not a number'.format(args[-1]))
                    return

                if len(message.mentions) >0:
                    for mention in message.mentions:
                        ids.append(mention.id)
                else:
                    if len(args) > 1:
                        ids = [args[0]]
                    else:
                        ids = [message.author.id]
                
                if message.mention_everyone:
                    everyone=True
                if command=='addtier':
                    add = True
                    
                set_tier(ids,amount,add=add,everyone=everyone)
                name_str='' 
                if message.mention_everyone:
                    name_str = 'everyone'
                elif len(ids) == 1:
                    name_str = people[ids[0]]['name']
                else:
                    for id in ids[:-1]:
                        name_str += people[id]['name']+' '
                    name_str += 'and '
                    name_str += people[ids[-1]]['name']
                    
                to_send = ''
                if command=='addtier':
                    to_send='Added {} to tier for {}.'.format(amount,name_str)
                else:
                    to_send='Set tier to {} for {}.'.format(amount,name_str)
                await client.send_message(message.channel,to_send)
                
            elif command=='remind':
                to_send = ' '.join(args)
                shopmtwow = client.get_server(mtwow)
                await client.request_offline_members(shopmtwow)
                pbrole = discord.utils.find(lambda role: role.name=='Potentially Bankrupt', shopmtwow.roles)
                for member in shopmtwow.members:
                    if pbrole in member.roles:
                        try:
                            await client.send_message(member, "Reminder to submit! {}".format(to_send))
                        except:
                            pass
                        
            elif command == 'exception':
                raise Exception('This is a test')
            
            elif command == 'kill':
                sys.exit()
                
        #user commands
        if command=='percs':
            id=''
            tried_other=False
            to_send = ''
            if is_owner:
                try:
                    id = message.mentions[0].id
                except IndexError:
                    if len(args) > 0:
                        id = args[0]
                    else:
                        id = message.author.id
            else:
                id = message.author.id
                try:
                    if len(message.mentions) > 1 or message.mentions[0].id != message.author.id:
                        tried_other=True
                except IndexError:
                    pass
            
            if not registered(id):
                if id == message.author.id:
                    await client.send_message(message.channel, 'You are not in the database')
                else:
                    await client.send_message(message.channel, '{} is not in the database or is not a user'.format(id))
                return
            
            percs = get_sum(id)
            
            if tried_other:
                to_send += 'You can only see how many percs you have. '
            
            if message.author.id == id:
                to_send += 'You have'
            else:
                to_send += people[id]['name']+' has'
                
            if percs == 1:
                await client.send_message(message.author,'{} 1 perc.'.format(to_send))
            else:
                await client.send_message(message.author,'{} {} percs.'.format(to_send,percs))
                
        elif command=='help':
            await client.send_message(message.channel,help_mess)
            if is_owner:
                await client.send_message(message.channel,owner_help)
            await client.send_message(message.channel,suff_help) 
            

        elif command=='tier':
            id=''
            tried_other=False
            to_send = ''
            if is_owner:
                try:
                    id = message.mentions[0].id
                except IndexError:
                    if len(args) > 0:
                        id = args[0]
                    else:
                        id = message.author.id
            else:
                id = message.author.id
                try:
                    if len(message.mentions) > 1 or message.mentions[0].id != message.author.id:
                        tried_other=True
                except IndexError:
                    pass
            
            if not registered(id):
                if id == message.author.id:
                    await client.send_message(message.channel, 'You are not in the database')
                else:
                    await client.send_message(message.channel, '{} is not in the database or is not a user'.format(message.mentions[0].name))
                return
            
            tier = people[id]['tier']
            
            if tried_other:
                to_send += 'You can only see your tier. '
            
            if message.author.id == id:
                to_send += 'You are at'
            else:
                to_send += people[id]['name']+' is at'
                
            await client.send_message(message.author,'{} tier {}.'.format(to_send,tier))  
         
        elif command=='transacinfo':
            id=''
            tried_other=False
            to_send = ''
            if is_owner:
                try:
                    id = message.mentions[0].id
                except IndexError:
                    if len(args) > 0:
                        id = args[0]
                    else:
                        id = message.author.id
            else:
                id = message.author.id
                try:
                    if len(message.mentions) > 1 or message.mentions[0].id != message.author.id:
                        tried_other=True
                except IndexError:
                    pass
            
            if not registered(id):
                if id == message.author.id:
                    await client.send_message(message.channel, 'You are not in the database')
                else:
                    await client.send_message(message.channel, '{} is not in the database or is not a user'.format(message.mentions[0].name))
                return
            
            hist = people[id]['transacts']
            gains = sum([x for x in hist if x>0])
            losses = sum([-x for x in hist if x<0])
            
            if tried_other:
                to_send += 'You can only see your history.\n'
            
            to_send += 'Perc History for **{}**\n'.format(people[id]['name'])
            to_send += 'Account: ¶{}\n'.format(sum(hist))
            to_send += 'Revenue: ¶{}\n'.format(gains)
            to_send += 'Payments: ¶{}\n'.format(losses)
            to_send += 'History: {}'.format(', '.join([str(x) for x in hist]))
                
            await client.send_message(message.author,to_send)   
         
        elif command=='allitems':
            item_tiers = {}
            to_send = ''
            try:
                tier = people[message.author.id]['tier']
            except KeyError:
                await client.send_message(message.channel, "You are not in the database")
                return
            
            if type(items)==int:
                await client.send_message(message.author,'There are no items.'.format(prefix))
                return
            
            for key, value in items.items():
                if value['tier'] <= tier:
                    stock = value['amount']
                    if stock <0:
                        stock='Unlimited' 
                    item_str='*{}*: ¶{}. {} in stock.\n'.format(key,value['price'],stock)
                    try: 
                        item_tiers[value['tier']].append(item_str)
                    except KeyError:
                        item_tiers[value['tier']]=[item_str]
                        
            for key in sorted(item_tiers):
                to_send += '**Tier {}**\n'.format(key)
                to_send += ''.join(sorted(item_tiers[key]))
                to_send+='\n'
                
            if len(to_send)>0:
                await client.send_message(message.author,to_send)
            else:
                await client.send_message(message.author,'There are no items you can view.'.format(prefix))
                
        elif command=='iteminfo':
            if len(args) < 1:
                await client.send_message(message.author,'Usage: `{}iteminfo <item>`'.format(prefix))
                return

            item = ''
            price = 0
            tier = 0
            try:
                item = get_item(' '.join(args))
            except KeyError:
                for key, value in items.items():
                    if args[0].lower()==key.lower():
                        await client.send_message(message.author,'{} is not an item. Did you mean {}'.format(' '.join(args),key))
                        return
                    else:
                        try:
                            for alias in value['aliases']:
                                if alias.lower == args[0].lower():
                                    await client.send_message(message.author,
                                        '{} is not an item. Did you mean {}'.format(' '.join(args),alias))
                                    return
                        except:
                            pass
                    
                await client.send_message(message.author,'{} is not an item.'.format(' '.join(args)))
                return
            
            tier = items[item]['tier']
            price = items[item]['price']
            aliases = []
            try:
                aliases = items[item]['aliases']
            except:
                pass
            try:
                if tier > people[message.author.id]['tier']:
                    await client.send_message(message.author,'{} is not an item.'.format(' '.join(args),prefix))
                    return
            except KeyError:
                await client.send_message(message.author,'You are not in the database')
                return

            stock = items[item]['amount']
            if stock<0:
                stock='Unlimited'
            description = items[item]['description']
            to_send = '**{}**\n'.format(item)
            if len(aliases) >0:
                to_send += 'Aliases: {}\n'.format(', '.join(aliases))
            to_send += 'Price: ¶{}\n'.format(price)
            to_send += 'Stock: {}\n'.format(stock)
            to_send += 'Tier: {}\n\n'.format(tier)
            to_send += description
            await client.send_message(message.author,to_send)
            
        elif command=='canbuy':#blatant copy paste
            item_tiers = {}
            to_send = ''
            tier = people[message.author.id]['tier']
            if type(items)==int:
                await client.send_message(message.author,'There are no items.'.format(prefix))
                return
            
            for key, value in items.items():
                if value['tier'] <= tier and value['price']<=people[message.author.id]['percs']:
                    stock = value['amount']
                    if stock <0:
                        stock='Unlimited'
                    item_str='*{}*: ¶{}. {} in stock.\n'.format(key,value['price'],stock)
                    try: 
                        item_tiers[value['tier']].append(item_str)
                    except KeyError:
                        item_tiers[value['tier']]=[item_str]
                        
            for key in sorted(item_tiers):
                to_send += '**Tier {}**\n'.format(key)
                to_send += ''.join(sorted(item_tiers[key]))
                to_send+='\n'
                
            if len(to_send)>0:
                await client.send_message(message.author,to_send)
            else:
                await client.send_message(message.author,'There are no items you can view.'.format(prefix))
            
        elif command=='myitems':
            id=''
            tried_other=False
            to_send = ''
            item_str = ''
            if is_owner:
                try:
                    id = message.mentions[0].id
                except IndexError:
                    if len(args) > 0:
                        id = args[0]
                    else:
                        id = message.author.id
            else:
                id = message.author.id
                try:
                    if len(message.mentions) > 1 or message.mentions[0].id != message.author.id:
                        tried_other=True
                except IndexError:
                    pass
            try:
                item_dict = inventories[id]
            except KeyError:
                if id == message.author.id:
                    await client.send_message(message.channel, 'You are not in the database')
                else:
                    await client.send_message(message.channel, '{} is not in the database or is not a user'.format(message.mentions[0].name))
                return
            
            if tried_other:
                to_send += 'You can only see how many items you have. Here are your items:\n'
            
            
            for key, value in item_dict.items():
                if value>0:
                    item_str+='{}: {}\n'.format(key,value)
            if len(item_str)==0:
                if message.author.id == id:
                    item_str = 'You have no items.'
                else:
                    item_str='{} has no items.'.format(people[id]['name'])
                
            to_send += item_str
            
            await client.send_message(message.author, to_send)
            
        elif command=='useitem':
            if len(args)<1:
                await client.send_message(message.channel, 'Usage: `{}useitem` <item>'.format(prefix))
                return                                          

            id = message.author.id
            item = ''
            try:
                item_dict = inventories[id]
            except KeyError:
                await client.send_message(message.channel, 'You are not in the database')
                return

            try:
                item = get_item(' '.join(args))
                if item_dict[item] > 0:
                    item_dict[item] -=1
                else:
                    await client.send_message(message.channel, 
                        'You don\'t have any {}. Use `{}myitems` to see your items.'.format(' '.join(args),prefix))
                    return
            except KeyError:
                for key, value in items.items():
                    if args[0].lower()==key.lower():
                        await client.send_message(message.author,'{} is not an item. Did you mean {}'.format(' '.join(args),key))
                        return
                    else:
                        try:
                            for alias in value['aliases']:
                                if alias.lower == args[0].lower():
                                    await client.send_message(message.author,
                                        '{} is not an item. Did you mean {}'.format(' '.join(args),alias))
                                    return
                        except:
                            pass
                await client.send_message(message.author,'{} is not an item.'.format(' '.join(args)))
                return
            
            await client.send_message(message.channel, 'You have used {}. Nerd has been alerted'.format(args[0]))
            nerd = await client.get_user_info('210285266814894081')
            await client.send_message(nerd, '{} has used {}'.format(message.author.name,item))
            inventories[id] = item_dict
            write_shop_info()
            
        elif command=='buy':
            if len(args) < 1:
                await client.send_message(message.author,'Usage: `{}buy <item>`'.format(prefix))
                return
                
            price = 0
            item = ''
            try:
                item = get_item(' '.join(args))
            except KeyError:
                for key, value in items.items():
                    if ' '.join(args).lower()==key.lower():
                        await client.send_message(message.author,'{} is not an item. Did you mean {}'.format(' '.join(args),key))
                        return
                    else:
                        try:
                            for alias in value['aliases']:
                                if alias.lower == ' '.join(args).lower():
                                    await client.send_message(message.author,
                                        '{} is not an item. Did you mean {}'.format(' '.join(args),alias))
                                    return
                        except:
                            pass
                    
                await client.send_message(message.author,'{} is not an item.'.format(' '.join(args)))
                return
            
            price = items[item]['price']
            try:#starting to bodge
                if items[item]['maxtier'] < people[message.author.id]['tier']:
                    return
            except:		
                pass
            
            try:
                user_total=people[message.author.id]['percs']
                if price > user_total:
                    await client.send_message(message.author,'You do not have enough percs! (¶{})'.format(user_total))
                    return
            
            except KeyError:
                await client.send_message(message.author,'You are not in the database')
                return

            success = give_item(message.author.id,item)
            if success==0:
                add_perc([message.author.id],-price)
                await client.send_message(message.author,'You bought one {} for ¶{}. Nerd has been alerted.'.format(item,price))
                nerd = await client.get_user_info('210285266814894081')
                await client.send_message(nerd, '{} has bought {}.'.format(message.author.name,item))
            elif success==4:
                await client.send_message(message.author,'{} is not an item.'.format(item,prefix))
            elif success==3:
                await client.send_message(message.author,'{} is out of stock, use `{}add` to restock it.'.format(item,prefix))
            write_shop_info()
            
        elif command == 'getsource':
            print("hi")
            with open('perc_bot.py','rb') as source:
                await client.send_file(message.author, source, content='Here is the source code. View at your own risk')
        
    except Exception as e:
        if type(e)==discord.errors.Forbidden:
            client.send_message(message.channel, 'The bot could not send a message')
            return
        print(e)
        tb = e.__traceback__
        hanss314 = await client.get_user_info('240995021208289280')
        await client.send_message(hanss314,message.author.name+' '+command+'\n'+str(type(e))+str(e)+'\n'+str(traceback.extract_tb(tb)))
        await client.send_message(message.channel, 'Something has gone wrong. hanss314 has been notified. '+
                                  'Please take note of what just happened and tell hanss314 if they ask. '+
                                  '~~Watch this training video for more detailed instructions.~~ '+ 
                                  'The bot should still be operational.')
token = open('token.txt','r').readline().replace('\n','')
client.run(token)
