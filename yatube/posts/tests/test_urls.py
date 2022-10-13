from http import HTTPStatus

from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
        )
        cls.INDEX = reverse('posts:index')
        cls.GROUP_LIST = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug},
        )
        cls.PROFILE = reverse('posts:profile', kwargs={
                              'username': cls.user_author})
        cls.POST_DETAIL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id},
        )
        cls.POST_CREATE = reverse('posts:post_create')
        cls.POST_EDIT = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id},
        )
        cls.LOGIN = reverse('users:login')
        cls.ADD_COMMENT = reverse(
            'posts:add_comment',
            kwargs={'post_id': cls.post.id},
        )

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        self.user = User.objects.create_user(username='User')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_anonymous_uses(self):
        """Cтраницы доступные любому пользователю"""
        templates_url = (
            self.INDEX,
            self.GROUP_LIST,
            self.PROFILE,
            self.POST_DETAIL,
        )

        for url in templates_url:
            with self.subTest(value=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_create_authorized_client(self):
        """Страница создания поста доступна авторизованному пользователю """
        response = self.authorized_client.get(self.POST_CREATE)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_edit_autho_client(self):
        """Страница редактирования поста доступна автору"""
        response = self.author_client.get(self.POST_EDIT)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_non_existent_and_template(self):
        """Проверка не существующей страницы и ее шаблона"""
        response = self.client.get('/error/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_edit_not_autho_client(self):
        """Перенаправление не автора при редактирование поста"""
        response = self.authorized_client.get(self.POST_EDIT, follow=True)
        self.assertRedirects(response, self.POST_DETAIL)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            self.INDEX: 'posts/index.html',
            self.GROUP_LIST: 'posts/group_list.html',
            self.PROFILE: 'posts/profile.html',
            self.POST_DETAIL: 'posts/post_detail.html',
            self.POST_CREATE: 'posts/create_post.html',
            self.POST_EDIT: 'posts/create_post.html',
        }
        for address, template, in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_edit_pages_post_create_for_guest_clien(self):
        """Доступ к post_edit и post_create для неавторизованного юзера"""
        responses = (
            self.client.get(self.POST_EDIT),
            self.client.get(self.POST_CREATE),
        )
        for response in responses:
            with self.subTest(value=response):
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_redirects_for_guest_client(self):
        """Проверка редиректа на страницах закрытых
        для неавторизованых пользователей.
        """
        redirects = {
            self.POST_CREATE: f'{self.LOGIN}?next={self.POST_CREATE}',
            self.POST_EDIT: f'{self.LOGIN}?next={self.POST_EDIT}',
            self.ADD_COMMENT: f'{self.LOGIN}?next={self.ADD_COMMENT}',
        }

        for address, redirect, in redirects.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertRedirects(response, redirect)
