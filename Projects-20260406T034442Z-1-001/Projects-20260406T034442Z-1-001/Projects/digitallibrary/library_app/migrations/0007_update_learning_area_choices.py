from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library_app', '0006_book_learning_area_and_student_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='learning_area',
            field=models.CharField(
                choices=[
                    ('novel', 'นิยาย'),
                    ('comic', 'การ์ตูน'),
                    ('textbook', 'หนังสือเรียน'),
                    ('literature', 'วรรณคดี'),
                    ('psychology', 'จิตวิทยา'),
                    ('history_art_social', 'ประวัติศาสตร์ ศิลปะ และสังคม'),
                ],
                default='novel',
                max_length=32,
                verbose_name='หมวดหมู่หนังสือ',
            ),
        ),
    ]
