"""กลุ่มผู้ใช้และฟังก์ชันตรวจสอบสิทธิ์"""

GROUP_STUDENT = 'Student'
GROUP_TEACHER = 'Teacher'
GROUP_LIBRARIAN = 'Librarian'


def user_is_librarian(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=GROUP_LIBRARIAN).exists()


def user_can_borrow_books(user):
    """นักเรียน ครู และแอดมิน (superuser) ยืมผ่านระบบได้"""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=(GROUP_STUDENT, GROUP_TEACHER)).exists()


def user_is_reader_member(user):
    """สมาชิกที่ใช้บริการยืมแบบนักเรียน/ครู"""
    return user_can_borrow_books(user)
