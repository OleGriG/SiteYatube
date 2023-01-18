from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from posts.models import Group, Post, Follow, User
from posts.forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse

NUM_POSTS = 10


def index(request):
    posts_on_page = Post.objects.all()
    paginator = Paginator(posts_on_page, NUM_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_on_page = Post.objects.filter(group=group)
    paginator = Paginator(posts_on_page, NUM_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_on_page = Post.objects.filter(author=author)
    paginator = Paginator(posts_on_page, NUM_POSTS)
    page_number = request.GET.get('page')
    posts_count = Post.objects.filter(author=author).count()
    page_obj = paginator.get_page(page_number)
    user_is_not_author = (request.user != author)
    following = (request.user.is_authenticated
                 and Follow.objects.filter(user=request.user,
                                           author=author).exists()
                 )
    template = 'posts/profile.html'
    context = {'page_obj': page_obj,
               'author': author,
               'posts_count': posts_count,
               'following': following,
               'user_is_not_author': user_is_not_author,
               }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    posts_count = Post.objects.filter(author=post.author).count()
    comments = post.comments.all()
    form = CommentForm()
    template = 'posts/post_detail.html'
    context = {
        'post': post,
        'posts_count': posts_count,
        'requser': request.user,
        'comments': comments,
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        create_post = form.save(commit=False)
        create_post.author = request.user
        create_post.save()
        return redirect('posts:profile', create_post.author)
    template = 'posts/create_post.html'
    context = {'form': form}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    edit_post = get_object_or_404(Post, id=post_id)
    if request.user != edit_post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, instance=edit_post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    template = 'posts/create_post.html'
    context = {'form': form, 'is_edit': True}
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    # Получите пост и сохраните его в переменную post.
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    list_of_posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(list_of_posts, NUM_POSTS)
    page_namber = request.GET.get('page')
    page_obj = paginator.get_page(page_namber)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    is_follower = Follow.objects.filter(user=user, author=author)
    if user != author and not is_follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    is_follower.delete()
    return redirect('posts:profile', username=author)
