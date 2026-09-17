import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

import config
import database as dbm
from keyboards import (
    main_menu, library_menu, back_main_button, back_library_button,
    novels_list_keyboard, novel_page_keyboard, volume_view_keyboard,
    admin_menu, admin_novel_actions, admin_edit_fields, confirm_delete_keyboard
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== Flask للسيرفر الوهمي ==================
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

# ================== حالات المحادثة ==================
(
    A_TITLE, A_AUTHOR, A_LANG, A_DESC, A_CATEGORY,
    A_VOL_NUM, A_VOL_FILE,
    E_VALUE,
    RQ_WAIT, RP_WAIT,
    S_WAIT, B_WAIT,
    ADDVOL_NUM, ADDVOL_FILE
) = range(14)


def is_admin(uid):
    return uid == config.ADMIN_ID


def escape_md(text):
    if not text:
        return ""
    for ch in ["_", "*", "[", "]", "`"]:
        text = text.replace(ch, f"\\{ch}")
    return text


# ================== أوامر عامة ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    dbm.add_user(user.id, user.username or "", user.first_name or "")

    text = (
        "📚 **بوت الروايات الآسيوية**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "مرحباً بك في أضخم مكتبة للروايات الآسيوية\n\n"
        "❝ اختر من القائمة أدناه للبدء ❞"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu(), parse_mode="Markdown")


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ هذا الأمر غير متاح.")
        return
    await update.message.reply_text(
        "⚙️ **لوحة الإدارة**\nاختر ما تريد:",
        reply_markup=admin_menu(),
        parse_mode="Markdown"
    )


# ================== معالج الأزرار الرئيسي ==================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = q.from_user.id

    if data == "back_main":
        await start(update, context)
        return

    if data == "menu_library":
        await q.edit_message_text(
            "📚 **المكتبة**\nاختر ما تريد:",
            reply_markup=library_menu(),
            parse_mode="Markdown"
        )
        return

    if data == "lib_novels":
        novels = dbm.get_all_novels()
        if not novels:
            await q.edit_message_text("📭 لا توجد روايات مضافة بعد.", reply_markup=back_library_button())
            return
        await q.edit_message_text(
            f"📖 **الروايات** ({len(novels)} رواية)\nاختر رواية:",
            reply_markup=novels_list_keyboard(novels),
            parse_mode="Markdown"
        )
        return

    if data in ("lib_recent", "new_novels"):
        novels = dbm.get_new_novels(15)
        if not novels:
            await q.edit_message_text("📭 لا توجد روايات.", reply_markup=back_library_button())
            return
        await q.edit_message_text(
            "🆕 **أحدث الروايات:**",
            reply_markup=novels_list_keyboard(novels),
            parse_mode="Markdown"
        )
        return

    if data == "most_viewed":
        novels = dbm.get_most_viewed(15)
        await q.edit_message_text(
            "🔥 **الأكثر مشاهدة:**",
            reply_markup=novels_list_keyboard(novels) if novels else back_main_button(),
            parse_mode="Markdown"
        )
        return

    if data == "top_rated":
        novels = dbm.get_top_rated(15)
        await q.edit_message_text(
            "⭐ **الأعلى تقييمًا:**",
            reply_markup=novels_list_keyboard(novels) if novels else back_main_button(),
            parse_mode="Markdown"
        )
        return

    if data == "most_downloaded":
        novels = dbm.get_most_downloaded(15)
        await q.edit_message_text(
            "🏆 **الأكثر تحميلاً:**",
            reply_markup=novels_list_keyboard(novels) if novels else back_main_button(),
            parse_mode="Markdown"
        )
        return

    if data == "trending":
        novels = dbm.get_most_viewed(10)
        await q.edit_message_text(
            "📈 **الرائج هذا الأسبوع:**",
            reply_markup=novels_list_keyboard(novels) if novels else back_main_button(),
            parse_mode="Markdown"
        )
        return

    if data == "random_novel":
        n = dbm.get_random_novel()
        if not n:
            await q.edit_message_text("📭 لا توجد روايات.", reply_markup=back_main_button())
            return
        await show_novel(q, n["id"])
        return

    if data == "suggested":
        novels = dbm.get_top_rated(10)
        await q.edit_message_text(
            "🎯 **مقترحة لك:**",
            reply_markup=novels_list_keyboard(novels) if novels else back_main_button(),
            parse_mode="Markdown"
        )
        return

    if data == "ai_recommend":
        await q.edit_message_text(
            "✨ **رشح لي**\n\n"
            "الميزة قيد التطوير. حالياً يمكنك تصفح:\n"
            "• الأكثر مشاهدة\n• الأعلى تقييماً\n• المضافة حديثاً",
            reply_markup=back_main_button(),
            parse_mode="Markdown"
        )
        return

    if data == "smart_translate":
        await q.edit_message_text(
            "🌐 خدمة الترجمة الذكية قيد التطوير.",
            reply_markup=back_main_button()
        )
        return

    if data == "about":
        await q.edit_message_text(
            "ℹ️ **حول البوت**\n\n"
            "بوت مكتبة الروايات الآسيوية\n"
            "يحتوي على العديد من الروايات بصيغة PDF",
            reply_markup=back_main_button(),
            parse_mode="Markdown"
        )
        return

    if data == "notifications":
        await q.edit_message_text(
            "🔔 **التنبيهات**\n\n"
            "لتفعيل التنبيهات عند نزول مجلد جديد،\n"
            "أضف الرواية للمفضلة ❤️",
            reply_markup=back_main_button(),
            parse_mode="Markdown"
        )
        return

    if data.startswith("novel_"):
        nid = int(data.split("_")[1])
        await show_novel(q, nid)
        return

    if data.startswith("vol_"):
        parts = data.split("_")
        nid, vnum = int(parts[1]), int(parts[2])
        vol = dbm.get_volume_by_number(nid, vnum)
        n = dbm.get_novel(nid)
        if not vol or not n:
            await q.edit_message_text("❌ المجلد غير موجود.", reply_markup=back_main_button())
            return
        dbm.inc_downloads(nid)
        dbm.mark_read(uid, nid)
        caption = f"📕 **{escape_md(n['title'])}** — المجلد {vnum}"
        try:
            await q.message.reply_document(
                document=vol["pdf_file_id"],
                caption=caption,
                parse_mode="Markdown",
                reply_markup=volume_view_keyboard(nid)
            )
            await q.answer("✅ تم إرسال الملف")
        except Exception as e:
            await q.answer(f"⚠️ خطأ في الإرسال: {e}", show_alert=True)
        return

    if data.startswith("fav_"):
        nid = int(data.split("_")[1])
        state = dbm.toggle_favorite(uid, nid)
        msg = "✅ أُضيفت للمفضلة" if state else "💔 أُزيلت من المفضلة"
        await q.answer(msg)
        await show_novel(q, nid)
        return

    if data in ("favorites", "lib_favs"):
        favs = dbm.get_favorites(uid)
        if not favs:
            await q.edit_message_text(
                "❤️ **المفضلة فارغة**\nأضف روايات لتراها هنا.",
                reply_markup=back_main_button(),
                parse_mode="Markdown"
            )
            return
        await q.edit_message_text(
            f"❤️ **مفضلاتك** ({len(favs)})",
            reply_markup=novels_list_keyboard(favs),
            parse_mode="Markdown"
        )
        return

    if data == "my_library":
        favs = dbm.get_favorites(uid)
        if not favs:
            await q.edit_message_text("📖 مكتبتك فارغة.", reply_markup=back_main_button())
            return
        await q.edit_message_text(
            "📖 **مكتبتك:**",
            reply_markup=novels_list_keyboard(favs),
            parse_mode="Markdown"
        )
        return

    if data == "my_stats":
        s = dbm.get_user_stats(uid)
        await q.edit_message_text(
            f"📊 **إحصائياتك**\n\n"
            f"❤️ المفضلة: {s['favorites']}\n"
            f"📖 روايات قرأتها: {s['reads']}",
            reply_markup=back_main_button(),
            parse_mode="Markdown"
        )
        return

    if data.startswith("adm_") or data.startswith("editf_") or data.startswith("confirm_del_"):
        if not is_admin(uid):
            await q.answer("⛔ لا تملك صلاحية.", show_alert=True)
            return
        await handle_admin_buttons(q, context, data)
        return


async def show_novel(q, nid):
    n = dbm.get_novel(nid)
    if not n:
        await q.edit_message_text("❌ الرواية غير موجودة.", reply_markup=back_main_button())
        return
    dbm.inc_views(nid)
    vols = dbm.get_volumes(nid)
    is_fav = dbm.is_favorite(q.from_user.id, nid)

    text = (
        f"📖 **{escape_md(n['title'])}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✍️ المؤلف: {escape_md(n['author'] or 'غير محدد')}\n"
        f"🌐 اللغة: {escape_md(n['language'] or 'غير محدد')}\n"
        f"📚 عدد المجلدات: {len(vols)}\n"
        f"📂 التصنيف: {escape_md(n['category'] or 'عام')}\n"
        f"👁 المشاهدات: {n['views']+1}\n"
        f"⬇️ التحميلات: {n['downloads']}\n\n"
        f"📝 **الوصف:**\n{escape_md(n['description'] or 'لا يوجد وصف')}"
    )
    await q.edit_message_text(
        text,
        reply_markup=novel_page_keyboard(nid, vols, is_fav),
        parse_mode="Markdown"
    )


async def handle_admin_buttons(q, context, data):
    if data == "adm_add_novel":
        await q.edit_message_text(
            "➕ **إضافة رواية جديدة**\n\n"
            "أرسل اسم الرواية:\n"
            "_(اكتب /cancel للإلغاء)_",
            parse_mode="Markdown"
        )
        return A_TITLE

    if data == "adm_manage":
        novels = dbm.get_all_novels()
        if not novels:
            await q.edit_message_text("📭 لا توجد روايات.", reply_markup=admin_menu())
            return
        await q.edit_message_text(
            f"📚 **إدارة المكتبة** ({len(novels)} رواية)\nاختر رواية:",
            reply_markup=novels_list_keyboard(novels, prefix="adm_novel"),
            parse_mode="Markdown"
        )
        return

    if data.startswith("adm_novel_"):
        nid = int(data.split("_")[2])
        n = dbm.get_novel(nid)
        if not n:
            await q.edit_message_text("❌ غير موجود.", reply_markup=admin_menu())
            return
        await q.edit_message_text(
            f"⚙️ **إدارة:** {escape_md(n['title'])}\n\nاختر عملية:",
            reply_markup=admin_novel_actions(nid),
            parse_mode="Markdown"
        )

    if data.startswith("adm_addvol_"):
        nid = int(data.split("_")[2])
        context.user_data["add_vol_nid"] = nid
        await q.edit_message_text(
            "➕ **إضافة مجلد جديد**\n\n"
            "أرسل رقم المجلد (مثلاً: 1):\n"
            "_(اكتب /cancel للإلغاء)_"
        )
        return ADDVOL_NUM

    if data.startswith("adm_editnov_"):
        nid = int(data.split("_")[2])
        await q.edit_message_text(
            "✏️ اختر الحقل الذي تريد تعديله:",
            reply_markup=admin_edit_fields(nid)
        )

    if data.startswith("editf_"):
        parts = data.split("_")
        nid = int(parts[1])
        field = parts[2]
        context.user_data["edit_nid"] = nid
        context.user_data["edit_field"] = field
        labels = {
            "title": "الاسم", "author": "المؤلف", "language": "اللغة",
            "description": "الوصف", "category": "التصنيف"
        }
        await q.edit_message_text(
            f"✏️ أرسل القيمة الجديدة لـ **{labels.get(field, field)}**:\n"
            f"_(اكتب /cancel للإلغاء)_",
            parse_mode="Markdown"
        )
        return E_VALUE

    if data.startswith("adm_delnov_"):
        nid = int(data.split("_")[2])
        n = dbm.get_novel(nid)
        if not n:
            await q.edit_message_text("❌ غير موجود.", reply_markup=admin_menu())
            return
        await q.edit_message_text(
            f"⚠️ **تأكيد الحذف**\n\n"
            f"هل أنت متأكد من حذف رواية **{escape_md(n['title'])}** "
            f"مع جميع مجلداتها؟",
            reply_markup=confirm_delete_keyboard(nid),
            parse_mode="Markdown"
        )

    if data.startswith("confirm_del_"):
        nid = int(data.split("_")[2])
        dbm.delete_novel(nid)
        await q.edit_message_text("✅ تم حذف الرواية بنجاح.", reply_markup=admin_menu())

    if data.startswith("adm_showvols_"):
        nid = int(data.split("_")[2])
        vols = dbm.get_volumes(nid)
        if not vols:
            await q.edit_message_text("📭 لا توجد مجلدات.", reply_markup=admin_novel_actions(nid))
            return
        text = "📕 **المجلدات:**\n\n"
        for v in vols:
            text += f"• المجلد {v['volume_number']}\n"
        await q.edit_message_text(text, reply_markup=admin_novel_actions(nid), parse_mode="Markdown")

    if data == "adm_edit":
        novels = dbm.get_all_novels()
        if not novels:
            await q.edit_message_text("📭 لا توجد روايات.", reply_markup=admin_menu())
            return
        await q.edit_message_text(
            "✏️ اختر رواية لتعديلها:",
            reply_markup=novels_list_keyboard(novels, prefix="adm_editnov")
        )

    if data == "adm_delete":
        novels = dbm.get_all_novels()
        if not novels:
            await q.edit_message_text("📭 لا توجد روايات.", reply_markup=admin_menu())
            return
        await q.edit_message_text(
            "🗑 اختر رواية لحذفها:",
            reply_markup=novels_list_keyboard(novels, prefix="adm_delnov")
        )

    if data == "adm_stats":
        stats = (
            f"📊 **إحصائيات البوت**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 المستخدمون: {dbm.count_users()}\n"
            f"📚 الروايات: {len(dbm.get_all_novels())}\n"
            f"📥 الطلبات: {dbm.count_requests()}\n"
            f"⚠️ البلاغات: {dbm.count_reports()}"
        )
        await q.edit_message_text(stats, reply_markup=admin_menu(), parse_mode="Markdown")

    if data == "adm_broadcast":
        await q.edit_message_text(
            "📢 **إرسال إعلان**\n\n"
            "أرسل الرسالة التي تريد نشرها لجميع المستخدمين:\n"
            "_(اكتب /cancel للإلغاء)_"
        )
        return B_WAIT


# ================== حوارات الإدارة ==================
async def add_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["n_title"] = update.message.text
    await update.message.reply_text("✍️ أرسل اسم المؤلف:")
    return A_AUTHOR


async def add_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["n_author"] = update.message.text
    await update.message.reply_text("🌐 أرسل اللغة:")
    return A_LANG


async def add_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["n_lang"] = update.message.text
    await update.message.reply_text("📝 أرسل وصف الرواية:")
    return A_DESC


async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["n_desc"] = update.message.text
    await update.message.reply_text("📂 أرسل التصنيف:")
    return A_CATEGORY


async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data
    nid = dbm.add_novel(d["n_title"], d["n_author"], d["n_lang"], d["n_desc"], update.message.text)
    await update.message.reply_text(
        f"✅ تمت إضافة الرواية (ID: {nid})\n\n"
        f"أرسل رقم المجلد الأول (مثلاً: 1)\n"
        f"أو /skip للإنهاء."
    )
    context.user_data["new_nid"] = nid
    return A_VOL_NUM


async def add_vol_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt == "/skip":
        await update.message.reply_text("✅ تم الانتهاء.", reply_markup=admin_menu())
        return ConversationHandler.END
    try:
        num = int(txt)
    except ValueError:
        await update.message.reply_text("❌ أرسل رقماً صحيحاً أو /skip")
        return A_VOL_NUM
    context.user_data["n_volnum"] = num
    await update.message.reply_text("📄 أرسل ملف PDF:")
    return A_VOL_FILE


async def add_vol_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        await update.message.reply_text("❌ أرسل ملف PDF من فضلك.")
        return A_VOL_FILE
    fid = update.message.document.file_id
    nid = context.user_data["new_nid"]
    dbm.add_volume(nid, context.user_data["n_volnum"], fid)
    await update.message.reply_text(
        f"✅ تم حفظ المجلد {context.user_data['n_volnum']}.\n\n"
        f"أرسل رقم المجلد التالي، أو /skip للإنهاء."
    )
    return A_VOL_NUM


async def addvol_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        num = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ أرسل رقماً صحيحاً.")
        return ADDVOL_NUM
    context.user_data["addvol_num"] = num
    await update.message.reply_text("📄 أرسل ملف PDF:")
    return ADDVOL_FILE


async def addvol_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        await update.message.reply_text("❌ أرسل ملف PDF.")
        return ADDVOL_FILE
    nid = context.user_data["add_vol_nid"]
    num = context.user_data["addvol_num"]
    dbm.add_volume(nid, num, update.message.document.file_id)
    await update.message.reply_text(f"✅ تم إضافة المجلد {num} بنجاح.", reply_markup=admin_menu())
    return ConversationHandler.END


async def edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nid = context.user_data["edit_nid"]
    field = context.user_data["edit_field"]
    dbm.update_novel_field(nid, field, update.message.text)
    await update.message.reply_text("✅ تم التعديل بنجاح.", reply_markup=admin_menu())
    return ConversationHandler.END


async def broadcast_wait(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    users = dbm.get_all_users()
    sent = 0
    await update.message.reply_text(f"⏳ جاري الإرسال إلى {len(users)} مستخدم...")
    for uid in users:
        try:
            await context.bot.send_message(uid, f"📢 **إعلان:**\n\n{msg}", parse_mode="Markdown")
            sent += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ تم الإرسال إلى {sent}/{len(users)}.", reply_markup=admin_menu())
    return ConversationHandler.END


async def request_novel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "📥 **طلب رواية**\n\nأرسل اسم الرواية:\n_(اكتب /cancel للإلغاء)_",
        parse_mode="Markdown"
    )
    return RQ_WAIT


async def request_novel_wait(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    content = update.message.text
    dbm.add_request(user.id, content)
    try:
        await context.bot.send_message(
            config.ADMIN_ID,
            f"📥 **طلب رواية جديد**\n\n"
            f"👤 من: {user.first_name} (@{user.username or 'بدون'})\n"
            f"🆔 ID: `{user.id}`\n\n"
            f"📖 الطلب: {content}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"خطأ في إرسال الطلب: {e}")
    await update.message.reply_text("✅ تم إرسال طلبك للإدارة.", reply_markup=main_menu())
    return ConversationHandler.END


async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "⚠️ **إبلاغ**\n\nأرسل تفاصيل المشكلة:\n_(اكتب /cancel للإلغاء)_",
        parse_mode="Markdown"
    )
    return RP_WAIT


async def report_wait(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    content = update.message.text
    dbm.add_report(user.id, content)
    try:
        await context.bot.send_message(
            config.ADMIN_ID,
            f"⚠️ **بلاغ جديد**\n\n"
            f"👤 من: {user.first_name} (@{user.username or 'بدون'})\n"
            f"🆔 ID: `{user.id}`\n\n"
            f"📝 التفاصيل:\n{content}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"خطأ في إرسال البلاغ: {e}")
    await update.message.reply_text("✅ تم إرسال البلاغ للإدارة.", reply_markup=main_menu())
    return ConversationHandler.END


async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "🔎 **البحث**\n\nأرسل اسم الرواية أو المؤلف:\n_(اكتب /cancel للإلغاء)_",
        parse_mode="Markdown"
    )
    return S_WAIT


async def search_wait(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.message.text
    results = dbm.search_novels(q)
    if not results:
        await update.message.reply_text("❌ لم يتم العثور على نتائج.", reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text(
        f"✅ تم العثور على {len(results)} نتيجة:",
        reply_markup=novels_list_keyboard(results),
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم الإلغاء.", reply_markup=main_menu())
    return ConversationHandler.END


# ================== التشغيل ==================
def main():
    dbm.init_db()

    # تشغيل Flask في الخلفية
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("Flask web server started.")

    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CallbackQueryHandler(buttons))

    add_novel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_admin_buttons, pattern="^adm_add_novel$")],
        states={
            A_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)],
            A_AUTHOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_author)],
            A_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_lang)],
            A_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
            A_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category)],
            A_VOL_NUM: [MessageHandler(filters.TEXT, add_vol_num)],
            A_VOL_FILE: [MessageHandler(filters.Document.PDF, add_vol_file)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    add_vol_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_admin_buttons, pattern="^adm_addvol_")],
        states={
            ADDVOL_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, addvol_num)],
            ADDVOL_FILE: [MessageHandler(filters.Document.PDF, addvol_file)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_admin_buttons, pattern="^editf_")],
        states={
            E_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_admin_buttons, pattern="^adm_broadcast$")],
        states={
            B_WAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_wait)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    request_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_novel_start, pattern="^request_novel$")],
        states={
            RQ_WAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_novel_wait)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    report_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(report_start, pattern="^report$")],
        states={
            RP_WAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_wait)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    search_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(search_start, pattern="^(search_start|lib_search)$")],
        states={
            S_WAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_wait)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    app.add_handler(add_novel_conv)
    app.add_handler(add_vol_conv)
    app.add_handler(edit_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(request_conv)
    app.add_handler(report_conv)
    app.add_handler(search_conv)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))

    logger.info("Bot started.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
