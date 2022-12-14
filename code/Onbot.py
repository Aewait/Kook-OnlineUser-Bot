# encoding: utf-8:
import json
import time
import aiohttp


from khl import Bot, Message, EventTypes, Event,Client,PublicChannel,PublicMessage
from khl.card import CardMessage, Card, Module, Element, Types, Struct


with open('./config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
# 用读取来的 config 初始化 bot，字段对应即可
bot = Bot(token=config['token'])

Botoken=config['token']
kook="https://www.kookapp.cn"
headers={f'Authorization': f"Bot {Botoken}"}

# 向botmarket通信
@bot.task.add_interval(minutes=30)
async def botmarket():
    api ="http://bot.gekj.net/api/v1/online.bot"
    headers = {'uuid':'8b3b4c14-d20c-4a23-9c71-da4643b50262'}
    async with aiohttp.ClientSession() as session:
        await session.post(api, headers=headers)

#############################################################################################

Debug_ch="6248953582412867"

def GetTime(): #将获取当前时间封装成函数方便使用
    return time.strftime("%y-%m-%d %H:%M:%S", time.localtime())

# 开机的时候打印一次时间，记录重启时间
print(f"Start at: [%s]"%GetTime())

# 在控制台打印msg内容，用作日志
def logging(msg: Message):
    now_time = GetTime()
    print(f"[{now_time}] G:{msg.ctx.guild.id} - C:{msg.ctx.channel.id} - Au:{msg.author_id}_{msg.author.username}#{msg.author.identify_num} = {msg.content}")

# 查看bot状态
@bot.command(name='alive')
async def alive_check(msg:Message):
    logging(msg)
    await msg.reply(f"bot alive here")

# 帮助命令
@bot.command(name='CKhelp')
async def help(msg:Message):
    logging(msg)
    cm = CardMessage()
    c3 = Card(Module.Header('目前在线/总人数小助手支持的指令如下'))
    c3.append(Module.Divider())
    #实现卡片的markdown文本
    help_Str="`/alive` 看看bot是否在线\n"
    help_Str+="`/svck` 查看当前服务器的在线/总人数\n"
    help_Str+="`/adck 频道id '前缀' '后缀'` 设置在本服务器的在线人数更新\n默认格式为`频道在线 10/100`。其中`频道在线 `为前缀，默认后缀为空。可以手动指定前缀和后缀，来适应你的频道的命名风格。记得加**英文的引号**来保证前缀/后缀的完整性！\n```\n/adck 111111111111 '频道在线 | ' ' 测试ing'\n```\n"
    help_Str+="在线人数监看设定为30分钟更新一次\n"
    help_Str+="`/tdck` 取消本服务器的在线人数监看\n"
    c3.append(Module.Section(Element.Text(help_Str,Types.Text.KMD)))
    c3.append(Module.Divider())
    c3.append(Module.Section(Element.Text("频道/分组id获取：打开`设置-高级-开发者模式`，右键频道复制id",Types.Text.KMD)))
    c3.append(Module.Divider())
    c3.append(Module.Section('有任何问题，请加入帮助服务器与我联系',
              Element.Button('帮助', 'https://kook.top/gpbTwZ', Types.Click.LINK)))
    cm.append(c3)
    await msg.reply(cm)


# 用于记录服务器信息
ServerDict={
    'guild':'',
    'channel':'',
    'front':'',
    'back':''
}


# 获取服务器用户数量用于更新
async def server_status(Gulid_ID:str):
    url=kook+"/api/v3/guild/user-list"
    params = {"guild_id":Gulid_ID}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params,headers=headers) as response:
                ret1= json.loads(await response.text())
                #print(ret1)
                return ret1

# 直接查看本服务器状态
@bot.command(name='svck')
async def server_user_check(msg:Message):
    logging(msg)
    try:
        ret = await server_status(msg.ctx.guild.id)
        total=ret['data']['user_count']
        online=ret['data']['online_count']
        await msg.reply(f"当前服务器用户状态为：{online}/{total}")
    except Exception as result:
        err_str=f"ERR! [{GetTime()}] check_server_user_status: {result}"
        print(err_str)
        await msg.reply(err_str)
        #发送错误信息到指定频道
        debug_channel= await bot.fetch_public_channel(Debug_ch)
        await bot.send(debug_channel,err_str)


# 设置在线人数监看
@bot.command(name='adck',aliases=['在线人数监看'])
async def Add_server_user_update(msg:Message,ch:str="err",front:str="频道在线 ",back:str=" "):
    logging(msg)
    if ch == 'err':
        await msg.reply(f"您尚未指定用于更新状态的频道！channel: {ch}")
        return

    try:
        global  ServerDict
        ServerDict['guild']=msg.ctx.guild.id
        ServerDict['channel']=ch
        ServerDict['front']=front
        ServerDict['back']=back

        #用两个flag来分别判断服务器和需要更新的频道是否相同
        flag_gu = 0
        flag_ch = 0
        with open("./log/server.json",'r',encoding='utf-8') as fr1:
            data = json.load(fr1)
        for s in data:
            if s['guild'] == msg.ctx.guild.id:
                if s['channel']==ch:
                    flag_ch = 1
                else:
                    s['channel']=ch
                
                s['front']=front
                s['back']=back
                flag_gu = 1
                # 修改了之后立马更新，让用户看到修改后的结果
                ret = await server_status(msg.ctx.guild.id)
                total=ret['data']['user_count']
                online=ret['data']['online_count']
                url=kook+"/api/v3/channel/update"
                params = {"channel_id":ch,"name":f"{s['front']}{online}/{total}{s['back']}"}
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=params,headers=headers) as response:
                        ret1= json.loads(await response.text())
                break
        
        # 执行不同的提示信息
        if flag_gu == 1 and flag_ch==1:
            await msg.reply(f"服务器在线人数监看格式已更新！\n前缀 [{front}]\n后缀 [{back}]")
        elif flag_gu ==1 and flag_ch == 0:
            await msg.reply(f"本服务器在线人数监看已修改频道为{ch}\n前缀 [{front}]\n后缀 [{back}]")
        else:
            # 直接执行第一次更新
            ret = await server_status(msg.ctx.guild.id)
            total=ret['data']['user_count']
            online=ret['data']['online_count']
            url=kook+"/api/v3/channel/update"
            params = {"channel_id":ch,"name":f"{ServerDict['front']}{online}/{total}{ServerDict['back']}"}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=params,headers=headers) as response:
                        ret1= json.loads(await response.text())
            
            # ↓服务器id错误时不会执行下面的↓
            await msg.reply(f'服务器监看系统已添加，首次更新成功！\n前缀 [{front}]\n后缀 [{back}]')
            #将ServerDict添加进list
            data.append(ServerDict)
        
        #不管是否已存在，都需要重新执行写入（更新/添加）
        with open("./log/server.json",'w',encoding='utf-8') as fw1:
            json.dump(data,fw1,indent=2,sort_keys=True, ensure_ascii=False)        
        fw1.close()

    except Exception as result:
        cm2 = CardMessage()
        c = Card(Module.Header(f"很抱歉，发生了一些错误"))
        c.append(Module.Divider())
        c.append(Module.Section(f"【报错】  {result}\n\n您可能需要重新设置本频道的监看事件"))
        c.append(Module.Divider())
        c.append(Module.Section('有任何问题，请加入帮助服务器与我联系',
            Element.Button('帮助', 'https://kook.top/Lsv21o', Types.Click.LINK)))
        cm2.append(c)
        await msg.reply(cm2)

# 取消在线人数监看
@bot.command(name='tdck',aliases=['退订在线人数监看'])
async def Cancel_server_user_update(msg:Message):
    logging(msg)
    global ServerDict
    emptyList = list() #空list
    with open("./log/server.json",'r',encoding='utf-8') as fr1:
        data = json.load(fr1)
    flag = 0 #用于判断
    for s in data:
        if s['guild']==msg.ctx.guild.id:
            flag = 1
            print(f"Cancel: G:{s['guild']} - C:{s['channel']}")
            await msg.reply(f"已成功取消本服务器的在线人数监看")
        else: # 不吻合，进行插入
            #先自己创建一个元素
            ServerDict['guild']=s['guild']
            ServerDict['channel']=s['channel']
            ServerDict['front']=s['front']
            ServerDict['back']=s['back']
            #插入进空list
            emptyList.append(ServerDict)

    #最后重新执行写入
    with open("./log/server.json",'w',encoding='utf-8') as fw1:
        json.dump(emptyList,fw1,indent=2,sort_keys=True, ensure_ascii=False)        
    fw1.close()

    if flag == 0:
        await msg.reply(f"本服务器暂未开启在线人数监看")


# 定时更新服务器的在线用户/总用户状态
@bot.task.add_interval(minutes=30)
async def server_user_update():
    try:
        with open("./log/server.json",'r',encoding='utf-8') as fr1:
            svlist = json.load(fr1)

        for s in svlist:
            now_time=GetTime()
            print(f"[{now_time}] Updating: %s"%s)

            ret = await server_status(s['guild'])
            total=ret['data']['user_count']
            online=ret['data']['online_count']
            url=kook+"/api/v3/channel/update"
            params = {"channel_id":s['channel'],"name":f"{s['front']}{online}/{total}{s['back']}"}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=params,headers=headers) as response:
                        ret1= json.loads(await response.text())
            
            #print(f"[{now_time}] update server_user_status {ret1['message']}")
    except Exception as result:
        err_str=f"ERR! [{GetTime()}] update_server_user_status: {result}"
        print(err_str)
        #发送错误信息到指定频道
        debug_channel= await bot.fetch_public_channel(Debug_ch)
        await bot.send(debug_channel,err_str)


bot.run()