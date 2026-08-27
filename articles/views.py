from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from .forms import ArticleForm, NewsletterForm
from .models import Article, Newsletter
from .permissions import EditorRequiredMixin, JournalistOrEditorRequiredMixin


class ArticleListView(LoginRequiredMixin, ListView):
    """
    General article list: readers/editors/journalists see approved
    articles; journalists additionally see their own pending articles.
    """
    model = Article
    template_name = "articles/article_list.html"
    context_object_name = "articles"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        qs = Article.objects.select_related("author", "publisher")
        if user.groups.filter(name="Journalist").exists():
            from django.db.models import Q
            return qs.filter(Q(approved=True) | Q(author=user))
        return qs.filter(approved=True)


class ArticleDetailView(LoginRequiredMixin, DetailView):
    """Display the details of a single news article."""
    model = Article
    template_name = "articles/article_detail.html"
    context_object_name = "article"


class PendingArticleListView(EditorRequiredMixin, ListView):
    """Queue of unapproved articles awaiting an editor's decision."""
    model = Article
    template_name = "articles/pending_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        return Article.objects.filter(approved=False).select_related("author", "publisher")


@login_required
def approve_article(request, pk):
    """
    Approve an article. Restricted to the Editor group (or superusers).
    This is the view-level access control required by the brief; the
    actual "email subscribers + POST to /api/approved/" side effects are
    handled by the post_save signal in articles/signals.py (Option 1).
    """
    if not (request.user.is_superuser or request.user.groups.filter(name="Editor").exists()):
        messages.error(request, "Only editors may approve articles.")
        return redirect("articles:pending_list")

    article = get_object_or_404(Article, pk=pk)
    if request.method == "POST":
        article.approve(editor=request.user)
        messages.success(request, f'"{article.title}" has been approved and subscribers notified.')
        return redirect("articles:pending_list")

    return render(request, "articles/approve_confirm.html", {"article": article})


@login_required
def reject_article(request, pk):
    """Editors may also reject (delete) a submitted article."""
    if not (request.user.is_superuser or request.user.groups.filter(name="Editor").exists()):
        messages.error(request, "Only editors may reject articles.")
        return redirect("articles:pending_list")

    article = get_object_or_404(Article, pk=pk)
    if request.method == "POST":
        title = article.title
        article.delete()
        messages.success(request, f'"{title}" was rejected and removed.')
        return redirect("articles:pending_list")
    return render(request, "articles/reject_confirm.html", {"article": article})


class NewsletterListView(LoginRequiredMixin, ListView):
    """Display the list of available newsletters."""

    model = Newsletter
    template_name = "articles/newsletter_list.html"
    context_object_name = "newsletters"


class NewsletterDetailView(LoginRequiredMixin, DetailView):
    model = Newsletter
    template_name = "articles/newsletter_detail.html"
    context_object_name = "newsletter"


class NewsletterCreateView(JournalistOrEditorRequiredMixin, LoginRequiredMixin, ListView):
    """Simple function-based create is used instead; kept for URL symmetry."""
    model = Newsletter
    template_name = "articles/newsletter_list.html"


@login_required
def create_newsletter(request):
    if not request.user.groups.filter(name__in=["Journalist", "Editor"]).exists() and not request.user.is_superuser:
        messages.error(request, "Only journalists and editors may create newsletters.")
        return redirect("articles:newsletter_list")

    if request.method == "POST":
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m()
            messages.success(request, "Newsletter created.")
            return redirect("articles:newsletter_detail", pk=newsletter.pk)
    else:
        form = NewsletterForm()
    return render(request, "articles/newsletter_form.html", {"form": form})


@login_required
def create_article(request):
    """Allow journalists to create and submit articles for editorial review."""
    if not request.user.groups.filter(name="Journalist").exists() and not request.user.is_superuser:
        messages.error(request, "Only journalists may create articles.")
        return redirect("articles:article_list")

    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.approved = False
            article.save()
            messages.success(request, "Article submitted for editorial review.")
            return redirect("articles:article_list")
    else:
        form = ArticleForm()
    return render(request, "articles/article_form.html", {"form": form})
