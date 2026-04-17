from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Book, Category, GradeLevel


class StudentRegistrationForm(UserCreationForm):
    """สมัครสมาชิกสำหรับนักเรียนเท่านั้น"""

    student_id = forms.CharField(
        label='รหัสนักเรียน',
        max_length=32,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'รหัสนักเรียนตามทะเบียน',
                'autocomplete': 'off',
            },
        ),
    )
    grade_level = forms.ChoiceField(
        label='ระดับชั้น',
        choices=GradeLevel.choices,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'password1', 'password2')
        labels = {
            'username': 'ชื่อผู้ใช้ (Username)',
            'first_name': 'ชื่อ',
            'last_name': 'นามสกุล',
        }

    field_order = [
        'username',
        'first_name',
        'last_name',
        'student_id',
        'grade_level',
        'password1',
        'password2',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('username', 'first_name', 'last_name', 'password1', 'password2'):
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault('class', 'form-control')
                self.fields[name].required = True
        self.fields['first_name'].widget.attrs.setdefault('autocomplete', 'given-name')
        self.fields['last_name'].widget.attrs.setdefault('autocomplete', 'family-name')

    def save(self, commit=True):
        from .models import UserProfile

        user = super().save(commit=False)
        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'student_id': self.cleaned_data['student_id'].strip(),
                    'grade_level': self.cleaned_data['grade_level'],
                    'phone': '',
                    'birth_date': None,
                    'national_id': '',
                },
            )
        return user


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = (
            'title',
            'description',
            'learning_area',
            'grade_level',
            'category',
            'authors',
            'cover_image',
            'total_copies',
            'available_copies',
            'ebook_pdf',
            'ebook_text',
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'learning_area': forms.Select(attrs={'class': 'form-select'}),
            'grade_level': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'authors': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 8}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'ebook_pdf': forms.FileInput(attrs={'class': 'form-control'}),
            'ebook_text': forms.Textarea(attrs={'class': 'form-control font-monospace small', 'rows': 12}),
        }

    def clean(self):
        data = super().clean()
        total = data.get('total_copies')
        avail = data.get('available_copies')
        if total is not None and avail is not None and avail > total:
            self.add_error('available_copies', 'จำนวนที่พร้อมยืมต้องไม่เกินจำนวนเล่มทั้งหมด')
        return data
