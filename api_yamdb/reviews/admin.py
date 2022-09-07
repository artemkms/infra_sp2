from django.contrib import admin

from .models import Category, Comment, Genre, GenreTitle, Review, Title, User


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', )
    list_editable = ('role', )
    search_fields = ('username', 'role', )


admin.site.register(User, UserAdmin)
admin.site.register(Category)
admin.site.register(Genre)
admin.site.register(Title)
admin.site.register(GenreTitle)
admin.site.register(Review)
admin.site.register(Comment)
