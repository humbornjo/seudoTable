"""seudo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic.base import RedirectView
from . import views

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('workspace/',views.workspace,name="workspace"),
    path('workspace/upload', views.upload, name='upload'),
    path('workspace/export', views.export, name="export"),
    path('workspace/aboutus', views.aboutus, name="aboutus"),
    path('workspace/tablist', views.tablist, name="tablist"),
    path('workspace/neCols_ajax_handle', views.check_neCols, name="necheck"),
    path('workspace/table/<int:table_id>', views.neCols_select, name='start'),
    path('workspace/table/reset/<int:table_id>', views.reset, name='reset'),
    path('workspace/table/direct/<int:table_id>', views.direct_search, name='direct'),
    path('workspace/table/seudo/<int:table_id>', views.seudo_search, name='seudo'),
    path('workspace/table/download/<int:table_id>', views.download, name="download"),
]
