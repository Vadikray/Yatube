from django.test import TestCase

from ..models import Group, Post, User
from posts.constants import NUMBER_OF_CHARACTERS_IN_POST_TITLE


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тут должен быть очень длинное название',
        )

    def test_str_correct(self):
        """Проверяем, что у моделей  корректно работает __str__."""
        my_objects_and_expected = (
            (str(self.group), self.group.title),
            (str(self.post),
             self.post.text[:NUMBER_OF_CHARACTERS_IN_POST_TITLE]
             )
        )
        for value, expected in my_objects_and_expected:
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_models_post_verbose_name(self):
        """Post verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'сообщение поста',
            'pub_date': 'дата',
            'author': 'автор поста',
            'group': 'группа поста',
        }

        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_models_post_help_text(self):
        """Post help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }

        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
