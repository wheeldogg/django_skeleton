"""
Demo app views showcasing HTMX and Alpine.js integration.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Item
from .forms import ItemForm


def demo_home(request):
    """Demo home page showcasing the tech stack."""
    context = {
        'tech_stack': {
            'Backend': 'Django 5.1+',
            'Frontend': 'HTMX + Alpine.js',
            'CSS': 'Tailwind CSS',
            'Database': 'PostgreSQL / SQLite',
            'Cache': 'Redis',
            'Static Files': 'WhiteNoise'
        }
    }
    return render(request, 'demo/home.html', context)


class ItemListView(ListView):
    """List view with HTMX infinite scroll."""
    model = Item
    template_name = 'demo/item_list.html'
    context_object_name = 'items'
    paginate_by = 10

    def get_template_names(self):
        if self.request.htmx:
            return ['demo/partials/item_rows.html']
        return [self.template_name]


@require_http_methods(["POST", "DELETE"])
def toggle_item(request, pk):
    """Toggle item completion status via HTMX."""
    item = get_object_or_404(Item, pk=pk)

    if request.method == "DELETE":
        item.delete()
        return HttpResponse("")  # Return empty for HTMX to remove element

    item.is_completed = not item.is_completed
    item.save()

    return render(request, 'demo/partials/item_row.html', {'item': item})


@require_http_methods(["GET", "POST"])
def create_item_htmx(request):
    """Create item with HTMX."""
    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            if request.user.is_authenticated:
                item.owner = request.user
            item.save()

            if request.htmx:
                # Return the new item row for HTMX to append
                return render(request, 'demo/partials/item_row.html', {'item': item})

            messages.success(request, 'Item created successfully!')
            return redirect('demo:item-list')
    else:
        form = ItemForm()

    return render(request, 'demo/partials/item_form.html', {'form': form})


def inline_edit(request, pk):
    """Inline edit with HTMX."""
    item = get_object_or_404(Item, pk=pk)

    if request.method == "POST":
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return render(request, 'demo/partials/item_row.html', {'item': item})
    else:
        form = ItemForm(instance=item)

    return render(request, 'demo/partials/item_edit.html', {'form': form, 'item': item})


def search_items(request):
    """Search items with HTMX."""
    query = request.GET.get('q', '')
    items = Item.objects.all()

    if query:
        items = items.filter(title__icontains=query)

    return render(request, 'demo/partials/item_rows.html', {'items': items})


def alpine_examples(request):
    """Page demonstrating Alpine.js components."""
    return render(request, 'demo/alpine_examples.html')


def api_example(request):
    """Example API endpoint returning JSON."""
    data = {
        'message': 'This is a sample API response',
        'items_count': Item.objects.count(),
        'tech_stack': ['Django', 'HTMX', 'Alpine.js', 'Tailwind CSS']
    }
    return JsonResponse(data)


# Error handlers
def custom_404(request, exception):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)