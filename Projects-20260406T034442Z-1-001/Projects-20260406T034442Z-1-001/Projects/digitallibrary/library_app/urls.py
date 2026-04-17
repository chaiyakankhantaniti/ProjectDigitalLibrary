from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('book/<int:book_id>/pdf/', views.ebook_pdf_serve, name='ebook_pdf_serve'),
    path('book/<int:book_id>/read/', views.ebook_reader, name='ebook_reader'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('my-books/', views.my_books, name='my_books'),
    path('my-books/return/<int:borrow_id>/', views.return_my_borrow, name='return_my_borrow'),
    path('my-history/', views.my_borrow_history, name='borrow_history'),
    path('librarian/', views.librarian_dashboard, name='librarian_dashboard'),
    path('librarian/returns/', views.librarian_returns, name='librarian_returns'),
    path('librarian/return/<int:borrow_id>/', views.return_borrow, name='return_borrow'),
    path('librarian/books/', views.librarian_book_list, name='librarian_book_list'),
    path('librarian/books/new/', views.librarian_book_create, name='librarian_book_create'),
    path('librarian/books/<int:book_id>/edit/', views.librarian_book_edit, name='librarian_book_edit'),
    path('librarian/books/<int:book_id>/delete/', views.librarian_book_delete, name='librarian_book_delete'),
    path('librarian/categories/', views.librarian_category_list, name='librarian_category_list'),
    path('librarian/categories/new/', views.librarian_category_create, name='librarian_category_create'),
    path('librarian/categories/<int:category_id>/edit/', views.librarian_category_edit, name='librarian_category_edit'),
    path('librarian/categories/<int:category_id>/delete/', views.librarian_category_delete, name='librarian_category_delete'),
]
