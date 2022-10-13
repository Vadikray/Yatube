from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, Follow, User
from .forms import PostForm, CommentForm
from .utils import paginator_posts


@cache_page(20, key_prefix='index_page')
def index(request):
    '''Обработка основной страницы сайта'''

    template = 'posts/index.html'
    posts = Post.objects.select_related(
        'author'
    ).all()

    context = {
        'page_obj': paginator_posts(request, posts),
    }

    return render(request, template, context)


def group_posts(request, slug):
    '''Обработка страницы группы'''

    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'page_obj': paginator_posts(request, posts),
    }

    return render(request, template, context)


def profile(request, username):
    '''Обработка страницы пользователя'''

    template = 'posts/profile.html'
    author = get_object_or_404(
        User.objects,
        username=username,
    )
    following = False
    posts_autor = author.posts.all()
    if request.user.is_authenticated:
        following = True if Follow.objects.filter(
            user=request.user,
            author=author,
        ).count() > 0 else False

    context = {
        'page_obj': paginator_posts(request, posts_autor),
        'author': author,
        'following': following,
    }

    return render(request, template, context)


def post_detail(request, post_id):
    '''Обработка странцы поста'''

    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.select_related('post', 'author')
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    '''Обработка страницы создания поста'''

    template = 'posts/create_post.html'

    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = User.objects.get(pk=request.user.id)
        post.save()

        return redirect('posts:profile', request.user.username)

    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    '''Обработка страницы редактирования поста'''

    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()

        return redirect('posts:post_detail', post_id)

    context = {
        'is_edit': True,
        'form': form,
        'post': post
    }

    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    '''Вью-функция добавления комментария'''

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
    '''Обработка страницы подписаок автора'''

    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    following_count = Follow.objects.filter(
        author__following__user=request.user).count()
    context = {
        'user': request.user,
        'page_obj': paginator_posts(request, posts),
        'following_count': following_count,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    '''Обработка страницы подписки на автора'''

    author = get_object_or_404(User, username=username)
    if request.user == author or Follow.objects.filter(
        user=request.user,
        author=author,
    ):
        return redirect('posts:profile', username=username)
    Follow.objects.create(user=request.user, author=author)

    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    '''Обработка страницы отписки от автора'''

    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()

    return redirect('posts:follow_index')
