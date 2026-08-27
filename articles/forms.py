from django import forms

from .models import Article, Newsletter


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ["title", "content", "publisher"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 10}),
        }


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ["title", "description", "articles"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "articles": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["articles"].queryset = Article.objects.filter(approved=True)
