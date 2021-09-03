import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


class PostCreateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group1 = Group.objects.create(
            title='Первая группа',
            slug='first',
            description='Тестовое описание первой группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group1
        )

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostCreateTests.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма в post_create создает запись."""
        post_cnt = Post.objects.count()
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
            'text': PostCreateTests.post.text,
            'group': PostCreateTests.post.group.id,
            'image': uploaded
        }
        response = self.authorized_client_author.post(
            reverse('post:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'post:profile', kwargs={
                    'username': 'auth'
                }
            )
        )
        self.assertEqual(Post.objects.count(), post_cnt + 1)
        self.assertTrue(
            Post.objects.filter(
                text=PostCreateTests.post.text,
                group=PostCreateTests.post.group.id
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма в post_edit редактирует
        и сохраняет запись."""
        post_cnt = Post.objects.count()
        form_data = {
            'text': PostCreateTests.post.text,
            'group': PostCreateTests.post.group.id
        }
        response = self.authorized_client_author.post(
            reverse(
                'post:post_edit', kwargs={'post_id': PostCreateTests.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'post:post_detail', kwargs={
                    'post_id': PostCreateTests.post.id
                }
            )
        )
        self.assertEqual(Post.objects.count(), post_cnt)
        self.assertTrue(
            Post.objects.filter(
                text=PostCreateTests.post.text,
                group=PostCreateTests.post.group.id
            ).exists()
        )
