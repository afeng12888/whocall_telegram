import os
import logging
from dotenv import load_dotenv
from phonenumbers import carrier, geocoder, timezone, parse, is_possible_number, is_valid_number, number_type, PhoneNumberType
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 加载环境变量
load_dotenv()

# 从环境变量中获取 Telegram Bot Token
TOKEN = os.getenv("TELEGRAM_TOKEN")

# 设置日志记录
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

def analyze_phone_number(phone_text: str) -> str:
    try:
        number = parse(phone_text, None)

        if not is_possible_number(number):
            return "❌ 该号码格式不太可能存在。"
        if not is_valid_number(number):
            return "❌ 该号码在现实中无效。"

        region = geocoder.description_for_number(number, "en")
        provider = carrier.name_for_number(number, "en")
        tz = timezone.time_zones_for_number(number)

        num_type = number_type(number)
        type_dict = {
            PhoneNumberType.FIXED_LINE: "固定电话",
            PhoneNumberType.MOBILE: "移动电话",
            PhoneNumberType.FIXED_LINE_OR_MOBILE: "固定或移动电话",
            PhoneNumberType.TOLL_FREE: "免费电话",
            PhoneNumberType.PREMIUM_RATE: "收费电话",
            PhoneNumberType.VOIP: "VoIP电话",
            PhoneNumberType.UNKNOWN: "未知"
        }

        response = f"""✅ 号码有效！

🌍 地区：{region}
📡 运营商：{provider if provider else '未知'}
📞 号码类型：{type_dict.get(num_type, '未知')}
🕒 时区：{', '.join(tz) if tz else '未知'}

🔢 国际格式：{format_number(number, PhoneNumberFormat.INTERNATIONAL)}
🔢 国家格式：{format_number(number, PhoneNumberFormat.NATIONAL)}
🔢 E.164格式：{format_number(number, PhoneNumberFormat.E164)}
"""
        return response

    except Exception as e:
        logging.error(f"解析错误: {str(e)}")
        return f"❌ 无法解析该号码，请确保输入正确，例如：+998901234567\n错误信息：{str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    # 自动补全 "+" 前缀（如用户输入 "998901234567"）
    if user_input.isdigit() and not user_input.startswith("+"):
        user_input = "+" + user_input

    logging.info(f"处理用户输入: {user_input}")
    
    result = analyze_phone_number(user_input)
    await update.message.reply_text(result)

if __name__ == "__main__":
    if not TOKEN:
        logging.error("未设置 TELEGRAM_TOKEN 环境变量")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("🤖 WhoCall Bot 已启动，等待消息...")
    app.run_polling()
