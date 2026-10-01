from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_user_user_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='rolepermission',
            name='can_use_digital_stamp',
            field=models.BooleanField(default=False, verbose_name='اجازه چاپ بارنامه با مهر و امضای دیجیتال'),
        ),
    ]
