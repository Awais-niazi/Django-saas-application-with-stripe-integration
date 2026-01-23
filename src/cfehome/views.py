from django.http import HttpResponse
from django.shortcuts import render
from visits.models import PageVisit
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

def landing_page_view(request):
   return render(request, "landing_page.html")


def home_view(request, *args, **kwargs):
    if request.user.is_authenticated:
        print(request.user.first_name) 
    return about_view(request, *args, **kwargs)

def about_view(request ):
    my_title = 'This is my home page'
    qs = PageVisit.objects.all()
    page_qs = PageVisit.objects.filter(path= request.path)
    try:
        percentage = (page_qs.count() * 100.0) / qs.count()
    except:
        percentage = 0    
    my_context = {

        'page_title': my_title,
        'queryset': page_qs.count(),
        'total_page_count': qs.count(),
        'percentage':percentage 
    }
    
    html_templates = 'home.html'
    path = request.path
    print('path', path)
    PageVisit.objects.create(path= request.path)
    return render(request, html_templates, my_context)


VALID_CODE = "abc123"

def pw_protected_view(request, *args, **kwargs):
    is_allowed = request.session.get('protected_page_allowed') or 0
    print(request.session.get('protected_page_allowed'), type (request.session.get('protected_page_allowed')))
    if request.method == "POST":
        user_pw_sent = request.POST.get("code") or None
        if user_pw_sent == VALID_CODE:
            is_allowed = 1
            request.session['protected_page_allowed'] = is_allowed
    if is_allowed:
        return render(request, "protected/view.html", {})
    return render(request, "protected/entry.html", {})

@login_required
def user_only_view(request, *args, **kwargs):
    #print(request.user.is_staff)
    return render(request, "protected/user-only.html", {}) 


@staff_member_required
def staff_only_view(request, *args, **kwargs):
    return render(request, "protected/user-only.html", {}) 