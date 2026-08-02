from django.db import models
from django_jalali.db import models as jmodels
from django.conf import settings


class UserTrackingModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
        db_index=True
    )
    created_by_role = models.CharField(max_length=50, blank=True, null=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
        db_index=True
    )
    updated_by_role = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class Vehicle(UserTrackingModel):
    driver = models.ForeignKey(
        'drivers.Driver', 
        on_delete=models.CASCADE, 
        verbose_name="انتخاب راننده",
        db_index=True
    )
    type = models.CharField(
        max_length=50,
        verbose_name='نوع ناوگان',
        choices=[
            ('vant pikan kof saf', 'وانت پیکان کف صاف'),
            ('vant pikan mamoli', 'وانت پیکان معمولی'),
            ('vant pikan tak', 'وانت پیکان تک'),
            ('vant pikan doganeh', 'وانت پیکان دوگانه'),
            ('vant pikan doganeh factory', 'وانت پیکان دوگانه کارخانه'),
            ('vant pikan doganeh handmade', 'وانت پیکان دوگانه دستی'),

            ('vant nisan kof saf', 'وانت نیسان کف صاف'),
            ('vant nisan mamoli', 'وانت نیسان معمولی'),
            ('vant nisan tak', 'وانت نیسان تک'),
            ('vant nisan dizel', 'وانت نیسان دیزل'),
            ('vant nisan doganeh', 'وانت نیسان دوگانه'),
            ('vant nisan doganeh factory', 'وانت نیسان دوگانه کارخانه'),
            ('vant nisan doganeh handmade', 'وانت نیسان دوگانه دستی'),
            ('vant nisan kof mobli', 'وانت نیسان کف مبلی'),
            ('vant nisan mosaqaf', 'وانت نیسان مسقف'),

            ('arisan', 'وانت آریسان'),
            ('arisan 2', 'وانت آریسان ۲'),
            ('mazda', 'وانت مزدا'),
            ('zamyad', 'وانت زامیاد'),

            ('Bari chobi 7T', 'باری چوبی-۳ تا ۷ تن'),
            ('Bari chobi 10T', 'باری چوبی-۷ تا ۱۰ تن'),
            ('Bari chobi 13T', 'باری چوبی-۱۰ تا ۱۳ تن'),
            ('Bari chobi 17T', 'باری چوبی-۱۳ تا ۱۷ تن'),
            ('Bari chobi 20T', 'باری چوبی-۱۷ تا ۲۰ تن'),
            ('Bari chobi +20T', 'باری چوبی بالای ۲۰ تن'),

            ('Bari mosaqaf 6W-7T', 'مسقف ۶ چرخ-۴ تا ۷ تن'),
            ('Bari mosaqaf 6W-10T', 'مسقف ۶ چرخ-۷ تا ۱۰ تن'),
            ('Bari mosaqaf 6W-13T', 'مسقف ۶ چرخ-۱۰ تا ۱۳ تن'),

            ('khavar mosaqaf 7T', 'مسقف خاور-۴ تا ۷ تن'),

            ('Bari mosavi 6W-13T', 'معمولی ۶ چرخ-۱۰ تا ۱۳ تن'),

            ('Bari kafi 6W-7T', 'کفی ۶ چرخ-۴ تا ۷ تن'),
            ('Bari kafi 6W-10T', 'کفی ۶ چرخ-۷ تا ۱۰ تن'),
            ('Bari kafi 6W-13T', 'کفی ۶ چرخ-۱۰ تا ۱۳ تن'),
            ('Bari kafi 6W-17T', 'کفی ۶ چرخ-۱۳ تا ۱۷ تن'),
            ('Bari kafi 6W-20T', 'کفی ۶ چرخ-۱۷ تا ۲۰ تن'),
            ('Bari kafi 6W-20T+', 'کفی ۶ چرخ-بالای ۲۰ تن'),

            ('Bari kafi 18W', 'کفی ۱۸ چرخ'),
            
            ('Bari flezi 7T', 'باری فلزی-۳ تا ۷ تن'),
            ('Bari flezi 10T', 'باری فلزی-۷ تا ۱۰ تن'),
            ('Bari flezi 13T', 'باری فلزی-۱۰ تا ۱۳ تن'),
            ('Bari flezi 17T', 'باری فلزی-۱۳ تا ۱۷ تن'),
            ('Bari flezi 20T', 'باری فلزی-۱۷ تا ۲۰ تن'),
            ('Bari flezi +20T', 'باری فلزی بالای ۲۰ تن'),

            ('Bari otaqdar 4w', 'اتاقدار ۴ چرخ'),
            ('Bari otaqdar 10w', 'اتاقدار ۱۰ چرخ'),
            ('Bari otaqdar 6w-7T', 'اتاقدار ۶ چرخ-۴ تا ۷ تن'),
            ('Bari otaqdar 6w-20T', 'اتاقدار ۶ چرخ-۱۷ تا ۲۰ تن'),
            ('Bari otaqdar 808', 'اتاقدار ۸۰۸'),

            ('Bari baqaldar chadari 12w', 'بغلدار چادری ۱۲ چرخ'),
            ('Bari baqaldar chadari khavar', 'بغلدار چادری خاور'),

            ('Bari baqaldar mamoli 12w', 'بغلدار معمولی ۱۲ چرخ'),
            ('Bari baqaldar mamoli 6w', 'بغلدار معمولی ۶ چرخ'),
            ('Bari baqaldar mamoli 18w', 'بغلدار معمولی ۱۸ چرخ'),

            ('Bari baqaldar mamoli 6w-7T', 'بغلدار معمولی ۶ چرخ-۴ تا ۷ تن'),

            ('Bari kompreci 6w', 'کمپرسی ۶ چرخ-۴ تا ۷ تن'),

            ('Tak baqal bazsho', 'تک بغل بازشو'),

            ('eisozo', 'ایسوزو'),
            
            ('608', 'خاور ۶۰۸'),
            ('808', 'خاور ۸۰۸'),

            ('kamunet van', 'کامیونت-ون'),
            ('kamunet force', 'کامیونت فورس'),
            ('kamunet', 'کامیونت بالای ۴ تن'),
            ('kamunet felezi', 'کامیونت-باری فلزی'),

        ]
    )

    room_model = models.CharField(
        max_length=50,
        verbose_name='مدل اتاق ناوگان',
        choices=[
            ('Normal', 'معمولی'),
            ('flat_floor', 'کف صاف'),
            ('sofa_floor', 'کف مبلی'),
        ],
        default='Normal'
    )
    Animal_feed_license = models.CharField(
        max_length=6,
        null=True,
        blank=True,
        verbose_name='مجوز حمل خوراک دام',
        choices=[
            ('No', 'ندارد'),
            ('Yes', 'دارد'),
        ], 
        default='No'
    )
    veterinary_code = models.CharField(
        max_length=7, 
        blank=True, 
        null=True, 
        verbose_name="کد دامپزشکی"
    )
    license_plate_two_digit = models.CharField(max_length=2, verbose_name="دو رقم پلاک")
    license_plate_alphabet = models.CharField(max_length=1, verbose_name="الفبای پلاک")
    license_plate_three_digit = models.CharField(max_length=3, verbose_name="سه رقم پلاک")
    license_plate_series = models.CharField(max_length=2, verbose_name="سری پلاک")
    vehicle_smart_card = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name="هوشمند ناوگان"
    )
    insurance_policy_number = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="شماره بیمه نامه"
    )
    insurance_policy_expiry = jmodels.jDateField(
        blank=True, 
        null=True, 
        verbose_name="تاریخ اعتبار بیمه نامه"
    )

    def __str__(self):
        return f"{self.type} - {self.license_plate}"
    
    @property
    def license_plate(self):
        return f"{self.license_plate_two_digit}{self.license_plate_alphabet}{self.license_plate_three_digit}{self.license_plate_series}"

    class Meta:
        db_table = 'issuance_vehicle'
        verbose_name = 'ناوگان'
        verbose_name_plural = 'ناوگان‌ها'
        indexes = [
            models.Index(fields=['driver']),
            models.Index(fields=['type']),
            models.Index(fields=['vehicle_smart_card']),
        ]
