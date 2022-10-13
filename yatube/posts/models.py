from django.db import models
from django.contrib.auth import get_user_model

from posts.constants import NUMBER_OF_CHARACTERS_IN_POST_TITLE

User = get_user_model()


class Group(models.Model):
    '''Создание модели Group'''

    title = models.CharField('Название группы', max_length=200)
    slug = models.SlugField('имя для перехода', unique=True)
    description = models.TextField('описание группы')

    class Meta:
        verbose_name = 'группа'
        verbose_name_plural = 'группы'

    def __str__(self) -> str:
        '''Выводит название группы'''
        return self.title


class Post(models.Model):
    '''Создание модели Post'''

    text = models.TextField('сообщение поста', help_text='Введите текст поста')
    pub_date = models.DateTimeField('дата', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор поста',
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='группа поста',
        related_name='posts',
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self) -> str:
        '''Выводит название группы'''
        return self.text[:NUMBER_OF_CHARACTERS_IN_POST_TITLE]


class Comment(models.Model):
    '''Создание модели Comment'''

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='кометарии поста',
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор коментария',
        related_name='comments',
    )
    text = models.TextField('комментарий к посту',
                            help_text='Введите текст комментария')
    created = models.DateTimeField('дата коментария', auto_now_add=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self) -> str:
        '''Выводит сообщение комментария'''
        return self.text


class Follow(models.Model):
    """Создание модели Follow"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписаться на автора',
    )
