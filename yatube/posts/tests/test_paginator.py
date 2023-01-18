from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group, User


class PaginatorViewsTest(TestCase):
    POSTS_ON_FIRST_PAGE = 10
    POSTS_ON_SECOND_PAGE = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='auth',
        )
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        Post.objects.bulk_create([Post(text=f"Post {i}",
                                       author=cls.user,
                                       group=cls.group) for i in range(13)])

    def setUp(self):
        self.unauthorized_client = Client()

    def test_paginator_on_pages(self):
        """Проверка пагинации на страницах."""
        url_pages = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for reverse_ in url_pages:
            with self.subTest(reverse_=reverse_):
                self.assertEqual(len(self.unauthorized_client.get(
                    reverse_).context.get('page_obj')),
                    PaginatorViewsTest.POSTS_ON_FIRST_PAGE
                )
                self.assertEqual(len(self.unauthorized_client.get(
                    reverse_ + '?page=2').context.get('page_obj')),
                    PaginatorViewsTest.POSTS_ON_SECOND_PAGE
                )
