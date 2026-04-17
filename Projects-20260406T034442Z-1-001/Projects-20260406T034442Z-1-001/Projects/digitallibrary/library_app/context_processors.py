from .roles import GROUP_STUDENT, GROUP_TEACHER, user_can_borrow_books, user_is_librarian


def library_roles(request):
    user = request.user
    if not user.is_authenticated:
        return {
            'is_librarian_user': False,
            'is_student_user': False,
            'is_teacher_user': False,
            'can_borrow_user': False,
        }
    names = set(user.groups.values_list('name', flat=True))
    is_super = user.is_superuser
    return {
        'is_librarian_user': user_is_librarian(user),
        'is_student_user': is_super or (GROUP_STUDENT in names),
        'is_teacher_user': is_super or (GROUP_TEACHER in names),
        'can_borrow_user': user_can_borrow_books(user),
    }
