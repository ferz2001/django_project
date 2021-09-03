from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from core.common.utils import paginate

from .forms import CommentForm, PostForm
from .models import Comment, Group, Post, User, Follow


@cache_page(20)
def index(request):
    template = 'posts/index.html'
    text = "Последние обновления на сайте"
    posts = Post.objects.all()
    page_obj = paginate(request, posts)
    context = {
        'text': text,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    description = group.description
    page_obj = paginate(request, posts)
    context = {
        'group': group,
        'posts': posts,
        'description': description,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    username = post.author.username
    count = Post.objects.filter(author__username=username).count()
    form = CommentForm()
    comments = Comment.objects.filter(post=post_id)
    context = {
        'post': post,
        'count': count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_all = author.posts.all()
    post_cnt = author.posts.all().count()
    page_obj = paginate(request, post_all)
    followings = author.following.all()
    following = False
    authors = [str(i.user) for i in followings]
    if request.user.username in authors:
        following = True
    context = {
        'page_obj': page_obj,
        'count': post_cnt,
        'username': username,
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post = form.save()
        username = request.user.username
        return redirect(reverse('post:profile',
                                kwargs={'username': username}
                                )
                        )
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user.username != post.author.username:
        return redirect(reverse('post:post_detail',
                                kwargs={'post_id': post_id}
                                )
                        )
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect(reverse('post:post_detail',
                                kwargs={'post_id': post_id}
                                )
                        )
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(
        request, 'posts/create_post.html', context
    )


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    followers = request.user.follower.all()
    followers = [follower.author for follower in followers]
    posts = Post.objects.filter(author__in=followers)
    page_obj = paginate(request, posts)
    text = "Последние записи авторов, на которых ты подписан"
    context = {
        'page_obj': page_obj,
        'text': text,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    followers = request.user.follower.all()
    followers = [follower.author for follower in followers]
    if author not in followers:
        if request.user != author:
            Follow.objects.create(user=request.user, author=author)
            return redirect('post:profile', username=username)
        return redirect('post:profile', username=username)
    return redirect('post:profile', username=username)
    


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('post:profile', username=username)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('post:post_detail', post_id=post_id)
