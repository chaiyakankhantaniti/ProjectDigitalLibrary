from django.db import migrations


def rename_user_id_to_borrower_id(apps, schema_editor):
    conn = schema_editor.connection
    if conn.vendor != 'sqlite':
        return
    with conn.cursor() as cursor:
        cursor.execute("PRAGMA table_info(library_app_borrow)")
        cols = {row[1] for row in cursor.fetchall()}
    if 'borrower_id' in cols or 'user_id' not in cols:
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('ALTER TABLE library_app_borrow RENAME COLUMN user_id TO borrower_id;')


def rename_borrower_id_to_user_id(apps, schema_editor):
    conn = schema_editor.connection
    if conn.vendor != 'sqlite':
        return
    with conn.cursor() as cursor:
        cursor.execute("PRAGMA table_info(library_app_borrow)")
        cols = {row[1] for row in cursor.fetchall()}
    if 'user_id' in cols or 'borrower_id' not in cols:
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('ALTER TABLE library_app_borrow RENAME COLUMN borrower_id TO user_id;')


class Migration(migrations.Migration):

    dependencies = [
        ('library_app', '0003_book_ebook_and_teacher_group'),
    ]

    operations = [
        migrations.RunPython(rename_user_id_to_borrower_id, rename_borrower_id_to_user_id),
    ]
