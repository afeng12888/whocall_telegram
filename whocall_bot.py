import logging
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# === 日志配置（无 emoji）===
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === 你的 Telegram Bot Token ===
TOKEN = os.getenv("TELEGRAM_TOKEN")

def analyze_phone_number(phone_text: str) -> str:
    try:
        number = phonenumbers.parse(phone_text, None)

        if not phonenumbers.is_possible_number(number):
            return "❌ 该号码格式不太可能存在。"
        if not phonenumbers.is_valid_number(number):
            return "❌ 该号码在现实中无效。"

        region = geocoder.description_for_number(number, "en")
        provider = carrier.name_for_number(number, "en")
        tz = timezone.time_zones_for_number(number)

        num_type = phonenumbers.number_type(number)
        type_dict = {
            phonenumbers.PhoneNumberType.FIXED_LINE: "固定电话",
            phonenumbers.PhoneNumberType.MOBILE: "移动电话",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "固定或移动电话",
            phonenumbers.PhoneNumberType.TOLL_FREE: "免费电话",
            phonenumbers.PhoneNumberType.PREMIUM_RATE: "收费电话",
            phonenumbers.PhoneNumberType.VOIP: "VoIP电话",
            phonenumbers.PhoneNumberType.UNKNOWN: "未知"
        }

        # ✅ 发送给用户的消息（保留 emoji）
        response = f"""✅ 号码有效！

🌍 地区：{region}
📡 运营商：{provider if provider else '未知'}
📞 号码类型：{type_dict.get(num_type, '未知')}
🕒 时区：{', '.join(tz) if tz else '未知'}

🔢 国际格式：{phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}
🔢 国家格式：{phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.NATIONAL)}
🔢 E.164格式：{phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)}
"""
        return response

    except Exception as e:
        logger.exception("号码解析失败")
        return "❌ 无法解析该号码，请确保输入正确，例如：+998901234567"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_input = update.message.text.strip()
        user_id = update.effective_user.id
        logger.info(f"收到用户 {user_id} 的输入: {user_input}")

        # 自动补全 "+"
        if user_input.isdigit() and not user_input.startswith("+"):
            user_input = "+" + user_input
            logger.debug(f"自动补全为：{user_input}")

        result = analyze_phone_number(user_input)
        await update.message.reply_text(result)

    except Exception as e:
        logger.exception("处理消息失败")
        await update.message.reply_text("❌ 处理请求时出错，请稍后再试。")

if __name__ == "__main__":
    logger.info("WhoCall Bot 启动中...")

    try:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        logger.info("WhoCall Bot 已启动，正在监听用户消息...")
        app.run_polling()
    except Exception:
        logger.exception("Bot 启动失败")
