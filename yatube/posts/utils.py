from django.core.paginator import Paginator

from .constants import NUMBER_OF_POSTS


def paginator_posts(request, posts):
    '''Отображет колличество постов на странице'''

    paginator = Paginator(posts, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')

    return paginator.get_page(page_number)
