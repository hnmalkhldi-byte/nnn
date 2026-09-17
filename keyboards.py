from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import CHANNEL_LINK, GROUP_LINK


def main_menu():
    kb = [
        [InlineKeyboardButton("📚 المكتبة", callback_data="menu_library")],
        [InlineKeyboardButton("✨ رشح لي (ذكاء اصطناعي)", callback_data="ai_recommend")],
        [InlineKeyboardButton("📈 الرائج هذا الأسبوع", callback_data="trending"),
         InlineKeyboardButton("🎯 مقترحة لك", callback_data="suggested")],
        [InlineKeyboardButton("🔥 الأكثر مشاهدة", callback_data="most_viewed"),
         InlineKeyboardButton("🆕 أحدث الروايات", callback_data="new_novels")],
        [InlineKeyboardButton("⭐ الأعلى تقييمًا", callback_data="top_rated"),
         InlineKeyboardButton("🏆 الأكثر تحميلاً", callback_data="most_downloaded")],
        [InlineKeyboardButton("🎲 رواية عشوائية", callback_data="random_novel"),
         InlineKeyboardButton("📖 مكتبتي", callback_data="my_library")],
        [InlineKeyboardButton("🔍 البحث", callback_data="search_start"),
         InlineKeyboardButton("❤️ المفضلة", callback_data="favorites")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
         InlineKeyboardButton("🔔 التنبيهات", callback_data="notifications")],
        [InlineKeyboardButton("📥 طلب رواية", callback_data="request_novel"),
         InlineKeyboardButton("⚠️ إبلاغ", callback_data="report")],
        [InlineKeyboardButton("📢 القناة الرئيسية", url=CHANNEL_LINK),
         InlineKeyboardButton("💬 المناقشة", url=GROUP_LINK)],
        [InlineKeyboardButton("🌐 الترجمة الذكية", callback_data="smart_translate"),
         InlineKeyboardButton("ℹ️ حول البوت", callback_data="about")],
    ]
    return InlineKeyboardMarkup(kb)


def library_menu():
    kb = [
        [InlineKeyboardButton("📖 الروايات", callback_data="lib_novels"),
         InlineKeyboardButton("🆕 المضافة حديثًا", callback_data="lib_recent")],
        [InlineKeyboardButton("❤️ المفضلة", callback_data="lib_favs"),
         InlineKeyboardButton("🔎 البحث", callback_data="lib_search")],
        [InlineKeyboardButton("🔙 عودة", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(kb)


def back_main_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة للقائمة الرئيسية", callback_data="back_main")]])


def back_library_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة للمكتبة", callback_data="menu_library")]])


def novels_list_keyboard(novels, prefix="novel"):
    kb = []
    for n in novels:
        kb.append([InlineKeyboardButton(f"📖 {n['title']}", callback_data=f"{prefix}_{n['id']}")])
    kb.append([InlineKeyboardButton("🔙 عودة", callback_data="menu_library")])
    return InlineKeyboardMarkup(kb)


def novel_page_keyboard(novel_id, volumes, is_fav=False):
    kb = []
    row = []
    for v in volumes:
        row.append(InlineKeyboardButton(
            f"📕 المجلد {v['volume_number']}",
            callback_data=f"vol_{novel_id}_{v['volume_number']}"
        ))
        if len(row) == 3:
            kb.append(row)
            row = []
    if row:
        kb.append(row)

    fav_text = "💔 إزالة من المفضلة" if is_fav else "❤️ إضافة للمفضلة"
    kb.append([InlineKeyboardButton(fav_text, callback_data=f"fav_{novel_id}")])
    kb.append([
        InlineKeyboardButton("🔙 عودة للمكتبة", callback_data="menu_library"),
        InlineKeyboardButton("🏠 الرئيسية", callback_data="back_main"),
    ])
    return InlineKeyboardMarkup(kb)


def volume_view_keyboard(novel_id):
    kb = [
        [InlineKeyboardButton("↩️ رجوع للرواية", callback_data=f"novel_{novel_id}")],
        [InlineKeyboardButton("🏠 الرئيسية", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(kb)


def admin_menu():
    kb = [
        [InlineKeyboardButton("➕ إضافة رواية", callback_data="adm_add_novel")],
        [InlineKeyboardButton("📚 إدارة المكتبة", callback_data="adm_manage")],
        [InlineKeyboardButton("✏️ تعديل رواية", callback_data="adm_edit")],
        [InlineKeyboardButton("🗑 حذف رواية", callback_data="adm_delete")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="adm_stats")],
        [InlineKeyboardButton("📢 إرسال إعلان", callback_data="adm_broadcast")],
        [InlineKeyboardButton("🏠 الرئيسية", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(kb)


def admin_novel_actions(novel_id):
    kb = [
        [InlineKeyboardButton("➕ إضافة مجلد", callback_data=f"adm_addvol_{novel_id}")],
        [InlineKeyboardButton("✏️ تعديل", callback_data=f"],
adm_editnov_{novel_id}")        [InlineKeyboardButton("🗑 حذف الرواية", callback_data=f"adm_delnov_{novel_id}")],
        [InlineKeyboardButton("📕 عرض المجلدات", callback_data=f"adm_showvols_{novel_id}")],
        [InlineKeyboardButton("🔙 عودة", callback_data="adm_manage")],
    ]
    return InlineKeyboardMarkup(kb)


def admin_edit_fields(novel_id):
    kb = [
        [InlineKeyboardButton("📝 الاسم", callback_data=f"editf_{novel_id}_title")],
        [InlineKeyboardButton("✍️ المؤلف", callback_data=f"editf_{novel_id}_author")],
        [InlineKeyboardButton("🌐 اللغة", callback_data=f"editf_{novel_id}_language")],
        [InlineKeyboardButton("📝 الوصف", callback_data=f"editf_{novel_id}_description")],
        [InlineKeyboardButton("📚 التصنيف", callback_data=f"editf_{novel_id}_category")],
        [InlineKeyboardButton("🔙 عودة", callback_data=f"adm_novel_{novel_id}")],
    ]
    return InlineKeyboardMarkup(kb)


def confirm_delete_keyboard(novel_id):
    kb = [
        [InlineKeyboardButton("✅ نعم، احذف", callback_data=f"confirm_del_{novel_id}")],
        [InlineKeyboardButton("❌ إلغاء", callback_data=f"adm_novel_{novel_id}")],
    ]
    return InlineKeyboardMarkup(kb)
