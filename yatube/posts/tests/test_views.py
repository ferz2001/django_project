import shutil
import tempfile
from datetime import datetime, timedelta

from django.core.cache import cache
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group1 = Group.objects.create(
            title='Первая группа',
            slug='first',
            description='Тестовое описание первой группы',
        )
        cls.group2 = Group.objects.create(
            title='Вторая группа',
            slug='second',
            description='Тестовое описание второй группы',
        )
        for i in range(6):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group1
            )
            cls.post.pub_date = datetime.now() + timedelta(minutes=i)
            cls.post.save()

        for i in range(6, 12):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group2
            )
            cls.post.pub_date = datetime.now() + timedelta(minutes=i)
            cls.post.save()

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostViewsTests.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse(
                'post:group_list', kwargs={
                    'slug': PostViewsTests.group1.slug
                }
            ): 'posts/group_list.html',
            reverse(
                'post:profile', kwargs={
                    'username': PostViewsTests.user.username
                }
            ): 'posts/profile.html',
            reverse(
                'post:post_detail', kwargs={
                    'post_id': PostViewsTests.post.id
                }
            ): 'posts/post_detail.html',
            reverse(
                'post:post_edit', kwargs={
                    'post_id': PostViewsTests.post.id
                }
            ): 'posts/create_post.html',
            reverse(
                'post:post_create'
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def context_test(self, page_obj_id, response):
        post_result = Post.objects.get(
            text=f'Тестовый пост {11-page_obj_id}'
        )
        post = response.context['page_obj'][page_obj_id]
        post_author = post.author.username
        post_text = post.text
        post_group = post.group
        post_id = post.id
        self.assertEqual(post_author, PostViewsTests.user.username)
        self.assertEqual(post_text, post_result.text)
        self.assertEqual(str(post_group), str(post_result.group))
        self.assertEqual(post_id, post_result.id)

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом.
        Проверяется вторая группа"""
        response = self.authorized_client_author.get(
            reverse('post:group_list', kwargs={
                'slug': PostViewsTests.group2.slug
            }))
        first_obj_in_page = 0
        last_obj_in_page = 5
        self.context_test(first_obj_in_page, response)
        self.context_test(last_obj_in_page, response)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('post:profile', kwargs={
                'username': PostViewsTests.user.username
            }))
        first_obj_in_page = 0
        last_obj_in_page = 9
        self.context_test(first_obj_in_page, response)
        self.context_test(last_obj_in_page, response)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('post:post_detail', kwargs={
                'post_id': PostViewsTests.post.id
            }))
        post = response.context['post']
        post_result = Post.objects.get(id=f'{PostViewsTests.post.id}')
        post_author = post.author.username
        post_text = post.text
        post_group = post.group
        post_id = post.id
        self.assertEqual(post_author, PostViewsTests.user.username)
        self.assertEqual(post_text, post_result.text)
        self.assertEqual(str(post_group), str(post_result.group))
        self.assertEqual(post_id, post_result.id)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('post:post_edit', kwargs={
                'post_id': f'{PostViewsTests.post.id}'
            })
        )
        title_inital = response.context['form'].instance.text
        self.assertEqual(title_inital, PostViewsTests.post.text)

        title_inital = response.context['form'].instance.group
        self.assertEqual(str(title_inital), str(PostViewsTests.post.group))

    def test_home_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('post:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group1 = Group.objects.create(
            title='Первая группа',
            slug='first',
            description='Тестовое описание первой группы',
        )
        cls.group2 = Group.objects.create(
            title='Вторая группа',
            slug='second',
            description='Тестовое описание второй группы',
        )
        for i in range(13):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group1
            )
            cls.post.pub_date = datetime.now() + timedelta(minutes=i)
            cls.post.save()

        for i in range(13, 15):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group2
            )
            cls.post.pub_date = datetime.now() + timedelta(minutes=i)
            cls.post.save()

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostPaginatorTests.user)

    def test_first_page_contains_ten_records(self):
        response = self.authorized_client_author.get(
            reverse('post:group_list', kwargs={'slug': 'first'})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        response = self.authorized_client_author.get(reverse(
            'post:group_list', kwargs={'slug': 'first'}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records(self):
        response = self.authorized_client_author.get(reverse(
            'post:profile', kwargs={'username': 'auth'})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        response = self.authorized_client_author.get(reverse(
            'post:profile', kwargs={'username': 'auth'}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 5)


class ImagePostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.user = User.objects.create_user(username='auth')
        cls.group1 = Group.objects.create(
            title='Первая группа',
            slug='first',
            description='Тестовое описание первой группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group1,
            image=uploaded
        )

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(ImagePostViewsTests.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_image_in_pages(self):
        templates_page_names = {
            reverse(
                'post:group_list', kwargs={
                    'slug': ImagePostViewsTests.group1.slug
                }
            ): 'group',
            reverse(
                'post:profile', kwargs={
                    'username': ImagePostViewsTests.user.username
                }
            ): 'profile',
        }
        post_result = Post.objects.get(
            text='Тестовый пост'
        )
        for reverse_name, page in templates_page_names.items():
            with self.subTest(page=page):
                response = self.authorized_client_author.post(reverse_name)
                post_image = response.context['page_obj'][0].image
                self.assertEqual(post_image, post_result.image)

    def test_image_post_create(self):
        post_result = Post.objects.get(
            text='Тестовый пост'
        )
        response = self.authorized_client_author.post(
            reverse(
                'post:post_detail', kwargs={
                    'post_id': ImagePostViewsTests.post.id
                }
            )
        )
        post_image = response.context['post'].image
        self.assertEqual(post_image, post_result.image)


class CommentPostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Тестовый комментарий'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(CommentPostTests.user)

    def test_comment_post_is_created_and_appears(self):
        response = self.authorized_client_author.get(reverse(
            'post:post_detail', kwargs={
                'post_id': f'{CommentPostTests.post.id}'
            })
        )
        comment_result = Comment.objects.get(text='Тестовый комментарий')
        comment = response.context['comments'][0].text
        self.assertEqual(comment, comment_result.text)


class CachePostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(CachePostTests.user)

    def test_cache_index(self):
        response = self.authorized_client_author.get(reverse('post:index'))
        post1 = response.content
        Post.objects.all().delete()
        response = self.authorized_client_author.get(reverse('post:index'))
        post2 = response.content
        self.assertIn(post1, post2)
        cache.clear()
        response = self.authorized_client_author.get(reverse('post:index'))
        post3 = response.content
        self.assertNotIn(post2, post3)


class FollowPostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth1')
        cls.user_n = User.objects.create_user(username='auth2')
        cls.user_post = User.objects.create_user(username='auth3')
        cls.post = Post.objects.create(
            author=cls.user_post,
            text='Тестовый пост',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user_post
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(FollowPostTests.user)
        self.authorized_client_n = Client()
        self.authorized_client_n.force_login(FollowPostTests.user_n)

    def test_view_in_page_follow(self):
        response = self.authorized_client.get(reverse(
            'post:follow_index')
        )
        post = response.context['page_obj'][0]
        self.assertTrue(Post.objects.get(
            text=FollowPostTests.post), post
        )
        response = self.authorized_client_n.get(reverse(
            'post:follow_index')
        )
        post = response.context['page_obj']
        self.assertNotEqual(post, Post.objects.get(
            text=FollowPostTests.post))

    def test_following(self):
        follow_cnt = Follow.objects.count()
        response = self.authorized_client_n.get(reverse(
            'post:profile_follow', kwargs={
                'username': FollowPostTests.user_post.username
            })
        )
        self.assertRedirects(
            response, reverse(
                'post:profile', kwargs={
                    'username': FollowPostTests.user_post.username
                }
            )
        )
        self.assertEqual(Follow.objects.count(), follow_cnt + 1)

    def test_unfollowing(self):
        follow_cnt = Follow.objects.count()
        response = self.authorized_client_n.get(reverse(
            'post:profile_unfollow', kwargs={
                'username': FollowPostTests.user_post.username
            })
        )
        self.assertRedirects(
            response, reverse(
                'post:profile', kwargs={
                    'username': FollowPostTests.user_post.username
                }
            )
        )
        self.assertEqual(Follow.objects.count(), follow_cnt)
