import nextcord, re, httpx, certifi
from dotenv import load_dotenv
load_dotenv()
from nextcord.ext import commands
import config
OWNERS = config.OWNERS
intents = nextcord.Intents.all()
bot = commands.Bot(help_command=None, intents=intents)
import json
from nextcord.ui import TextInput, Modal, View
import requests
import os
import datetime
from server import keep_alive

os.chdir(os.path.dirname(os.path.abspath(__file__)))

class topupModal(nextcord.ui.Modal):

  def __init__(self):
    super().__init__(title='เติมเงิน | Hope Shop', timeout=None, custom_id='topup-modal')
    self.link = TextInput(
        label='🧧 ลิ้งค์ซองอั่งเปา',
        placeholder='https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx',
        style=nextcord.TextInputStyle.short,
        required=True)
    self.add_item(self.link)

  async def callback(self, interaction: nextcord.Interaction):
    ########################################################################################
    try:
        link = str(self.link.value).replace(' ', '')


        data = {
            'phone': "0630102037",
            'gift' : link
        }

        res = requests.post("https://api.mystrix2.me/truemoney", data=data)

        response_data = res.json()

        if 'redeemResponse' in response_data:
            status = response_data['redeemResponse'].get('status', {})
            msg = status.get('message', 'เกิดข้อผิดพลาด')
            code = status.get('code', '')
            embed = nextcord.Embed(title="❌ เติมเงินไม่สำเร็จ", description=f"⚠️ {msg}", color=nextcord.Color.red())
            if code:
                embed.set_footer(text=f"Code: {code}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if res.status_code == 200:

            voucher = response_data.get('data', {}).get('voucher', {})
            amount = voucher.get('amount_baht', 0)
            amount = float(amount)

            if amount < 10:
                embed = nextcord.Embed(title="❌ เติมเงินไม่สำเร็จ", description="⚠️ ยอดเงินขั้นต่ำ 10 บาท", color=nextcord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            ########################################################################################
            message = await interaction.response.send_message(embed=config.loading,ephemeral=True)


            with open('database/users.json', 'r', encoding="utf-8") as file:
                                        user_data = json.load(file)

            user_id = str(interaction.user.id)
            print(float(amount))
            point = float(amount) - float(amount)* 0 
            if user_id in user_data:
                                        print("เข้าสู่ระบบสำเร็จ")
                                        new_point = float(user_data[user_id]['point']) + float(point)
                                        user_data[user_id]['point'] = str(new_point)
                                        new_point = float(user_data[user_id]['all-point']) + float(point)
                                        user_data[user_id]['all-point'] = str(new_point)
            else:
                                        print("ไม่พบผู้ใช้ในระบบ")

                                        user_data[user_id] = {
                                            "userId": int(user_id),
                                            "point": str(0 + float(point)),
                                            "all-point": str(0 + float(point)),
                                            "historybuy": [],
                                            "buyrole": [],
                                            "buymarket": []
                                        }
                                        print("สร้างผู้ใช้ใหม่เรียบร้อยแล้ว")




            with open('database/users.json', 'w', encoding="utf-8") as file:
                    json.dump(user_data, file, indent=4)
            embed = nextcord.Embed(description=f'✅﹒**เติมเงินสำเร็จ จำนวน {point} บาท**',
                                color=nextcord.Color.green())
            await message.edit(content=None, embed=embed)
            if interaction.user.avatar:
                embed.set_thumbnail(url=interaction.user.avatar.url)

        else:




            print(f"Request failed with status code: {res.status_code}")
            embed = nextcord.Embed(title="❌ เติมเงินไม่สำเร็จ", description=f"⚠️ เกิดข้อผิดพลาดจากระบบ (Status: {res.status_code})", color=nextcord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
          await interaction.response.send_message(embed=nextcord.Embed(title="กรุณากรอกซองให้ถูกต้อง", color=nextcord.Color.red()), ephemeral=True)

class sellroleView(nextcord.ui.View):

  def __init__(self, message: nextcord.Message, value: str):
    super().__init__(timeout=None)
    self.message = message
    self.value = value

  @nextcord.ui.button(label='✅ ยืนยันสั่งซื้อ',
                      custom_id='already',
                      style=nextcord.ButtonStyle.primary,
                      row=1)
  async def already(self, button: nextcord.Button,
                    interaction: nextcord.Interaction):
    roleJSON = json.load(open('./database/roles.json', 'r', encoding='utf-8'))
    userJSON = json.load(open('./database/users.json', 'r', encoding='utf-8'))
    if (str(interaction.user.id) not in userJSON):
      embed = nextcord.Embed(description='💳﹒กรุณาเติมเงินเพื่อเปิดบัญชี',
                             color=nextcord.Color.red())
    else:
      if int(float(userJSON[str(interaction.user.id)]['point'])) >= roleJSON[self.value]['price']:
        userJSON[str(interaction.user.id)]['point'] = str(float(userJSON[str(interaction.user.id)]['point']) - roleJSON[self.value]['price'])
        userJSON[str(interaction.user.id)]['buyrole'].append({
            "role": {
                "roleId": self.value,
                "time": str(datetime.datetime.now())
            }
        })
        json.dump(userJSON,
                  open('./database/users.json', 'w', encoding='utf-8'),
                  indent=4,
                  ensure_ascii=False)
        if ('package' in self.value):
          for roleId in roleJSON[self.value]['roleIds']:
            try:
              await interaction.user.add_roles(
                  nextcord.utils.get(interaction.user.guild.roles, id=roleId))
            except:
              pass
          embed = nextcord.Embed(
              description=
              f'✅﹒ซื้อยศสำเร็จ ได้รับ {roleJSON[self.value]["name"]}',
              color=nextcord.Color.green())
          await self.message.edit(embed=embed, view=None, content=None)
        else:
            with open('database/users.json', encoding="utf-8") as f:
                            data_dict = json.load(f)
            transactions = data_dict[str(interaction.user.id)]["point"]
            embed = nextcord.Embed(
                                                        title="📲 รายละเอียดการสั่งซื้อสินค้า",
                                                        description=(
                                                            f"```👤 คุณ {interaction.user.name}\n"
                                                            f"🛒 ซื้อสินค้า: {roleJSON[self.value]['name']}\n"
                                                            f"✅ สถานะการสั่งซื้อ : สั่งซื้อสำเร็จ\n"
                                                            f"💴 เงินลดลง : {roleJSON[self.value]['price']}\n"
                                                            f"💸 เงินคงเหลือ : {transactions}\n"
                                                            "```"
                                                        ),
                                                        color=nextcord.Color.green()
                                                    )

            if interaction.user.avatar:
                                                embed.set_thumbnail(url=interaction.user.avatar.url)

            role = nextcord.utils.get(interaction.user.guild.roles,
                                        id=roleJSON[self.value]['roleId'])
            
            if role:
                await interaction.user.add_roles(role)
            embed.add_field(name="⭐ รายลดเอียดการสั่งซื้อ", value="✅ เก็บหลักฐานไว้สำหรับ การกู้คืนสินค้า กับแอดมิน \n(กู้คืนติดต่อ <@984128015543984179>)")
            await self.message.edit(embed=embed, view=None, content=None)
            await interaction.user.send(embed=embed)
      else:
        embed = nextcord.Embed(
            description=f'💸﹒ยอดเงินไม่เพียงพอ ขาดอีก ({roleJSON[str(self.value)]["price"] - float(userJSON[str(interaction.user.id)]["point"])})',color=nextcord.Color.red())
    return await self.message.edit(embed=embed, view=None, content=None)

  @nextcord.ui.button(label='❌ ยกเลือกการสั่งซื้อ',
                      custom_id='cancel',
                      style=nextcord.ButtonStyle.red,
                      row=1)
  async def cancel(self, button: nextcord.Button,
                   interaction: nextcord.Interaction):
    return await self.message.edit(content='ยกเลิกการการสำเร็จแล้ว',embed=None,view=None)

class sellroleselectmain(nextcord.ui.Select):
  def __init__(self):
    options = []
    roleJSON = json.load(open('./database/roles.json', 'r', encoding='utf-8'))
    for role in roleJSON:
      options.append(
          nextcord.SelectOption(label=roleJSON[role]['name'],
                                description=roleJSON[role]['description'],
                                value=role,
                                emoji=nextcord.PartialEmoji.from_str(roleJSON[role]['emoji'].strip()) if roleJSON[role]['emoji'] else None))
    super().__init__(custom_id='select-role',
                     placeholder='[ 🎭 เลือกยศและบทบาท ]',
                     min_values=1,
                     max_values=1,
                     options=options,
                     row=2)

  async def callback(self, interaction: nextcord.Interaction):
    message = await interaction.response.send_message(
        content='[SELECT] กำลังตรวจสอบ', ephemeral=True)
    selected = self.values[0]
    if ('package' in selected):
      roleJSON = json.load(open('./database/roles.json', 'r',
                                encoding='utf-8'))
      embed = nextcord.Embed()
      embed.description = f'''
E {roleJSON[selected]['name']}**
'''
      await message.edit(content=None,
                         embed=embed,
                         view=sellroleView(message=message, value=selected))
    else:
      
      roleJSON = json.load(open('./database/roles.json', 'r',
                                encoding='utf-8'))
      embed=nextcord.Embed(title=roleJSON[selected]['title'], description=f"```{roleJSON[selected]['embeddes']}```" , color=nextcord.Color.green()).set_image(url=roleJSON[selected]['image']).set_footer(icon_url=config.emojidev, text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
      await message.edit(content="🪙 รายละเอียดสินค้า",
                         embed=embed,
                         view=sellroleView(message=message, value=selected))


class buyrole(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(sellroleselectmain())

        
class menu(nextcord.ui.Select):
    def __init__(self):

        options = [
            nextcord.SelectOption(label="ซื้อยศ / BUY ROLE", description="เลือกซื้อยศต่างๆ", emoji="📸"),
            nextcord.SelectOption(label="ซื้อสคลิปบอท / BUY SRC", description="เลือกซื้อสคริปต์", emoji="💻"),
            nextcord.SelectOption(label="ล้างการเลือก", description="Clear Selection", emoji="❌"),
        ]

        super().__init__(custom_id='menu',
                        placeholder='[ 📸 Hope Shop Menu ]',
                        min_values=1,
                        max_values=1,
                        options=options,
                        row=1)

    async def callback(self, interaction: nextcord.Interaction):
        selected_values = self.values
        if "ซื้อยศ / BUY ROLE" in selected_values:
             await interaction.response.send_message(view=buyrole() , ephemeral=True)
        elif "ซื้อสคลิปบอท / BUY SRC"  in selected_values:
             await interaction.response.send_message(view=buybot() , ephemeral=True)
        else:
             pass


class buybot(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(sellmarketsellprogram())
class sellmarketsellprogram(nextcord.ui.Select):
  def __init__(self):
    options = []
    IDJSON = json.load(open('./database/market.json', 'r', encoding='utf-8'))
    for role in IDJSON:
      options.append(
          nextcord.SelectOption(label=IDJSON[role]['name'],
                                description=IDJSON[role]['description'],
                                value=role,
                                emoji=nextcord.PartialEmoji.from_str(IDJSON[role]['emoji'].strip()) if IDJSON[role]['emoji'] else None))
    super().__init__(custom_id='sellmarketui',
                     placeholder='[  เลือกสินค้าที่ต้องการ ]',
                     min_values=1,
                     max_values=1,
                     options=options,
                     row=3)

  async def callback(self, interaction: nextcord.Interaction):
    message = await interaction.response.send_message(
        content='[SELECT] กำลังตรวจสอบ', ephemeral=True)
    selected = self.values[0]
    if ('package' in selected):
      IDJSON = json.load(open('./database/market.json', 'r',
                                encoding='utf-8'))
      embed = nextcord.Embed()
      embed.description = f'''
E {IDJSON[selected]['name']}**
'''
      await message.edit(content=None,
                         embed=embed,
                         view=sellmarket(message=message, value=selected))
    else:
      
      IDJSON = json.load(open('./database/market.json', 'r',
                                encoding='utf-8'))
      embed=nextcord.Embed(title=IDJSON[selected]['title'], description=f"```{IDJSON[selected]['embeddes']}```" , color=nextcord.Color.green()).set_image(url=IDJSON[selected]['image']).set_footer(icon_url=config.emojidev, text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
      await message.edit(content="🪙 รายละเอียดสินค้า",
                         embed=embed,
                         view=sellmarket(message=message, value=selected))  
      
class sellmarket(nextcord.ui.View):
  def __init__(self, message: nextcord.Message, value: str):
    super().__init__(timeout=None)
    self.message = message
    self.value = value

  @nextcord.ui.button(label='✅ ยืนยันสั่งซื้อ',
                      custom_id='already',
                      style=nextcord.ButtonStyle.primary,
                      row=3)
  async def already(self, button: nextcord.Button,
                    interaction: nextcord.Interaction):
    IDJSON = json.load(open('./database/market.json', 'r', encoding='utf-8'))
    userJSON = json.load(open('./database/users.json', 'r', encoding='utf-8'))
    if (str(interaction.user.id) not in userJSON):
      embed = nextcord.Embed(description='💳﹒กรุณาเติมเงินเพื่อเปิดบัญชี',
                             color=nextcord.Color.red())
    else:
      if int(float(userJSON[str(interaction.user.id)]['point'])) >= IDJSON[self.value]['price']:
        userJSON[str(interaction.user.id)]['point'] = str(float(userJSON[str(interaction.user.id)]['point']) - IDJSON[self.value]['price'])
        userJSON[str(interaction.user.id)]['buymarket'].append({
            "market": {
                "name": IDJSON[self.value]['name'],
                "time": str(datetime.datetime.now()),
                "code" : IDJSON[self.value]['code']
            }
        })
        json.dump(userJSON,
                  open('./database/users.json', 'w', encoding='utf-8'),
                  indent=4,
                  ensure_ascii=False)
        if ('package' in self.value):
          for roleId in IDJSON[self.value]['roleIds']:
            try:
              await interaction.user.add_roles(
                  nextcord.utils.get(interaction.user.guild.roles, id=roleId))
            except:
              pass
          
          # เพิ่มยศลูกค้า (ถ้ามี config)
          if config.cusrole != 0:
              try:
                  role = nextcord.utils.get(interaction.user.guild.roles, id=config.cusrole)
                  if role:
                      await interaction.user.add_roles(role)
              except:
                  pass

          channelLog = bot.get_channel(config.logbuy)
          transactions = userJSON[str(interaction.user.id)]['point'] # ดึงยอดเงินคงเหลือ
          if (channelLog):
            embed = nextcord.Embed(
                                                        title="📲 รายละเอียดการสั่งซื้อสินค้า",
                                                        description=(
                                                            f"```👤 คุณ {interaction.user.name}\n"
                                                            f"🛒 ซื้อสินค้า: {IDJSON[self.value]['name']}\n"
                                                            f"✅ สถานะการสั่งซื้อ : สั่งซื้อสำเร็จ\n"
                                                            f"💴 เงินลดลง : {IDJSON[self.value]['price']}\n"
                                                            f"💸 เงินคงเหลือ : {transactions}\n"
                                                            "```"
                                                        ),
                                                        color=nextcord.Color.green()
                                                    )

            await channelLog.send(embed=embed)
          embed = nextcord.Embed(
              description=
              f'✅﹒สั่งซื้อสำเร็จ ได้รับ {IDJSON[self.value]["name"]}',
              color=nextcord.Color.green())
          await self.message.edit(embed=embed, view=None, content=None)
        else:
            channelLog = bot.get_channel(config.logbuy)
            with open('database/users.json', encoding="utf-8") as f:
                            data_dict = json.load(f)
            transactions = data_dict[str(interaction.user.id)]["point"]
            
            # สร้าง Embed ก่อนใช้งาน
            embed = nextcord.Embed(
                                title="📲 รายละเอียดการสั่งซื้อสินค้า",
                                description=(
                                    f"```👤 คุณ {interaction.user.name}\n"
                                    f"🛒 ซื้อสินค้า: {IDJSON[self.value]['name']}\n"
                                    f"✅ สถานะการสั่งซื้อ : สั่งซื้อสำเร็จ\n"
                                    f"💴 เงินลดลง : {IDJSON[self.value]['price']}\n"
                                    f"💸 เงินคงเหลือ : {transactions}\n"
                                    "```"
                                ),
                                color=nextcord.Color.green()
                            )
            if interaction.user.avatar:
                                                embed.set_thumbnail(url=interaction.user.avatar.url)
            if channelLog: # เช็คว่ามีห้อง Log หรือไม่
                await channelLog.send(embed=embed)
            
            embed.add_field(name="⭐ รายละเอียดการสั่งซื้อ", value="✅ เก็บหลักฐานไว้สำหรับ การกู้คืนสินค้า กับแอดมิน \n(กู้คืนติดต่อ <@984128015543984179>)",inline=False)
            embed.add_field(name="⭐ รับสินค้า", value=f" กดตรงนี้เพื่อรับโค้ด : [คลิกตรงนี้!!]({IDJSON[self.value]['code']}) ```{IDJSON[self.value]['code']}```",inline=False)
            await self.message.edit(embed=embed, view=None, content=None)
            await interaction.user.send(embed=embed)
      else:
        embed = nextcord.Embed(
            description=f'💸﹒ยอดเงินไม่เพียงพอ ขาดอีก ({IDJSON[str(self.value)]["price"] - float(userJSON[str(interaction.user.id)]["point"])})',color=nextcord.Color.red())
    return await self.message.edit(embed=embed, view=None, content=None)

  @nextcord.ui.button(label='❌ ยกเลือกการสั่งซื้อ',
                      custom_id='cancel',
                      style=nextcord.ButtonStyle.red,
                      row=3)
  async def cancel(self, button: nextcord.Button,
                   interaction: nextcord.Interaction):
    return await self.message.edit(content='ยกเลิกการการสำเร็จแล้ว',embed=None,view=None)


@bot.event
async def on_ready():
    print(f'BOT NAME : {bot.user}')
    bot.add_view(mainui())



class mainui(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(menu())

    @nextcord.ui.button(label='เติมเงิน',
                        emoji="🧧",
                        custom_id='t1',
                        style=nextcord.ButtonStyle.blurple,
                        row=2)
    async def t1(self, button: nextcord.Button,
                        interaction: nextcord.Interaction):
            await interaction.response.send_modal(topupModal())
    @nextcord.ui.button(label='เช็คเงิน',
                        emoji="",
                        custom_id='t2',
                        style=nextcord.ButtonStyle.blurple,
                        row=2)
    async def t2(self, button: nextcord.Button,
                        interaction: nextcord.Interaction):
        userJSON = json.load(open('./database/users.json', 'r', encoding='utf-8'))
        if (str(interaction.user.id) not in userJSON):
            embed = nextcord.Embed(title="❌ ผิดพลาด", description='⚠️ ไม่พบข้อมูลบัญชี\nกรุณา **เติมเงิน** เพื่อเปิดบัญชีกับทางร้าน',
                                color=nextcord.Color.red())
            if interaction.user.avatar:
                embed.set_thumbnail(url=interaction.user.avatar.url)
        else:
            embed = nextcord.Embed(
                title="💳 ข้อมูลบัญชี | Hope Shop",
                description=
                f' สมาชิก: {interaction.user.mention}\n💰 ยอดเงินคงเหลือ: **{userJSON[str(interaction.user.id)]["point"]}** บาท',
                color=nextcord.Color.green())
            embed.set_footer(text="Hope Shop - แหล่งรวมของถ่ายรูป คุ้มจัดๆ", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            if interaction.user.avatar:
                embed.set_thumbnail(url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=True)
    @nextcord.ui.button(label='รีวิว',
                            emoji="⭐",
                            custom_id='a1',
                            style=nextcord.ButtonStyle.primary,
                            row=3)
    async def a1(self, button: nextcord.Button,
                            interaction: nextcord.Interaction):
            thank_you_message = "ขอบคุณสำหรับการรีวิว!"

            await interaction.response.send_message(thank_you_message, ephemeral=True)
            user_id = str(interaction.user.id)
            os.makedirs("Review", exist_ok=True) # สร้างโฟลเดอร์ Review ถ้ายังไม่มี
            user_review_file = f"Review/{user_id}.json"
            if not os.path.exists(user_review_file):
                    with open(user_review_file, "w", encoding='utf-8') as f:
                        json.dump({"reviewed": True}, f)
                    reviewlog = config.review_log
                    channel = bot.get_channel(reviewlog)
                    log_embed = nextcord.Embed(title="> THANK FOR REVIEW   ", description=f"__รายละเอียดการรีวิว__ \n\n <:botsever24:1184867502124179586> ขอบคุณผู้ใช้งาน : {interaction.user.mention} \n\n <:botsever24:1184867502124179586>         **THANK YOU** <:botsever24:1184867502124179586> ", color=0x7289da)
                    if interaction.user.avatar:
                            log_embed.set_thumbnail(url=interaction.user.avatar.url)
                    else :
                            log_embed.set_thumbnail(url=None)
                    if channel:
                        await channel.send(embed=log_embed)
            else:
                    await interaction.followup.send("คุณรีวิวไปแล้วครับ!", ephemeral=True)

@bot.slash_command( description="ติดตั้งได้หมด")
async def setup(interaction: nextcord.Interaction):

            embed=nextcord.Embed(title=f"📸 Hope Shop | แหล่งรวมของถ่ายรูป คุ้มจัดๆ", color=nextcord.Color.purple())
    

            des = '''```ansi
[2;35m[1;35m📸 Hope Shop ยินดีต้อนรับ[0m[2;35m[0m
[2;36mแหล่งรวมของถ่ายรูป ราคาคุ้มค่า สบายกระเป๋า[0m
[2;37m[2;34m---------------------------------------[0m[2;37m[0m
[2;33m✨ ระบบอัตโนมัติ 24 ชั่วโมง[0m
[2;32m💳 เติมเงินผ่านซองอั่งเปา TrueMoney[0m
[2;34m🛒 สินค้าคุณภาพ ส่งทันทีหลังซื้อ[0m
```'''
            embed.add_field(name="", value=des, inline=False)
            
            des_info = '''> 📸 **สินค้าถ่ายรูปสวยๆ**
> 💸 **ราคาสุดคุ้ม**
> ⚡ **บริการรวดเร็วทันใจ**'''
            embed.add_field(name="`✨` รายละเอียดร้านค้า", value=des_info, inline=True)

            des_how = '''> 1. กดปุ่ม **เติมเงิน** ด้านล่าง
> 2. ใส่ลิ้งค์ซองอั่งเปา
> 3. เลือกซื้อสินค้าที่ต้องการ'''
            embed.add_field(name="`🟢` วิธีการใช้งาน", value=des_how, inline=True)
            
            
            
            embed.set_image(url="https://media.discordapp.net/attachments/1096081392296796210/1102603621192966184/truewallet_01.jpg?ex=69460ae4&is=6944b964&hm=f2940f6d489233c1e86638f0684f0b81a326c0c3b534d10d84f26b8ea45d3457&=&format=webp")
            embed.set_footer(text="Hope Shop System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
            rent = await interaction.channel.send(embed=embed, view=mainui())


keep_alive()
bot.run(config.TOKEN)