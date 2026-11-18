# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026

import asyncio
import random

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from anony import app, config, db

# ========== قائمة النصوص ==========
SELECTIONS = [
    "لو قالوا لك تناول صنف واحد فقط من الطعام لمدة شهر، ماذا تختار؟",
    "لو كان لديك قوة خارقة، ماذا ستكون؟",
    "ما هو أكثر شيء يجعلك سعيداً؟",
    "لو كنت حيواناً، ماذا ستكون؟",
    "ما هو حلمك الأكبر في الحياة؟",
    "لو كنت تستطيع السفر عبر الزمن، لأي عصر ستذهب؟",
    "ما هي أكثر مهارة تتمنى أن تتقنها؟",
    "لو كنت مليونيراً ليوم واحد، ماذا ستفعل؟",
    "ما هو أكثر كتاب أثر في حياتك؟",
    "لو كان لديك ثلاث أمنيات، ماذا ستتمنى؟",
    "ما هي أغلى هدية تلقيتها في حياتك؟",
    "لو كنت رئيساً لبلدك، ما أول قرار ستتخذه؟",
    "ما هو أكثر مكان تتمنى زيارته؟",
    "لو أردت تغيير اسمك، ماذا ستختار؟",
    "ما هو أكثر فيلم أثر فيك؟",
    "لو كنت تستطيع التحدث بلغة جديدة، أي لغة ستختار؟",
    "ما هي أكثر عادة تريد التخلص منها؟",
    "لو كان بإمكانك مقابلة أي شخصية تاريخية، من ستختار؟",
    "ما هو أكثر اختراع تتمنى لو كان موجوداً؟",
    "لو كنت رياضي محترف، أي رياضة ستختار؟",
    "ما هي أغنية تسمعها عندما تكون حزيناً؟",
    "لو كنت تطير، إلى أين ستتجه أولاً؟",
    "ما هو أكثر طعام تحبه ولا تستطيع الاستغناء عنه؟",
    "لو كنت نجماً، أي نجم ستكون؟",
    "ما هو أكثر شيء تخاف منه؟",
    "لو كنت أستاذاً، أي مادة ستدرس؟",
    "ما هي أجمل ذكرى في طفولتك؟",
    "لو كنت تستطيع الاختفاء، أين ستذهب؟",
    "ما هو أكثر شيء يلهمك في الحياة؟",
    "لو كنت شخصية كرتونية، من ستكون؟",
    "أوصف نفسك بكلمة؟",
    "ما هي أهم صفة تبحث عنها في صديق؟",
    "لو كنت في جزيرة مهجورة، ما ثلاثة أشياء ستأخذها معك؟",
    "ما هو أكثر شيء تندم عليه في حياتك؟",
    "لو كنت تستطيع تغيير شيء واحد في العالم، ماذا سيكون؟",
]

# ========== متغيرات ==========
biof = []
chatt = []
chat = []


@app.on_message(filters.command(["كت", "تويت"], ""), group=8836)
async def bottttt(client, message):
    bar = random.choice(SELECTIONS)
    cid = message.chat.id
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("دفع 5⭐", url=f"https://t.me/{client.me.username}?start=call_{cid}")]]
    )
    await message.reply_text(text=bar, reply_markup=reply_markup)


# ========== البايو ==========
@app.on_message(filters.command(["قفل البايو", "تعطيل البايو"], ""), group=509)
async def iddlock(client, message):
    get = await client.get_chat_member(message.chat.id, message.from_user.id)
    if get.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        if message.chat.id in biof:
            return await message.reply_text("البايو معطل بالفعل في هذه المجموعة")
        biof.append(message.chat.id)
        return await message.reply_text("تم تعطيل البايو بنجاح")
    return await message.reply_text("هذا الأمر يخص المشرفين فقط")


@app.on_message(filters.command(["فتح البايو", "تفعيل البايو"], ""), group=678)
async def biopen(client, message):
    get = await client.get_chat_member(message.chat.id, message.from_user.id)
    if get.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        if message.chat.id not in biof:
            return await message.reply_text("البايو مفعل بالفعل في هذه المجموعة")
        biof.remove(message.chat.id)
        return await message.reply_text("تم فتح البايو بنجاح")
    return await message.reply_text("هذا الأمر يخص المشرفين فقط")


@app.on_message(filters.command(["بايو", "البايو"], ""), group=444)
async def biio(client, message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        user_id = message.from_user.id
    if message.chat.id in biof:
        return await message.reply_text("البايو معطل في هذه المجموعة")

    try:
        nq = await client.get_chat(user_id)
        bio = nq.bio
        if bio:
            await message.reply_text(f"📝 بايو المستخدم:\n\n{bio}")
        else:
            await message.reply_text("هذا المستخدم ليس لديه بايو")
    except Exception as e:
        await message.reply_text(f"حدث خطأ: {str(e)}")


# ========== الاستيكر ==========
@app.on_message(filters.command(["استك"], prefixes=""), group=1282)
async def sticker_id(_, message: Message):
    reply = message.reply_to_message
    if not reply:
        return await message.reply("عزيزي قم برد علي الاستيكر")
    if not reply.sticker:
        return await message.reply("عزيزي قم برد علي الاستيكر")
    await message.reply_text(
        f"<code>{reply.sticker.file_id}</code>\n\n<b>عزيزي هذا هو ايدي الاستيكر المطلوب:</b>"
    )


# ========== النداء ==========
@app.on_message(filters.text & filters.group, group=77677668)
async def aarr(c, msg):
    if msg.text in ["تفعيل نداء", "تفعيل النداء", "فتح النداء"]:
        if msg.chat.id in chatt:
            return await msg.reply_text("<b>نداء مفعله من قبل\n༄</b>")
        chatt.append(msg.chat.id)
        return await msg.reply_text("تم تفعيل نداء بنجاح\n༄")
    elif msg.text in ["تعطيل نداء", "تعطيل النداء", "قفل النداء"]:
        if msg.chat.id in chatt:
            chatt.remove(msg.chat.id)
            return await msg.reply_text("تم تعطيل نداء بنجاح\n༄")
        return await msg.reply_text("نداء معطله من قبل\n༄")


async def ndaaa():
    while True:
        await asyncio.sleep(1200)
        for i in list(chatt):
            members = []
            try:
                async for member in app.get_chat_members(i):
                    if not member.user.is_bot:
                        members.append(member)
            except Exception as e:
                print(f"Error retr: {e}")
                continue

            if members:
                random_member = random.choice(members)
                random_member_mention = (
                    f"<a href=\"tg://user?id={random_member.user.id}\">{random_member.user.first_name}</a>"
                )
                random_message = [
                    f"⇜متجي : {random_member_mention}",
                    f"⇜• يـا قمـري ❤️‍🔥 : {random_member_mention}",
                    f"⇜ولك فينك يعمري 😂 : {random_member_mention}",
                    f"⇜حبيبي وينك : {random_member_mention}",
                    f"⇜انت منيح : {random_member_mention}",
                    f"⇜ولله اشتقتلك اكتير : {random_member_mention}",
                    f"⇜حياااااااتي : {random_member_mention}",
                    f"⇜اخي بدك تشارك معانا : {random_member_mention}",
                    f"⇜يعمررررري انا : {random_member_mention}",
                    f"⇜حبــي الـڪ ادمان 💋😍 : {random_member_mention}",
                    f"⇜اوووه حبيبي هنا : {random_member_mention}",
                    f"⇜استغفر الله : {random_member_mention}",
                    f"⇜واحد الله : {random_member_mention}",
                    f"⇜اذكر الله : {random_member_mention}",
                    f"⇜يسمر يسمر : {random_member_mention}",
                    f"⇜حبيبي وينك : {random_member_mention}",
                    f"⇜حب الحب : {random_member_mention}",
                    f"⇜تحبنــي ؟ 🙊🫶 : {random_member_mention}",
                    f"⇜عادوغري انا مشتاق : {random_member_mention}",
                    f"⇜مكنتش متخيل انك تسبيني : {random_member_mention}",
                    f"⇜مكنتش متخيلي انا القمر هنا : {random_member_mention}",
                    f"⇜مشتاقيـن حــب وينڪ 😥🍓 : {random_member_mention}",
                    f"اموت انا واعيد السنه : {random_member_mention}",
                    f"⇜عامل ايه يجمييل : {random_member_mention}",
                    f"⇜قلب قلبي : {random_member_mention}",
                    f"⇜فينك يروحي : {random_member_mention}",
                    f"⇜ولك يروحي : {random_member_mention}",
                    f"⇜شوو هدا الجمال : {random_member_mention}",
                    f"⇜خطفت قلبي : {random_member_mention}",
                    f"⇜ههـلاوات ڪبد حياتـي 😊 : {random_member_mention}",
                    f"⇜Hello : {random_member_mention}",
                    f"⇜انت شخه 😛 : {random_member_mention}",
                    f"⇜اخاف انا كدا يعني 🥱: {random_member_mention}",
                    f"⇜اضحك يبختك اعم🙂 : {random_member_mention}",
                    f"⇜فينك يحب شارك معانا : {random_member_mention}",
                    f"⇜اللي مصبرني هنا انت : {random_member_mention}",
                    f"⇜تع يمز نكلم شويه : {random_member_mention}",
                    f"⇜يخرااشي عالقمر : {random_member_mention}",
                    f"⇜منين يودي عالفين يجميل : {random_member_mention}",
                    f"⇜براحه عالجروب مش بتاعنا : {random_member_mention}",
                    f"⇜ماتجي ونجيب مليجي : {random_member_mention}",
                    f"⇜يلا نروح ونجيب ممدوح : {random_member_mention}",
                    f"⇜اوع الفحت لتقع تحت : {random_member_mention}",
                    f"⇜ما تمسي علينا : {random_member_mention}",
                ]
                try:
                    await app.send_message(i, random.choice(random_message))
                except Exception as e:
                    print(f"Error sending message: {e}")


# ========== الأذكار ==========
@app.on_message(filters.group, group=768)
async def azkarr(c, msg):
    if msg.text == "تفعيل الاذكار":
        if msg.chat.id in chat:
            return await msg.reply_text("<b>الاذكار مفعله من قبل\n༄</b>")
        chat.append(msg.chat.id)
        return await msg.reply_text("تم تفعيل الاذكار بنجاح\n༄")
    elif msg.text == "تعطيل الاذكار":
        if msg.chat.id in chat:
            chat.remove(msg.chat.id)
            return await msg.reply_text("تم تعطيل الاذكار بنجاح\n༄")
        return await msg.reply_text("الاذكار معطله من قبل\n༄")


async def azkar():
    azkarl = [
        "لا إِلَهَ إِلا أَنتَ سُبْحَانَكَ إِنِّي كُنتُ مِنَ الظَّالِمِينَ🌸",
        "اللَّهُمَّ أَعِنِّي عَلَى ذِكْرِكَ , وَشُكْرِكَ , وَحُسْنِ عِبَادَتِكَ🎈💞",
        "استغفر الله العظيم وأتوبُ إليه 🌹",
        "سبحان الله وبحمده سبحان الله العظيم🌸",
        "أشهد أنْ لا إله إلا الله وحده لا شريك له، وأشهد أن محمدًا عبده ورسوله🌺",
        "اللهم إنك عفو تُحب العفو فاعفُ عنّا 🌿🌹",
        "رَبِّ اشْرَحْ لِي صَدْرِي وَيَسِّرْ لِي أَمْرِي ﴾",
        "اللهم اشفي كل مريض يتألم ولا يعلم بحاله إلا أنت",
        "يارب دُعاء القلب انت تسمعه فأستجب لهُ.",
        "اللهم صلِ وسلم على نبينآ محمد ❥⇣",
        "لا اله الا الله سيدنا محمد رسول الله🌿💜",
        "مُجرد ثانية تنفعِك : أستغفُرالله العظيِم وأتوب إليّه.",
        "اللهم اكفني بحلالك عن حرامك، وأغنني بفضلك عمن سواك",
        "اللهم يا رحمن يا حنان يا منان استودعك يا رب قلبي فلا تجعل فيه أحدا سواك",
        "اللهمَّ اغفر لوالدي وارحمهما كما ربّياني صغيراً",
        "اللهم لا تخزني يوم القيامة",
        "اللهم إني أسألك الفردوس أعلى الجنة",
        "استغفر الله العظيم وأتوبُ إليه.",
        "قال ﷺ : ”حَيْثُمَا كُنْتُمْ فَصَلُّوا عَلَيَّ، فَإِنَّ صَلَاتَكُمْ تَبْلُغُنِي“.",
        "اللهم قلبًا سليمًا عفيفًا تقيًا نقيًا يخشاك سرًا وعلانية🤍🌱",
    ]
    while True:
        await asyncio.sleep(1000)
        for i in list(chat):
            try:
                await app.send_message(i, random.choice(azkarl))
            except Exception:
                pass