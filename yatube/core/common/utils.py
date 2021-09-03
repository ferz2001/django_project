from django.core.paginator import Paginator


def paginate(request, object):
    page = Paginator(object, 10)
    page_num = request.GET.get('page')
    page_obj = page.get_page(page_num)
    return page_obj
