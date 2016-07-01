"""
V2 API
"""
import logging
import json
try:
    from urlparse import urljoin, urlparse
    from urllib import urlencode
except ImportError:
    from urllib.parse import urljoin, urlparse, urlencode

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
import jwt

from lizard_auth_server import forms
from lizard_auth_server.views_sso import (
    ProcessGetFormView,
    # get_domain,
    domain_match,
    construct_user_data,
)
from lizard_auth_server.views import ErrorMessageResponse
from lizard_auth_server.models import UserProfile


logger = logging.getLogger(__name__)


# Copied from views_sso.py
def get_domain(form):
    """Return domain for the redirect back to the site.

    Normally, the ``redirect_url`` is used. If your server is known under
    several domains, you can pass a ``domain`` GET parameter.

    Note: the domain can also have an extra path element, so
    http://some.where/something is allowed, if needed.

    """
    portal_redirect = form.site.redirect_url
    domain = form.cleaned_data.get('domain', None)

    # BBB, previously the "next" parameter was used, but django itself also
    # uses it, leading to conflicts. IF "next" starts with "http", we use it
    # and otherwise we omit it.
    next = form.cleaned_data.get('next', None)
    if next:
        if next.startswith('http'):  # Includes https :-)
            domain = next

    if domain is None:
        return portal_redirect
    netloc = urlparse(domain)[1]
    if netloc == '':
        return urljoin(portal_redirect, domain)
    if form.site.allowed_domain != '' \
            and domain_match(netloc, form.site.allowed_domain):
        return domain
    return portal_redirect


class AuthorizeView(ProcessGetFormView):
    form_class = forms.JWTDecryptForm

    def form_valid(self, form):
        self.domain = get_domain(form)
        self.site = form.site
        if self.request.user.is_authenticated():
            return self.form_valid_authenticated()
        return self.form_valid_unauthenticated(
            form.cleaned_data.get('force_sso_login', True))

    def form_invalid(self, form):
        return HttpResponse("invalid %s" % json.dumps(form.cleaned_data))

    def form_valid_authenticated(self):
        """
        Called when login succeeded.
        """
        if self.has_access():
            return self.success()
        return self.access_denied()

    def build_login_url(self):
        """
        Store the authorize view (most likely the current view) as
        "next" page for a login page.
        """
        nextparams = {
            'message': self.request.GET['message'],
            'key': self.request.GET['key'],
        }
        params = urlencode([(
            'next',
            '%s?%s' % (
                reverse('lizard_auth_server.api_v2.authorize'),
                urlencode(nextparams))
        )])
        return '%s?%s' % (reverse('django.contrib.auth.views.login'), params)

    def build_back_to_portal_url(self):
        """Redirect user back to the portal, without logging him in."""
        return urljoin(self.domain, 'sso/local_not_logged_in/')

    def form_valid_unauthenticated(self, force_sso_login):
        """
        Redirect user to login page if force_sso_login == True, else, return
        without having to log in.
        """
        if force_sso_login:
            # Typical situation -- force the user to login.
            return HttpResponseRedirect(self.build_login_url())
        else:
            # Return the unauthenticated user back to the portal.
            return HttpResponseRedirect(self.build_back_to_portal_url())

    def has_access(self):
        """
        Check whether the user has access to the portal.
        """
        if not self.request.user.is_active:
            # extra check: should not be necessary as inactive users can't
            # login anyway
            return False
        try:
            # get_profile is deprecated in Django >= 1.7
            # profile = self.request.user.get_profile()
            profile = self.request.user.user_profile
        except UserProfile.DoesNotExist:
            return False
        # TODO: check whether the UserProfile object is related to this Site
        return True

    def success(self):
        payload = {
            'key': self.site.sso_key,
            # Dump all relevant data:
            # TODO: this contains user fullname, is that sensitive info?
            # TODO: construct_user_data still uses user.user_profile, need
            # to update that to the new api.
            'user': json.dumps(construct_user_data(self.request.user)),
            }

        signed_message = jwt.encode(payload, self.site.sso_secret,
                                    algorithm='HS256')
        params = {
            'message': signed_message,
            'api_version': 'v2',
            }
        url = urljoin(self.domain, 'sso/local_login/')
        url_with_params = '%s?%s' % (url, urlencode(params))
        return HttpResponseRedirect(url_with_params)


class LogoutView(ProcessGetFormView):
    """
    View that allows portals to do some miscellaneous actions,
    like logging out.
    """
    form_class = forms.JWTDecryptForm

    def form_valid(self, form):
        next_url = reverse('lizard_auth_server.api_v2.logout_redirect')
        next_params = {
            'message': self.request.GET['message'],
            'key': self.request.GET['key'],
            # TODO: include user?
            # 'user': self.request.user.username,
        }

        # after logout redirect user to the site
        params = urlencode({
            'next': '%s?%s' % (next_url, urlencode(next_params))
            })
        url = '%s?%s' % (reverse('django.contrib.auth.views.logout'),
                         params)
        # TODO: why can't I redirect immediately to the Site using
        # the next parameter?
        return HttpResponseRedirect(url)

    def form_invalid(self, form):
        logger.error('Error while decrypting form: %s',
                     form.errors.as_text())
        return ErrorMessageResponse(self.request,
                                    _('Communication error.'),
                                    400)


class LogoutRedirectView(ProcessGetFormView):
    """
    View that redirects the user to the logout page of the portal.
    """
    form_class = forms.JWTDecryptForm

    def form_valid(self, form):
        url = urljoin(get_domain(form), 'sso/local_logout/')
        return HttpResponseRedirect(url)

    def form_invalid(self, form):
        logger.error('Error while decrypting form: %s',
                     form.errors.as_text())
        return ErrorMessageResponse(self.request,
                                    _('Communication error.'),
                                    400)
