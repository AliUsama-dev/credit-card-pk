# Generated migration for adding country field to Bank model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0005_creditcard_peekaboo_association_type_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bank',
            name='country',
            field=models.CharField(choices=[('PK', 'Pakistan'), ('TT', 'Trinidad & Tobago'), ('US', 'United States'), ('CA', 'Canada'), ('UK', 'United Kingdom')], db_index=True, default='PK', max_length=2),
        ),
    ]

