import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Post, Group, Comment, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    """Проверка форм приложения Posts"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.form = PostForm()
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.get(username='author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_authorized_client(self):
        '''Авторизованый пользователь может публиковать пост'''
        number_of_new_posts = 1
        post_count = Post.objects.count()
        small_gif_new = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif_new,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user}
        ))

        post_last = Post.objects.latest('pub_date')
        self.assertEqual(Post.objects.count(),
                         post_count + number_of_new_posts
                         )
        self.assertEqual(post_last.text, form_data['text'])
        self.assertEqual(post_last.group, self.group)
        self.assertEqual(post_last.author, self.user)
        self.assertEqual(post_last.image.read(), small_gif_new)

    def test_edit_post_authorized_client(self):
        '''Авторизованый пользователь может редактировать пост'''
        group_new = Group.objects.create(
            title='новая группа',
            slug='slug_new',
            description='Тестовое описание',
        )
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тут были перемены',
            'group': group_new.id,
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        edit_post = Post.objects.get(id=self.post.id)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id},
        ))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(edit_post.text, form_data['text'])
        self.assertEqual(edit_post.group, group_new)
        self.assertEqual(edit_post.author, self.user)

    def test_add_comment_authorized_client(self):
        """Комментарий создается авторизованным пользователем"""
        count_comments = Comment.objects.count()
        form_data = {'text': 'Комментарий'}
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), count_comments + 1)
        self.assertEqual(Comment.objects.first().text, form_data['text'])

    def test_add_comment_client(self):
        """Комментарий не создается обычным пользователем"""
        count_comments = Comment.objects.count()
        form_data = {'text': 'Test comment'}
        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), count_comments)
