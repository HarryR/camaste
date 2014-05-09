__all__ = ('logout', 'activate', 'LoginView', 'RegisterView', 'AccountView')

from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.text import capfirst
from django.utils.http import is_safe_url
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.auth import get_user_model, authenticate, login as auth_login, logout as auth_logout

from camaste.models import Account


##############################################################################


@never_cache
def activate(request, username=None, token=None):
    user = get_object_or_404(Account, username=username)
    if user.activate_token is not None and user.activate_token == token:
        """
        Clear activation token and login
        """
        user.activate()
        user.save()
        user.backend = 'camaste.auth.Backend'
        auth_login(request, user)
    # TODO: display error message if token is invalid?
    return HttpResponseRedirect(reverse('home'))


##############################################################################


@csrf_protect
@never_cache
def logout(request, next_page=None,
           redirect_field_name="next"):
    """
    Logs out the user and redirects to homepage (or other page..)
    """
    auth_logout(request)

    if next_page is not None:
        next_page = resolve_url(next_page)
    else:
        next_page = reverse('home')

    if (redirect_field_name in request.POST or
            redirect_field_name in request.GET):
        next_page = request.POST.get(redirect_field_name,
                                     request.GET.get(redirect_field_name))
        # Security check -- don't allow redirection to a different host.
        if not is_safe_url(url=next_page, host=request.get_host()):
            next_page = request.path

    return HttpResponseRedirect(next_page)


##############################################################################



class LoginForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    username = forms.CharField(max_length=254)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': _("Please enter a correct %(username)s and password. "
                           "Note that both fields may be case-sensitive."),
        'inactive': _("This account is inactive."),
    }

    def __init__(self, request=None, *args, **kwargs):
        """
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        """
        self.request = request
        self.user_cache = None
        super(LoginForm, self).__init__(*args, **kwargs)

        # Set the label for the "username" field.
        self.username_field = Account._meta.get_field(Account.USERNAME_FIELD)
        if self.fields['username'].label is None:
            self.fields['username'].label = capfirst(self.username_field.verbose_name)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(username=username,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Controls whether the given Account may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``forms.ValidationError``.

        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache



class LoginView(FormView):
    template_name = 'camaste/login.html'
    success_url = reverse_lazy('home')

    def get_form_class(self):
        return LoginForm

    def form_valid(self, form):
        auth_login(self.request, form.get_user())
        return super(LoginView, self).form_valid(form)



##############################################################################



class RegisterForm(forms.ModelForm):
    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    username = forms.RegexField(label=_("Username"), max_length=30,
        regex=r'^[a-zA-Z0-9]{3,30}$',
        help_text=_("Required. 3 to 30 letters and numbers"),
        error_messages={'invalid': _("This value may contain only letters and numbers")})
    password1 = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = Account
        fields = ('full_name', 'username', 'email')

    def clean_username(self):
        # Since Account.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            Account._default_manager.get(username=username)
        except Account.DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2   

    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class RegisterView(CreateView):
    template_name = 'camaste/register.html'
    form_class = RegisterForm
    model = Account
    fields = ('full_name', 'username', 'email', 'password1', 'password2')    
    def get_success_url(self):
        return reverse('activate', kwargs={'username': self.object.username,
                                           'token': self.object.activate_token})


##############################################################################

class AccountForm(forms.ModelForm):
    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    username = forms.RegexField(label=_("Username"), max_length=30,
        regex=r'^[a-zA-Z0-9]{3,30}$',
        help_text=_("Required. 3 to 30 letters and numbers"),
        error_messages={'invalid': _("This value may contain only letters and numbers")})
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput,
                                required=False)
    password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput,
                                help_text=_("Enter the same password as above, for verification."),
                                required=False)

    class Meta:
        model = Account
        fields = ('full_name', 'username', 'email')

    def clean_username(self):
        # Since Account.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data.get("username")
        if 0 == len(Account.objects.filter(username=username).exclude(pk=self.instance.pk)[:1]):
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2   

    def save(self, commit=True):
        user = super(AccountForm, self).save(commit=False)
        if self.cleaned_data["password1"] != "":
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class AccountView(UpdateView):
    template_name = 'camaste/account.html'
    form_class = AccountForm
    model = Account
    success_url = reverse_lazy('account')
    fields = ('username', 'full_name', 'email', 'password1', 'password2')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('home'))
        return super(AccountView, self).dispatch(request, *args, **kwargs)
    def get_object(self, queryset=None):
        return Account.objects.get(pk=self.request.user.pk)