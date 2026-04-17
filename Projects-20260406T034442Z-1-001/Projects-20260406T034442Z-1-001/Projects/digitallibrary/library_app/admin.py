from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User

from .models import Author, Book, Borrow, Category, UserProfile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short')
    search_fields = ('name', 'description')
    ordering = ('name',)

    fieldsets = (
        ('ข้อมูลหมวดหมู่', {'fields': ('name', 'description')}),
    )

    @admin.display(description='รายละเอียด (ย่อ)')
    def description_short(self, obj):
        if not obj.description:
            return '—'
        return (obj.description[:80] + '…') if len(obj.description) > 80 else obj.description


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'nationality')
    search_fields = ('full_name', 'nationality')
    ordering = ('full_name',)

    fieldsets = (
        ('ผู้แต่ง', {'fields': ('full_name', 'nationality')}),
    )


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'learning_area',
        'grade_level',
        'category',
        'copies_badge',
        'created_at',
    )
    list_filter = ('learning_area', 'grade_level', 'category', 'created_at')
    search_fields = ('title', 'description')
    autocomplete_fields = ('category',)
    filter_horizontal = ('authors',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        (
            'ข้อมูลหลัก',
            {
                'fields': (
                    'title',
                    'learning_area',
                    'grade_level',
                    'category',
                    'description',
                    'cover_image',
                ),
            },
        ),
        (
            'จำนวนเล่ม',
            {
                'fields': ('total_copies', 'available_copies'),
                'description': 'เมื่อเพิ่มหนังสือใหม่ ควรให้ available_copies ไม่เกิน total_copies',
            },
        ),
        (
            'e-book',
            {
                'fields': ('ebook_pdf', 'ebook_text'),
                'description': 'อัปโหลด PDF หรือวางข้อความแบ่งหน้าด้วย <<<PAGE>>>',
            },
        ),
        (
            'บันทึกระบบ',
            {'fields': ('created_at',), 'classes': ('collapse',)},
        ),
    )

    @admin.display(description='สต็อก')
    def copies_badge(self, obj):
        return f'{obj.available_copies} / {obj.total_copies} เล่มพร้อมยืม'


@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower', 'borrow_date', 'due_date', 'return_date', 'status')
    list_filter = ('status', 'borrow_date', 'due_date')
    search_fields = ('book__title', 'borrower__username', 'borrower__first_name', 'borrower__last_name')
    autocomplete_fields = ('borrower', 'book')
    date_hierarchy = 'borrow_date'
    ordering = ('-borrow_date', '-id')

    fieldsets = (
        (
            'รายการยืม',
            {'fields': ('borrower', 'book')},
        ),
        (
            'กำหนดการ',
            {
                'fields': ('borrow_date', 'due_date', 'return_date'),
                'description': 'วันที่ยืมตั้งอัตโนมัติเมื่อสร้างรายการ',
            },
        ),
        (
            'สถานะ',
            {'fields': ('status',)},
        ),
    )


class GroupAdmin(admin.ModelAdmin):
    """แสดงกลุ่ม Student / Teacher / Librarian ให้จัดการสิทธิ์ได้ชัดเจน"""

    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('permissions',)


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 0
    can_delete = False
    fields = ('student_id', 'grade_level', 'phone', 'birth_date', 'national_id')


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'group_list')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('groups')

    @admin.display(description='กลุ่มผู้ใช้')
    def group_list(self, obj):
        return ', '.join(g.name for g in obj.groups.all()) or '—'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.site_header = 'ระบบห้องสมุดดิจิทัล'
admin.site.site_title = 'ห้องสมุดดิจิทัล'
admin.site.index_title = 'จัดการข้อมูลห้องสมุดโรงเรียน'
