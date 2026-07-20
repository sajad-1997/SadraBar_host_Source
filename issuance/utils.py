import jdatetime
from num2words import num2words


def num_to_word_rial(value):
    try:
        number = int(value)
        return num2words(number, lang='fa') + " ریال"
    except:
        return ""


def persian_to_english_numbers(input_str):
    """
    تبدیل اعداد فارسی به انگلیسی
    مثال: '۱۴۰۳/۰۶/۰۱' → '1403/06/01'
    """
    if not input_str:
        return ''
    persian_nums = '۰۱۲۳۴۵۶۷۸۹'
    english_nums = '0123456789'
    translation_table = str.maketrans(''.join(persian_nums), ''.join(english_nums))
    return input_str.translate(translation_table)


def persian_to_gregorian(jalali_str):
    """
    تبدیل رشته Jalali به datetime.date میلادی
    ورودی: '۱۴۰۳/۰۶/۰۱'
    خروجی: datetime.date
    """
    if not jalali_str:
        return None
    jalali_str = persian_to_english_numbers(jalali_str)
    try:
        year, month, day = map(int, jalali_str.split('/'))
        g_date = jdatetime.date(year, month, day).togregorian()
        return g_date
    except ValueError:
        return None


def gregorian_to_persian(date_obj):
    """
    تبدیل تاریخ میلادی به شمسی - نسخه اصلاح شده
    """
    if not date_obj:
        return ''

    try:
        print(f"🔍 gregorian_to_persian INPUT: {date_obj}, type: {type(date_obj)}")

        # اگر از نوع jdatetime.date است (شمسی در پایتون)
        if isinstance(date_obj, jdatetime.date):
            # بررسی: اگر سال خیلی کوچک است (کمتر از 1300)، احتمالاً تاریخ میلادی است که اشتباه تفسیر شده
            if date_obj.year < 1300:
                print(f"⚠️  WARNING: Year {date_obj.year} is too small. Might be Gregorian mis-converted.")
                # سعی می‌کنیم فرض کنیم این تاریخ میلادی است
                try:
                    # فرض می‌کنیم سال میلادی است (مثلاً 1996)
                    # اما jdatetime آن را به عنوان 751 شمسی خوانده
                    # باید برگردیم به میلادی اصلی
                    g_date = date_obj.togregorian()
                    # حالا دوباره به شمسی تبدیل می‌کنیم
                    j_date = jdatetime.date.fromgregorian(date=g_date)
                except:
                    j_date = date_obj
            else:
                j_date = date_obj
        else:
            # اگر datetime است، به date تبدیل کن
            if hasattr(date_obj, 'date'):
                date_obj = date_obj.date()
            j_date = jdatetime.date.fromgregorian(date=date_obj)

        print(f"🔍 Jalali date: {j_date}")

        # تبدیل اعداد به فارسی
        persian_nums = '۰۱۲۳۴۵۶۷۸۹'

        year_str = str(j_date.year)
        month_str = f"{j_date.month:02d}"
        day_str = f"{j_date.day:02d}"

        # تبدیل تک تک ارقام
        year_fa = ''.join(persian_nums[int(digit)] for digit in year_str)
        month_fa = ''.join(persian_nums[int(digit)] for digit in month_str)
        day_fa = ''.join(persian_nums[int(digit)] for digit in day_str)

        result = f"{year_fa}/{month_fa}/{day_fa}"
        print(f"🔍 FINAL RESULT: {result}")
        return result

    except Exception as e:
        print(f"❌ ERROR in gregorian_to_persian: {e}")
        return str(date_obj)
