from django.urls import path
import blog.views as blog

urlpatterns = [
    path('', blog.index),
    path('article/<int:article_id>', blog.article_page, name='article_page'),
    path('edit/<int:article_id>', blog.edit_page, name='edit_page'),
    path('edit/action/', blog.edit_action, name='edit_action'),
]