from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment, User


class PostFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="NoName")
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group_other = Group.objects.create(
            title='Название другой группы',
            description='Описание другой группы',
            slug='test-other-slug'
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {"text": "Тестовый текст"}
        response = self.authorized_client.post(
            reverse("posts:create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response, reverse("posts:profile",
                              kwargs={"username": self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text="Тестовый текст").exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        self.post = Post.objects.create(
            author=self.user,
            text="Тестовый текст",
        )
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        posts_count = Post.objects.count()
        form_data = {"text": "Меняем текст", "group": self.group_other.id}
        response = self.authorized_client.post(
            reverse("posts:edit", args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse("posts:post_detail",
                              kwargs={"post_id": self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(text="Меняем текст",
                                            group=self.group_other.id).exists()
                        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_guest_client(self):
        """Валидная форма не создаст запись в Post"""
        """если пользователь не авторизирован"""
        posts_count = Post.objects.count()
        form_data = {"text": "Тестовый текст"}
        response = self.guest_client.post(
            reverse("posts:create"), data=form_data, follow=True
        )
        self.assertRedirects(response,
                             f'{reverse("users:login")}?next=/create/')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(text="Тестовый текст").exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_not_create_guest_client(self):
        """Валидная форма не изменит запись в Post если неавторизован."""
        self.post = Post.objects.create(
            author=self.user,
            text="Тестовый текст",
        )
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        posts_count = Post.objects.count()
        form_data = {"text": "Изменяем текст", "group": self.group.id}
        response = self.guest_client.post(
            reverse("posts:edit", args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response,
                             f"/auth/login/?next=/posts/{self.post.id}/edit/")
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(text="Изменяем текст").exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_not_author(self):
        self.ktoto = User.objects.create_user(username="Ktoto")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.ktoto)
        self.post = Post.objects.create(
            author=self.user,
            text="Тестовый текст",
        )
        url = reverse('posts:edit', args=[1])
        self.authorized_client.get(url)
        form_data = {
            "text": "Измененный текст",
        }
        self.authorized_client.post(
            reverse('posts:edit', args=[1]),
            data=form_data,
            follow=True,
        )
        self.assertFalse(Post.objects.filter(text="Измененный текст").exists())

    def test_post_with_picture(self):
        count_posts = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Пост с картинкой',
            'image': uploaded
        }
        self.authorized_client.post(
            reverse('posts:create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), count_posts + 1)

    def test_authorized_user_create_comment(self):
        comments_count = Comment.objects.count()
        self.post = Post.objects.create(
            author=self.user,
            text="Тестовый текст",)
        form_data = {"text": "текст комментария"}
        response = self.authorized_client.post(
            reverse("posts:add_comment", args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(Comment.objects.latest('id').text, form_data['text'])
        self.assertEqual(response.status_code, HTTPStatus.OK)
