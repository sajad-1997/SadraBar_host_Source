from django.db import models
from django.conf import settings
from django_jalali.db import models as jmodels
from decimal import Decimal

from issuance.models.bijak import Bijak
from customers.models import Customer
from drivers.models import Driver


class AccountType(models.Model):
    TYPE_CHOICES = [
        ('customer', 'مشتری'),
        ('driver', 'راننده'),
        ('office', 'دفتر باربری'),
        ('announcer', 'اعلام‌کننده بار'),
        ('expense', 'هزینه'),
        ('revenue', 'درآمد'),
        ('bank', 'بانک/صندوق'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="نام نوع حساب")
    type_code = models.CharField(max_length=20, choices=TYPE_CHOICES, unique=True, verbose_name="کد نوع حساب")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounting_account_type'
        verbose_name = 'نوع حساب'
        verbose_name_plural = 'انواع حساب‌ها'
    
    def __str__(self):
        return self.name


class Account(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام حساب")
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE, related_name='accounts', verbose_name="نوع حساب")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='accounting_accounts', verbose_name="مشتری")
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='accounting_accounts', verbose_name="راننده")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='accounting_accounts', verbose_name="کاربر")
    code = models.CharField(max_length=50, unique=True, verbose_name="کد حساب")
    balance = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="موجودی فعلی")
    bank_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="نام بانک")
    account_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="شماره حساب")
    iban = models.CharField(max_length=50, blank=True, null=True, verbose_name="شماره شبا")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="تلفن")
    address = models.TextField(blank=True, null=True, verbose_name="آدرس")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='account_created')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        db_table = 'accounting_account'
        verbose_name = 'حساب'
        verbose_name_plural = 'حساب‌ها'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['account_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def recalculate_balance(self):
        from django.db.models import Sum
        credits = self.document_entries.filter(entry_type='credit').aggregate(Sum('amount'))['amount__sum'] or 0
        debits = self.document_entries.filter(entry_type='debit').aggregate(Sum('amount'))['amount__sum'] or 0
        self.balance = Decimal(credits) - Decimal(debits)
        self.save()
