from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_static_page(self):
        pages = {
            'author_page': '/about/author/',
            'about_page': '/about/tech/'
        }
        for page_name, url in pages.items():
            with self.subTest(page_name):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostURLTests.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_exists_at_desired_location(self):
        """Страница доступна любому пользователю."""
        pages = {
            'author_page': '/about/author/',
            'about_page': '/about/tech/',
            'group_list': f'/group/{PostURLTests.group.slug}/',
            'profile': f'/profile/{PostURLTests.user.username}/',
            'post_detail': f'/posts/{PostURLTests.post.id}/',
        }
        for page_name, url in pages.items():
            with self.subTest(page_name):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url(self):
        """Страница /create/ редиректит неавторизованного пользователя."""
        response = self.guest_client.get('/create/')
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_detail_url_guest(self):
        """Страница post/<post_id>/edit редиректит на страницу регистрации,
        если не авторизован."""
        response = self.guest_client.get(
            f'/posts/{PostURLTests.post.id}/edit/'
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{PostURLTests.post.id}/edit/'
        )

    def test_post_detail_url_not_author(self):
        """Страница post/<post_id>/edit редиректит на страницу поста,
        если авторизован, но не автор."""
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post.id}/edit/'
        )
        self.assertRedirects(
            response, f'/posts/{PostURLTests.post.id}/'
        )

    def test_urls_404_of_unexisting_page(self):
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client_author.get(adress)
                self.assertTemplateUsed(response, template)


class CommentPostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(CommentPostTests.user)

    def test_comment_post_authorized(self):
        response = self.guest_client.get(
            f'/posts/{CommentPostTests.post.id}/comment'
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{CommentPostTests.post.id}/comment'
        )
