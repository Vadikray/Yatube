import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms

from posts.models import Post, Group, Comment, Follow, User
from posts.constants import NUMBER_OF_POSTS

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SECOND_PAGE_COUNT_POST = 3


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='author')
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
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )

        cls.INDEX = reverse('posts:index')
        cls.GROUP_LIST = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug},
        )
        cls.PROFILE = reverse(
            'posts:profile',
            kwargs={'username': cls.user_author},
        )
        cls.POST_DETAIL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id},
        )
        cls.POST_CREATE = reverse('posts:post_create')
        cls.POST_EDIT = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id},
        )
        cls.FOLLOW = reverse('posts:follow_index')
        cls.PROFILE_FOLLOW = reverse(
            'posts:profile_follow',
            args=[cls.user_author],
        ),
        cls.PROFILE_UNFOLLOW = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.user_author},
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        self.user = User.objects.create_user(username='User')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_аuthorized_uses_correct_template(self):
        """URL-адрес использует соответствующий
        шаблон для авторизованых пользователей.
        """
        templates_pages_names = {
            self.INDEX: 'posts/index.html',
            self.GROUP_LIST: 'posts/group_list.html',
            self.PROFILE: 'posts/profile.html',
            self.POST_CREATE: 'posts/create_post.html',
            self.POST_DETAIL: 'posts/post_detail.html',
            self.POST_EDIT: 'posts/create_post.html',
            self.FOLLOW: 'posts/follow.html'
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_profile_group_list_page_index_page_show_correct_context(self):
        """Проверка контекста постов на главной, странице групп и профиля"""
        pages = (
            self.INDEX,
            self.GROUP_LIST,
            self.PROFILE,
        )

        for page in pages:
            with self.subTest(value=page):
                response = self.author_client.get(page)
                post = response.context['page_obj'][0]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(
                    post.author,
                    self.user_author,
                )
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        comment = Comment.objects.create(
            text='Тут должен быть комент',
            author=self.user_author,
            post=self.post,
        )

        form_fields = {'text': forms.fields.CharField}
        response = self.author_client.get(self.POST_DETAIL)
        form_field = response.context.get('form').fields.get('text')
        self.assertIsInstance(form_field, form_fields['text'])
        self.assertEqual(response.context.get('post').id, self.post.id)
        self.assertEqual(response.context.get('post').author, self.user_author)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').group, self.group)
        self.assertEqual(response.context.get('post').image, self.post.image)
        self.assertEqual(response.context['comments'][0], comment)

    def test_group_list_correct_context(self):
        """Контекст group_list соответствует."""
        response = self.author_client.get(self.GROUP_LIST)
        group = response.context['group']
        self.assertEqual(group, self.group)

    def test_profile_orrect_context(self):
        """Контекст profile соответствует."""
        response = self.author_client.get(self.PROFILE)
        self.assertEqual(response.context['author'], self.user_author)
        self.assertFalse(response.context['following'])

    def test_create_post_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.author_client.get(self.POST_CREATE)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_show_correct_context(self):
        """Шаблон edit_create сформирован с правильным контекстом."""
        response = self.author_client.get(self.POST_EDIT)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertEqual(response.context.get('post').id, self.post.id)
        self.assertEqual(response.context.get('post').author, self.user_author)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').group, self.group)
        self.assertTrue(response.context['is_edit'])

    def test_new_post_on_pages(self):
        """Пост попадает на главную страницу, в свою группу и профиль автора"""
        user = User.objects.create_user(username='new')
        group = Group.objects.create(title='new', slug='new')
        post = Post.objects.create(
            author=user,
            text='новый пост',
            group=group,
        )
        pages = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': group.slug}),
            reverse('posts:profile', kwargs={'username': user.username}),
        )
        for reverses in pages:
            with self.subTest(value=reverses):
                response = self.author_client.get(reverses)
                self.assertEqual(
                    response.context.get('page_obj')[0],
                    post,
                )

    def test_new_post_another_pages(self):
        """Пост не попадает в чужую группу"""
        user = User.objects.create_user(username='new_author')
        group = Group.objects.create(title='new_group', slug='new-slug')
        post = Post.objects.create(
            author=user,
            text='новый пост',
            group=group,
        )

        response = self.author_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug})
        )
        self.assertNotIn(post, response.context.get('page_obj').object_list)

    def test_cache_index(self):
        """Кеширование главной страницы работает"""
        content = self.client.get(self.INDEX).content
        Post.objects.all().delete()
        content_after = self.client.get(self.INDEX).content
        self.assertEqual(content, content_after)

    def test_following_for_users(self):
        """Неавторизованый пользователь не может создать подписку"""
        follow_count = Follow.objects.count()
        self.client.get(reverse(
            'posts:profile_follow',
            args=[self.user_author],
        ))
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_following_for_authorized_users(self):
        """Авторизованый пользователь создаёт подписку"""
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=[self.user_author],
        ))

        follow = Follow.objects.latest('id')
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(follow.user, self.user)
        self.assertEqual(follow.author, self.user_author)
        follow_count_after = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=[self.user_author],
        ))

        self.assertEqual(Follow.objects.count(), follow_count_after)

    def test_authorized_users_remove_following(self):
        """Авторизованый пользователь удаляет подписки"""
        Follow.objects.create(user=self.user, author=self.user_author)
        follow_count = Follow.objects.count()
        self.authorized_client.get(self.PROFILE_UNFOLLOW)
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_new_post_shows_follower(self):
        """Подписчик видит новую запись """
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=[self.user_author],
        ))
        Post.objects.create(
            text='Новый тестовый пост',
            author=self.user_author,
        )
        response = self.authorized_client.get(self.FOLLOW)
        self.assertEqual(
            response.context['page_obj'][0],
            Post.objects.latest('pub_date'),
        )

    def test_new_post_dont_shows_nofollower(self):
        """Неподписчик не видит новую запись"""
        Post.objects.create(
            text='Новый тестовый пост',
            author=self.user,
        )
        response = self.author_client.get(self.FOLLOW)
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):

    @ classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )

        for i in range(NUMBER_OF_POSTS + SECOND_PAGE_COUNT_POST):
            cls.post = Post.objects.create(
                author=cls.user_author,
                text=f'Тестовый пост {i}',
                group=cls.group,
            )

        cls.INDEX = reverse('posts:index')
        cls.GROUP_LIST = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug},
        )
        cls.PROFILE = reverse('posts:profile', kwargs={
            'username': cls.user_author})

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_author)

    def test_first_page_contains_ten_records(self):
        """На страницы приложения posts выводится по 10 постов"""
        pages = (
            self.INDEX,
            self.GROUP_LIST,
            self.PROFILE,
        )

        for reverses in pages:
            with self.subTest(value=reverses):
                response = self.authorized_client.get(reverses)
                self.assertEqual(
                    len(response.context['page_obj']),
                    NUMBER_OF_POSTS
                )

    def test_second_page_contains_three_records(self):
        """Проверка: на второй странице паджинации должно быть три поста."""
        pages = (
            self.INDEX + '?page=2',
            self.GROUP_LIST + '?page=2',
            self.PROFILE + '?page=2',
        )

        for reverses in pages:
            with self.subTest(value=reverses):
                response = self.authorized_client.get(reverses)
                self.assertEqual(
                    len(response.context['page_obj']),
                    SECOND_PAGE_COUNT_POST,
                )
