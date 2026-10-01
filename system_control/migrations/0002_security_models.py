# Generated migration for security monitoring models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('system_control', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('login_success', 'Login Success'), ('login_failure', 'Login Failure'), ('password_change', 'Password Change'), ('permission_denied', 'Permission Denied'), ('suspicious_activity', 'Suspicious Activity'), ('rate_limit_exceeded', 'Rate Limit Exceeded'), ('module_access_denied', 'Module Access Denied'), ('quota_exceeded', 'Quota Exceeded'), ('unusual_location', 'Unusual Location'), ('brute_force_attempt', 'Brute Force Attempt')], db_index=True, max_length=50)),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='low', max_length=20)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('path', models.CharField(blank=True, max_length=500)),
                ('details', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='security_events', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Security Event',
                'verbose_name_plural': 'Security Events',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='LoginAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(db_index=True, max_length=150)),
                ('ip_address', models.GenericIPAddressField(db_index=True)),
                ('success', models.BooleanField(default=False)),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'verbose_name': 'Login Attempt',
                'verbose_name_plural': 'Login Attempts',
                'ordering': ('-created_at',),
            },
        ),
        migrations.AddIndex(
            model_name='securityevent',
            index=models.Index(fields=['event_type', 'created_at'], name='system_control_event_type_idx'),
        ),
        migrations.AddIndex(
            model_name='securityevent',
            index=models.Index(fields=['severity', 'created_at'], name='system_control_severity_idx'),
        ),
        migrations.AddIndex(
            model_name='securityevent',
            index=models.Index(fields=['user', 'created_at'], name='system_control_user_idx'),
        ),
        migrations.AddIndex(
            model_name='loginattempt',
            index=models.Index(fields=['username', 'created_at'], name='system_control_login_username_idx'),
        ),
        migrations.AddIndex(
            model_name='loginattempt',
            index=models.Index(fields=['ip_address', 'created_at'], name='system_control_login_ip_idx'),
        ),
    ]
