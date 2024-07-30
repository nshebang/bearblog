from django.apps import AppConfig


class BlogsConfig(AppConfig):
    name = 'blogs'

    def ready(self):
        print("ʕ≧ᴥ≦ʔ ichoria★blogs has been activated!")

