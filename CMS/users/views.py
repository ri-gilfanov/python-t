from django.shortcuts import redirect, render
from django.contrib import auth, messages
from django.template.context_processors import csrf
from random import randint
from django.utils import timezone
from .forms import SignUpForm, SecurityCodeForm, ProfileEditingForm, LegalEntityFormSet
from .models import User
from shop.models import Receipt
from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from core.sms import send_sms


def sign_in(request):
    context = {}
    context.update(csrf(request))
    context['auth_form'] = auth.forms.AuthenticationForm()
    req_POST = request.POST
    if req_POST and 'username' in req_POST and 'password' in req_POST:
        user = auth.authenticate(username=req_POST['username'], password=req_POST['password'])
        print(user, req_POST['username'], req_POST['password'])
        if user:
            auth.login(request, user)
        else:
            messages.warning(request, '<p>Ошибка. Неизвестный телефон или пароль.</p>')
    print(request.user.is_authenticated(), request.GET)
    if not request.user.is_authenticated():
        return render(request, 'users/sign_in.html', context)
    elif 'next' in request.GET:
        return redirect(request.GET['next'])
    else:
        return redirect('/')


def sign_out(request):
    auth.logout(request)
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    else:
        return redirect('/')


def sign_up(request):
    context = {}
    context.update(csrf(request))
    reqPOST = request.POST
    session = request.session
    if 'sign_up' not in session:
        if not reqPOST:
            context['form'] = SignUpForm()
        else:
            context['form'] = SignUpForm(reqPOST)
            print(context['form'].is_valid())
            if context['form'].is_valid():
                security_code = randint(1000, 9999)
                session['sign_up'] = {
                    'phone': reqPOST['phone'],
                    'first_name': reqPOST['first_name'],
                    'password': reqPOST['password1'],
                    'security_code': security_code,
                    'retry_limit': 3,
                }
                if 'wholesale_buyer_request' in reqPOST:
                    session['sign_up']['wholesale_buyer_request'] = reqPOST['wholesale_buyer_request']
                send_sms(recipient=reqPOST['phone'], text='Код безопасности: %i' % security_code)
                return redirect('/sign_up/')
    else:
        if 'security_code' not in reqPOST:
            context['form'] = SecurityCodeForm()
        else:
            context['form'] = SecurityCodeForm(reqPOST)
            sign_up_data = session['sign_up']
            phone = sign_up_data['phone']
            password = sign_up_data['password']
            first_name = sign_up_data['first_name']
            wholesale_buyer_request = False
            if (
                'wholesale_buyer_request' in sign_up_data
                and sign_up_data['wholesale_buyer_request'] == 'on'
            ):
                wholesale_buyer_request = True
            if context['form'].is_valid():
                if context['form'].cleaned_data['security_code'] == sign_up_data['security_code']:
                    user = User.objects.create_user(phone, password, first_name=first_name, wholesale_buyer_request=wholesale_buyer_request)
                    session.pop('sign_up')
                    user = auth.authenticate(phone=phone, password=password)
                    auth.login(request, user)
                    return redirect('/')
                elif session['sign_up']['retry_limit'] > 0:
                    sign_up_data['retry_limit'] -= 1
                    session.__setitem__('sign_up', sign_up_data)
                if session['sign_up']['retry_limit'] == 0:
                    session.pop('sign_up')
                    return redirect('/sign_up/')
    return render(request, 'users/sign_up.html', context)


@login_required
def get_profile(request):
    context = {}
    return render(request, 'users/profile.html', context)


@login_required
def get_profile_editing(request):
    context = {}
    context.update(csrf(request))
    form = ProfileEditingForm()
    if request.method == 'POST':
        form = ProfileEditingForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
    else:
        form = ProfileEditingForm(instance=request.user)
    context['form'] = form
    return render(request, 'users/profile__editing.html', context)


@login_required
def get_profile_buyer_receipts(request):
    context = {}
    receipts = Receipt.objects.filter(buyer=request.user).prefetch_related(
        'order_set__product__price_set__buyer_type',
    ).select_related('buyer__buyer_type')
    context['receipts'] = receipts
    return render(request, 'users/profile__buyer_receipts.html', context)


@login_required
def get_profile_buyer_receipt(request, pk):
    context = {}
    receipt = Receipt.objects.get(pk=pk)
    orders = receipt.order_set.all().prefetch_related('product__price_set__buyer_type')
    context['receipt'] = receipt
    context['orders'] = orders
    context['buyer'] = request.user
    return render(request, 'users/profile__buyer_receipt.html', context)


@login_required
def get_legal_entities_editing(request):
    context = {}
    context.update(csrf(request))
    if request.method == 'POST':
        formset = LegalEntityFormSet(request.POST, instance=request.user)
        if formset.is_valid():
            formset.save()
            return redirect('/profile/legal_entities/')
    else:
        formset = LegalEntityFormSet(instance=request.user)
    context['formset'] = formset
    return render(request, 'users/profile__legal_entity_editing.html', context)


@login_required
def get_profile_settings(request):
    context = {}
    return render(request, 'users/profile__access.html', context)
