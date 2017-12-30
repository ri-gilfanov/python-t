from .models import Category

def get_category_tree(request):
    category_roots = Category.objects.filter(parent=None)
    categories = category_roots.get_descendants(include_self=True)
    return {'category_tree': categories}
