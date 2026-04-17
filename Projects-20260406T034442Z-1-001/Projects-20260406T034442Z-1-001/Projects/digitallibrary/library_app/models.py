from django.conf import settings
from django.db import models


class GradeLevel(models.TextChoices):
    ALL = 'all', 'ทุกระดับ (ป.1-ป.6)'
    P1 = 'p1', 'ป.1'
    P2 = 'p2', 'ป.2'
    P3 = 'p3', 'ป.3'
    P4 = 'p4', 'ป.4'
    P5 = 'p5', 'ป.5'
    P6 = 'p6', 'ป.6'


class LearningArea(models.TextChoices):
    NOVEL = 'novel', 'นิยาย'
    COMIC = 'comic', 'การ์ตูน'
    TEXTBOOK = 'textbook', 'หนังสือเรียน'
    LITERATURE = 'literature', 'วรรณคดี'
    PSYCHOLOGY = 'psychology', 'จิตวิทยา'
    HISTORY_ART_SOCIAL = 'history_art_social', 'ประวัติศาสตร์ ศิลปะ และสังคม'


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='ชื่อหมวดหมู่')
    description = models.TextField(blank=True, null=True, verbose_name='รายละเอียด')

    class Meta:
        verbose_name = 'หมวดหมู่'
        verbose_name_plural = 'หมวดหมู่'
        ordering = ['name']

    def __str__(self):
        return self.name


class Author(models.Model):
    full_name = models.CharField(max_length=200, verbose_name='ชื่อ-นามสกุล ผู้แต่ง')
    nationality = models.CharField(max_length=100, blank=True, null=True, verbose_name='สัญชาติ')

    class Meta:
        verbose_name = 'ผู้แต่ง'
        verbose_name_plural = 'ผู้แต่ง'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class Book(models.Model):
    title = models.CharField(max_length=255, verbose_name='ชื่อหนังสือ')
    description = models.TextField(blank=True, null=True, verbose_name='เรื่องย่อ / รายละเอียด')
    cover_image = models.ImageField(
        upload_to='book_covers/',
        blank=True,
        null=True,
        verbose_name='ภาพหน้าปก',
    )
    total_copies = models.PositiveIntegerField(default=1, verbose_name='จำนวนเล่มทั้งหมด')
    available_copies = models.PositiveIntegerField(default=1, verbose_name='จำนวนเล่มที่พร้อมยืม')

    learning_area = models.CharField(
        max_length=32,
        choices=LearningArea.choices,
        default=LearningArea.NOVEL,
        verbose_name='หมวดหมู่หนังสือ',
    )
    grade_level = models.CharField(
        max_length=8,
        choices=GradeLevel.choices,
        default=GradeLevel.P1,
        verbose_name='ระดับชั้นที่เหมาะสม',
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        verbose_name='หมวดหมู่ (เพิ่มเติม)',
    )
    authors = models.ManyToManyField(Author, blank=True, related_name='books', verbose_name='ผู้แต่ง')
    ebook_pdf = models.FileField(
        upload_to='ebooks/',
        blank=True,
        null=True,
        verbose_name='ไฟล์ e-book (PDF)',
        help_text='อัปโหลด PDF สำหรับอ่านในตัวอ่านดิจิทัล (ถ้ามี)',
    )
    ebook_text = models.TextField(
        blank=True,
        default='',
        verbose_name='เนื้อหา e-book (ข้อความ)',
        help_text='ถ้าไม่มี PDF ให้วางข้อความ แบ่งหน้าด้วยบรรทัด <<<PAGE>>> ระหว่างหน้า',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='บันทึกเมื่อ')

    class Meta:
        verbose_name = 'หนังสือ'
        verbose_name_plural = 'หนังสือ'
        ordering = ['title']

    def __str__(self):
        return self.title


class Borrow(models.Model):
    class Status(models.TextChoices):
        BORROWED = 'borrowed', 'กำลังยืม'
        RETURNED = 'returned', 'คืนแล้ว'
        OVERDUE = 'overdue', 'เลยกำหนดคืน'

    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='borrows',
        verbose_name='ผู้ยืม',
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrows', verbose_name='หนังสือ')
    borrow_date = models.DateField(auto_now_add=True, verbose_name='วันที่ยืม')
    due_date = models.DateField(verbose_name='วันที่กำหนดคืน')
    return_date = models.DateField(null=True, blank=True, verbose_name='วันที่คืนจริง')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.BORROWED,
        verbose_name='สถานะการคืน',
    )

    class Meta:
        verbose_name = 'การยืมหนังสือ'
        verbose_name_plural = 'การยืมหนังสือ'
        ordering = ['-borrow_date', '-id']

    def __str__(self):
        return f'{self.borrower} — {self.book.title}'


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='library_profile',
        verbose_name='ผู้ใช้',
    )
    student_id = models.CharField(max_length=32, blank=True, default='', verbose_name='รหัสนักเรียน')
    grade_level = models.CharField(
        max_length=8,
        choices=GradeLevel.choices,
        blank=True,
        default='',
        verbose_name='ระดับชั้น',
    )
    phone = models.CharField(max_length=20, blank=True, default='', verbose_name='เบอร์โทรศัพท์')
    birth_date = models.DateField(null=True, blank=True, verbose_name='วันเกิด')
    national_id = models.CharField(
        max_length=13,
        blank=True,
        default='',
        verbose_name='เลขบัตรประชาชน',
    )

    class Meta:
        verbose_name = 'โปรไฟล์สมาชิกห้องสมุด'
        verbose_name_plural = 'โปรไฟล์สมาชิกห้องสมุด'

    def __str__(self):
        if self.student_id:
            return f'{self.user.username} ({self.student_id})'
        return f'{self.user.username}'
