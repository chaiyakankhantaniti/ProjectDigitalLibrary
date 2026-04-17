from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library_app', '0007_update_learning_area_choices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='grade_level',
            field=models.CharField(
                choices=[
                    ('all', 'ทุกระดับ (ป.1-ป.6)'),
                    ('p1', 'ป.1'),
                    ('p2', 'ป.2'),
                    ('p3', 'ป.3'),
                    ('p4', 'ป.4'),
                    ('p5', 'ป.5'),
                    ('p6', 'ป.6'),
                ],
                default='p1',
                max_length=8,
                verbose_name='ระดับชั้นที่เหมาะสม',
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='grade_level',
            field=models.CharField(
                blank=True,
                choices=[
                    ('all', 'ทุกระดับ (ป.1-ป.6)'),
                    ('p1', 'ป.1'),
                    ('p2', 'ป.2'),
                    ('p3', 'ป.3'),
                    ('p4', 'ป.4'),
                    ('p5', 'ป.5'),
                    ('p6', 'ป.6'),
                ],
                default='',
                max_length=8,
                verbose_name='ระดับชั้น',
            ),
        ),
    ]
