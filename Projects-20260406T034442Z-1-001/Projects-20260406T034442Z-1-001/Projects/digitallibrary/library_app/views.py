from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, User
from django.db.models import Count, Q, Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .decorators import librarian_required
from .forms import BookForm, CategoryForm, StudentRegistrationForm
from .models import Book, Borrow, Category, GradeLevel, LearningArea, UserProfile
from .roles import user_can_borrow_books, user_is_librarian

EBOOK_PREVIEW_MAX_PAGES = 5
BORROW_MAX_DAYS_AHEAD = 90


def sync_borrow_state():
    """คืนหนังสือเข้าสต็อกอัตโนมัติเมื่อเลยกำหนดคืน (วันที่คืน < วันนี้) และยังไม่ได้คืน"""
    today = timezone.localdate()
    expired = Borrow.objects.filter(
        due_date__lt=today,
        status__in=(Borrow.Status.BORROWED, Borrow.Status.OVERDUE),
    ).select_related('book')
    for borrow in expired:
        book = borrow.book
        if book.available_copies < book.total_copies:
            book.available_copies += 1
            book.save()
        borrow.status = Borrow.Status.RETURNED
        borrow.return_date = today
        borrow.save()


def user_can_read_ebook(user, book):
    if user_is_librarian(user):
        return True
    if not user.is_authenticated:
        return False
    return Borrow.objects.filter(
        borrower=user,
        book=book,
        status__in=(Borrow.Status.BORROWED, Borrow.Status.OVERDUE),
    ).exists()


def book_has_ebook_content(book):
    if book.ebook_pdf:
        return True
    text = (book.ebook_text or '').strip()
    if not text:
        return False
    return True


def index(request):
    sync_borrow_state()
    books = Book.objects.select_related('category').prefetch_related('authors').order_by('-created_at')
    q = (request.GET.get('q') or '').strip()
    area = (request.GET.get('area') or '').strip()
    grade = (request.GET.get('grade') or '').strip()

    valid_areas = {c[0] for c in LearningArea.choices}
    valid_grades = {c[0] for c in GradeLevel.choices}
    if area in valid_areas:
        books = books.filter(learning_area=area)
    if grade in valid_grades and grade != GradeLevel.ALL:
        books = books.filter(Q(grade_level=grade) | Q(grade_level=GradeLevel.ALL))

    if q:
        matching_areas = [v for v, label in LearningArea.choices if q.lower() in label.lower()]
        books = books.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(category__name__icontains=q)
            | Q(learning_area__in=matching_areas)
        ).distinct()

    filter_area = area if area in valid_areas else ''
    filter_grade = grade if grade in valid_grades else ''

    area_links = []
    for value, label in LearningArea.choices:
        p = {}
        if q:
            p['q'] = q
        if filter_grade:
            p['grade'] = filter_grade
        p['area'] = value
        area_links.append(
            {
                'value': value,
                'label': label,
                'url': '?' + urlencode(p),
                'active': filter_area == value,
            },
        )

    grade_links = []
    for value, label in GradeLevel.choices:
        p = {}
        if q:
            p['q'] = q
        if filter_area:
            p['area'] = filter_area
        p['grade'] = value
        grade_links.append(
            {
                'value': value,
                'label': label,
                'url': '?' + urlencode(p),
                'active': filter_grade == value,
            },
        )

    clear_filters = '?' + urlencode({'q': q}) if q else '?'

    return render(
        request,
        'index.html',
        {
            'books': books,
            'search_query': q,
            'filter_area': filter_area,
            'filter_grade': filter_grade,
            'area_links': area_links,
            'grade_links': grade_links,
            'clear_filters': clear_filters,
        },
    )


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url:
                    if next_url.startswith('/') and not next_url.startswith('//'):
                        return redirect(next_url)
                    if url_has_allowed_host_and_scheme(
                        next_url,
                        allowed_hosts={request.get_host()},
                        require_https=request.is_secure(),
                    ):
                        return redirect(next_url)
                if user_is_librarian(user):
                    return redirect('librarian_dashboard')
                return redirect('index')
        messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง โปรดลองอีกครั้ง')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('index')


def book_detail(request, book_id):
    sync_borrow_state()
    book = get_object_or_404(
        Book.objects.prefetch_related('authors').select_related('category'),
        id=book_id,
    )
    can_borrow = user_can_borrow_books(request.user) if request.user.is_authenticated else False
    has_ebook = book_has_ebook_content(book)
    can_read_ebook = user_can_read_ebook(request.user, book) if has_ebook else False
    today = timezone.localdate()
    ctx = {
        'book': book,
        'can_borrow': can_borrow,
        'has_ebook': has_ebook,
        'can_read_ebook': can_read_ebook,
        'ebook_preview_max': EBOOK_PREVIEW_MAX_PAGES,
        'borrow_due_min': today.isoformat(),
        'borrow_due_max': (today + timedelta(days=BORROW_MAX_DAYS_AHEAD)).isoformat(),
        'borrow_due_default': (today + timedelta(days=7)).isoformat(),
        'is_librarian_user': user_is_librarian(request.user) if request.user.is_authenticated else False,
    }
    return render(request, 'book_detail.html', ctx)


def borrow_book(request, book_id):
    sync_borrow_state()
    if not request.user.is_authenticated:
        messages.warning(request, 'กรุณาเข้าสู่ระบบก่อนยืมหนังสือ')
        return redirect('login')

    if not user_can_borrow_books(request.user):
        messages.error(
            request,
            'เฉพาะนักเรียน ครู หรือผู้ดูแลระบบเท่านั้นที่ยืมหนังสือผ่านหน้านี้ได้',
        )
        return redirect('book_detail', book_id=book_id)

    book = get_object_or_404(Book, id=book_id)
    today = timezone.localdate()
    max_due = today + timedelta(days=BORROW_MAX_DAYS_AHEAD)

    if request.method == 'POST':
        active = Borrow.objects.filter(
            borrower=request.user,
            book=book,
            status__in=(Borrow.Status.BORROWED, Borrow.Status.OVERDUE),
        ).exists()
        if active:
            messages.warning(request, f'คุณกำลังยืม "{book.title}" อยู่แล้ว')
        elif book.available_copies > 0:
            due_raw = (request.POST.get('due_date') or '').strip()
            if due_raw:
                try:
                    due = datetime.strptime(due_raw, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'รูปแบบวันที่คืนไม่ถูกต้อง')
                    return redirect('book_detail', book_id=book.id)
            else:
                due = today + timedelta(days=7)

            if due < today:
                messages.error(request, 'วันที่คืนต้องไม่ก่อนวันนี้')
                return redirect('book_detail', book_id=book.id)
            if due > max_due:
                messages.error(
                    request,
                    f'วันที่คืนต้องไม่เกิน {BORROW_MAX_DAYS_AHEAD} วันนับจากวันนี้',
                )
                return redirect('book_detail', book_id=book.id)

            book.available_copies -= 1
            book.save()

            Borrow.objects.create(
                borrower=request.user,
                book=book,
                due_date=due,
            )
            messages.success(
                request,
                f'ยืมหนังสือ "{book.title}" สำเร็จ! กรุณาติดต่อรับหนังสือที่บรรณารักษ์ — กำหนดคืน {due.strftime("%d/%m/%Y")} — อ่านฉบับดิจิทัลเต็มเล่มได้ที่เมนู «หนังสือของฉัน»',
            )
        else:
            messages.error(request, 'ขออภัย หนังสือเล่มนี้ถูกยืมหมดแล้ว')

    return redirect('book_detail', book_id=book.id)


def register_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            student_group = Group.objects.filter(name='Student').first()
            if student_group:
                user.groups.add(student_group)
            login(request, user)
            messages.success(request, 'สมัครสมาชิกสำเร็จ! ยินดีต้อนรับนักเรียนเข้าสู่ห้องสมุด')
            return redirect('index')
    else:
        form = StudentRegistrationForm()

    return render(request, 'register.html', {'form': form})


@login_required
def my_borrow_history(request):
    sync_borrow_state()
    borrows = (
        Borrow.objects.filter(borrower=request.user)
        .select_related('book', 'book__category')
        .order_by('-borrow_date', '-id')
    )
    return render(request, 'borrow_history.html', {'borrows': borrows})


@login_required
def my_books(request):
    """หนังสือที่กำลังยืม — ลิงก์ไปตัวอ่าน e-book"""
    sync_borrow_state()
    borrows = (
        Borrow.objects.filter(
            borrower=request.user,
            status__in=(Borrow.Status.BORROWED, Borrow.Status.OVERDUE),
        )
        .select_related('book', 'book__category')
        .order_by('-borrow_date', '-id')
    )
    return render(request, 'my_books.html', {'borrows': borrows})


@login_required
def return_my_borrow(request, borrow_id):
    sync_borrow_state()
    if request.method != 'POST':
        return redirect('my_books')

    if not user_can_borrow_books(request.user):
        messages.error(request, 'คุณไม่มีสิทธิ์ดำเนินการคืนหนังสือผ่านระบบนี้')
        return redirect('index')

    borrow = get_object_or_404(
        Borrow.objects.select_related('book'),
        id=borrow_id,
        borrower=request.user,
    )

    if borrow.status == Borrow.Status.RETURNED:
        messages.warning(request, 'รายการนี้คืนหนังสือแล้ว')
        return redirect('my_books')

    book = borrow.book
    if book.available_copies < book.total_copies:
        book.available_copies += 1
        book.save()

    borrow.status = Borrow.Status.RETURNED
    borrow.return_date = timezone.localdate()
    borrow.save()

    messages.success(request, f'แจ้งคืน "{book.title}" เรียบร้อย — กรุณานำหนังสือตัวจริงมาส่งที่บรรณารักษ์')
    return redirect('my_books')


@login_required
def ebook_reader(request, book_id):
    sync_borrow_state()
    book = get_object_or_404(
        Book.objects.prefetch_related('authors').select_related('category'),
        id=book_id,
    )
    if not book_has_ebook_content(book):
        messages.info(request, 'หนังสือเล่มนี้ยังไม่มีฉบับอ่านดิจิทัล')
        return redirect('book_detail', book_id=book_id)

    full_access = user_can_read_ebook(request.user, book)
    preview_mode = not full_access

    text = (book.ebook_text or '').strip()
    pages = []
    if text:
        raw_pages = [p.strip() for p in text.split('<<<PAGE>>>')]
        pages = [p for p in raw_pages if p]

    mode = 'pdf' if book.ebook_pdf else 'text'
    if mode == 'text' and not pages:
        pages = [
            (book.description or 'ยังไม่มีเนื้อหาสำหรับตัวอ่านดิจิทัล — บรรณารักษ์สามารถเพิ่ม PDF หรือข้อความในหน้าจัดการหนังสือ').strip()
        ]

    if preview_mode and pages:
        pages = pages[:EBOOK_PREVIEW_MAX_PAGES]

    pdf_url = ''
    if book.ebook_pdf:
        pdf_url = request.build_absolute_uri(
            reverse('ebook_pdf_serve', kwargs={'book_id': book.id})
        )

    return render(
        request,
        'ebook_reader.html',
        {
            'book': book,
            'mode': mode,
            'pages': pages,
            'pdf_url': pdf_url,
            'preview_mode': preview_mode,
            'max_preview_pages': EBOOK_PREVIEW_MAX_PAGES,
            'show_my_books_link': full_access and user_can_borrow_books(request.user),
        },
    )


@login_required
def ebook_pdf_serve(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if not book.ebook_pdf:
        raise Http404()
    if not (user_can_read_ebook(request.user, book) or book_has_ebook_content(book)):
        raise Http404()
    try:
        return FileResponse(book.ebook_pdf.open('rb'), content_type='application/pdf')
    except FileNotFoundError:
        raise Http404() from None


@librarian_required
def librarian_dashboard(request):
    sync_borrow_state()
    total_books = Book.objects.count()
    total_users = User.objects.filter(is_active=True).count()
    users_qs = list(
        User.objects.filter(is_active=True)
        .annotate(
            active_borrows=Count(
                'borrows',
                filter=Q(
                    borrows__status__in=(
                        Borrow.Status.BORROWED,
                        Borrow.Status.OVERDUE,
                    ),
                ),
            ),
        )
        .order_by('username')
    )
    dashboard_rows = []
    uids = [u.pk for u in users_qs]
    profile_map = {p.user_id: p for p in UserProfile.objects.filter(user_id__in=uids)} if uids else {}
    for u in users_qs:
        prof = profile_map.get(u.pk)
        dashboard_rows.append(
            {
                'user': u,
                'student_id': prof.student_id if prof else '',
                'grade_display': prof.get_grade_level_display() if prof and prof.grade_level else '',
                'active_borrows': u.active_borrows,
            },
        )
    return render(
        request,
        'librarian_dashboard.html',
        {
            'total_books': total_books,
            'total_users': total_users,
            'dashboard_rows': dashboard_rows,
        },
    )


@librarian_required
def librarian_returns(request):
    sync_borrow_state()
    q = (request.GET.get('q') or '').strip()

    active_borrows = (
        Borrow.objects.filter(status__in=(Borrow.Status.BORROWED, Borrow.Status.OVERDUE))
        .select_related('borrower', 'book', 'book__category')
        .order_by('borrower__username', '-borrow_date')
    )

    if q:
        active_borrows = active_borrows.filter(
            Q(borrower__username__icontains=q)
            | Q(borrower__first_name__icontains=q)
            | Q(borrower__last_name__icontains=q)
            | Q(borrower__email__icontains=q)
        )

    return render(
        request,
        'librarian_returns.html',
        {'borrows': active_borrows, 'search_query': q},
    )


@librarian_required
def return_borrow(request, borrow_id):
    sync_borrow_state()
    if request.method != 'POST':
        return redirect('librarian_returns')

    borrow = get_object_or_404(
        Borrow.objects.select_related('book'),
        id=borrow_id,
    )

    if borrow.status == Borrow.Status.RETURNED:
        messages.warning(request, 'รายการนี้คืนหนังสือแล้ว')
        return redirect('librarian_returns')

    book = borrow.book
    if book.available_copies < book.total_copies:
        book.available_copies += 1
        book.save()

    borrow.status = Borrow.Status.RETURNED
    borrow.return_date = timezone.localdate()
    borrow.save()

    student_label = borrow.borrower.get_full_name() or borrow.borrower.username
    messages.success(
        request,
        f'รับคืน "{book.title}" จาก {student_label} เรียบร้อยแล้ว',
    )
    return redirect('librarian_returns')


@librarian_required
def librarian_book_list(request):
    books = Book.objects.select_related('category').prefetch_related('authors').order_by('title')
    q = (request.GET.get('q') or '').strip()
    if q:
        matching_areas = [v for v, label in LearningArea.choices if q.lower() in label.lower()]
        books = books.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(category__name__icontains=q)
            | Q(learning_area__in=matching_areas)
        ).distinct()
    return render(request, 'librarian_book_list.html', {'books': books, 'search_query': q})


@librarian_required
def librarian_book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มหนังสือเรียบร้อยแล้ว')
            return redirect('librarian_book_list')
    else:
        form = BookForm()

    return render(request, 'librarian_book_form.html', {'form': form, 'title_label': 'เพิ่มหนังสือ'})


@librarian_required
def librarian_book_edit(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'บันทึกการแก้ไขหนังสือเรียบร้อย')
            return redirect('librarian_book_list')
    else:
        form = BookForm(instance=book)

    return render(
        request,
        'librarian_book_form.html',
        {'form': form, 'book': book, 'title_label': 'แก้ไขหนังสือ'},
    )


@librarian_required
def librarian_book_delete(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    active = Borrow.objects.filter(
        book=book,
        status__in=(Borrow.Status.BORROWED, Borrow.Status.OVERDUE),
    ).exists()
    if request.method == 'POST':
        if active:
            messages.error(request, 'ไม่สามารถลบได้ขณะมีผู้ยืมเล่มนี้อยู่')
            return redirect('librarian_book_list')
        title = book.title
        book.delete()
        messages.success(request, f'ลบหนังสือ «{title}» แล้ว')
        return redirect('librarian_book_list')
    return render(request, 'librarian_book_confirm_delete.html', {'book': book, 'has_active_borrow': active})


@librarian_required
def librarian_category_list(request):
    categories = Category.objects.annotate(
        book_count=Count('books'),
        total_stock=Sum('books__total_copies'),
        available_stock=Sum('books__available_copies'),
    ).order_by('name')
    return render(request, 'librarian_category_list.html', {'categories': categories})


@librarian_required
def librarian_category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มหมวดหมู่เรียบร้อยแล้ว')
            return redirect('librarian_category_list')
    else:
        form = CategoryForm()
    return render(request, 'librarian_category_form.html', {'form': form, 'title_label': 'เพิ่มหมวดหมู่'})


@librarian_required
def librarian_category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'บันทึกหมวดหมู่เรียบร้อย')
            return redirect('librarian_category_list')
    else:
        form = CategoryForm(instance=category)
    return render(
        request,
        'librarian_category_form.html',
        {'form': form, 'category': category, 'title_label': 'แก้ไขหมวดหมู่'},
    )


@librarian_required
def librarian_category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    book_count = Book.objects.filter(category=category).count()
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'ลบหมวดหมู่ «{name}» แล้ว — หนังสือในหมวดนี้จะไม่มีหมวดจนกว่าจะแก้ไข')
        return redirect('librarian_category_list')
    return render(
        request,
        'librarian_category_confirm_delete.html',
        {'category': category, 'book_count': book_count},
    )
