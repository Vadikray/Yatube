from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    '''Создает postform по модели post'''
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    '''Создает postform по модели post'''
    class Meta:
        model = Comment
        fields = ('text',)
