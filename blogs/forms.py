from django import forms

from .models import Blog, UserSettings

import re


class BlogForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BlogForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'placeholder': 'Título de tu blog'})
        self.fields['title'].label = False
        self.fields['subdomain'].widget.attrs.update({'placeholder': 'Subdominio'})
        self.fields['subdomain'].label = False

    class Meta:
        model = Blog
        fields = ('title', 'subdomain')


class DashboardCustomisationForm(forms.ModelForm):
    dashboard_styles = forms.CharField(
        widget=forms.Textarea(),
        label="Estilo del panel",
        required=False,
        help_text="Cambia el estilo del panel con CSS."
    )

    dashboard_footer = forms.CharField(
        widget=forms.Textarea(),
        label="Contenido del pie de página",
        required=False,
        help_text="Añade scripts y demás contenido al pie de página."
    )

    class Meta:
        model = UserSettings
        fields = ('dashboard_styles', 'dashboard_footer')


class NavForm(forms.ModelForm):
    nav = forms.CharField(
        label="Nav",
        widget=forms.Textarea(attrs={'rows': 10, 'cols': 40}),
        help_text='''<span>Añade enlaces al menú de navegación o "nav" de tu blog.
                    <br>
                    [Inicio](/) [Sobre mi](/sobre-mi/) [Blog](/blog/)
                    <br>
                    Los enlaces deben ser escritos en Markdown</span>
                    ''',
        required=False,
    )

    class Meta:
        model = Blog
        fields = ('nav',)


class StyleForm(forms.ModelForm):
    custom_styles = forms.CharField(
        label="Editar tema manualmente",
        widget=forms.Textarea(),
        required=False,
        help_text="Introduce reglas de CSS personalizadas."
    )

    class Meta:
        model = Blog
        fields = ('custom_styles', )


class AdvancedSettingsForm(forms.ModelForm):
    analytics_active = forms.BooleanField(
        label="Recolección de estadísticas",
        required=False,
        help_text="Puedes deshabilitar la recopilación de estadísticas"
    )

    fathom_site_id = forms.CharField(
        max_length=20,
        required=False,
        help_text=""
    )

    meta_tag = forms.CharField(
        label="Etiqueta de metadatos personalizada",
        required=False,
        help_text="La estructura de esta etiqueta es estrictamente: &lt;meta name='' property='' content='' /&gt"
    )

    robots_txt = forms.CharField(
        widget=forms.Textarea(),
        label="Cotenido de robots.txt",
        required=False,
        help_text="Directivas para robots y web crawlers. Puedes ver tu archivo actual en tu-subdominio.ichoria.cc/robots.txt"
    )

    def clean_meta_tag(self):
        meta_tag = self.cleaned_data.get('meta_tag')
        if meta_tag:
            pattern = r'<meta\s+((?!\b(?:javascript|script|url|onerror)\b)[^>])*?>'
            if not re.search(pattern, meta_tag, re.IGNORECASE):
                raise forms.ValidationError("Etiqueta de metadatos inválida")
        return meta_tag

    class Meta:
        model = Blog
        fields = ('analytics_active', 'fathom_site_id', 'blog_path', 'rss_alias', 'meta_tag', 'robots_txt')


class AnalyticsForm(forms.ModelForm):
    fathom_site_id = forms.CharField(
        max_length=20,
        required=False,
        help_text="Ocho letras mayúsculas"
    )

    class Meta:
        model = Blog
        fields = ('fathom_site_id',)


class PostTemplateForm(forms.ModelForm):
    post_template = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 20, 'cols': 40, 'placeholder': "title: \nmeta_description: \n___\nHello world!"}),
        required=False,
        label='',
        help_text="Este será el contenido por defecto de los posts nuevos. Separa la cabecera del cuerpo con ___ (3 barras bajas)."
    )

    class Meta:
        model = Blog
        fields = ('post_template',)
