# -*- coding: utf-8 -*-
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.db import transaction
from django.db.models import F
from django.db.models.query_utils import Q
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _
from lizard_auth_server.utils import gen_secret_key

import datetime
import logging
import pytz
import uuid


BILLING_ROLE = "billing"
THREEDI_PORTAL = "3Di"


logger = logging.getLogger(__name__)


@deconstructible
class GenKey(object):
    """
    Helper function to give a unique default value to the selected
    field in a model.

    Note: Field.default needs to be serializable (a change since Django 1.7).
    Here we use the deconstruct method described in:
    https://code.djangoproject.com/ticket/22999
    https://docs.djangoproject.com/en/1.9/topics/migrations/#adding-a-deconstruct-method
    """

    def __init__(self, model, field):
        self.model = model
        self.field = field

    def __call__(self):
        if isinstance(self.model, str):
            ModelClass = apps.get_app_config("lizard_auth_server").get_model(self.model)
            if not ModelClass:
                raise Exception("Unknown model {}".format(self.model))
        else:
            ModelClass = self.model
        key = gen_secret_key(64)
        while ModelClass.objects.filter(**{self.field: key}).exists():
            key = gen_secret_key(64)
        return key

    def __eq__(self, other):
        return all([self.model == other.model, self.field == other.field])


class Portal(models.Model):
    """
    A portal. If secret/key change, the portal website has to be updated too!
    """

    name = models.CharField(
        verbose_name=_("name"),
        max_length=255,
        null=False,
        blank=False,
        help_text=_("Name used to refer to this portal."),
    )
    sso_secret = models.CharField(
        verbose_name=_("shared secret"),
        max_length=64,
        unique=True,
        default=GenKey("Portal", "sso_secret"),
        help_text=_(
            "Secret shared between SSO client and "
            "server to sign/encrypt communication."
        ),
    )
    sso_key = models.CharField(
        verbose_name=_("identifying key"),
        max_length=64,
        unique=True,
        default=GenKey("Portal", "sso_key"),
        help_text=_("String used to identify the SSO client."),
    )
    allowed_domain = models.CharField(
        verbose_name=_("allowed domain(s)"),
        max_length=255,
        default="unused in v2 api",
        help_text=_(
            "Allowed domain suffix for redirects using the next parameter. "
            "Multiple, whitespace-separated suffixes may be specified."
        ),
    )
    redirect_url = models.CharField(
        verbose_name=_("redirect url"),
        max_length=255,
        default="http://unused.in/v2/api",
        help_text=_("URL used in the SSO redirection."),
    )
    visit_url = models.CharField(
        verbose_name=_("visit url"),
        max_length=255,
        help_text=_("URL used in the UI to refer to this portal."),
    )
    allow_migrate_user = models.BooleanField(
        default=False, help_text="Whether to allow the migrate_user v2 api"
    )

    def __str__(self):
        return self.name

    def rotate_keys(self):
        self.sso_secret = GenKey(Portal, "sso_secret")()
        self.sso_key = GenKey(Portal, "sso_key")()
        self.save()

    class Meta:
        ordering = ("name",)
        verbose_name = _("portal")
        verbose_name_plural = _("portals")


class TokenManager(models.Manager):
    def create_for_portal(self, portal):
        """
        Create a new token for a portal object.
        """
        request_token = gen_secret_key(64)
        auth_token = gen_secret_key(64)
        # check unique constraints
        while self.filter(
            Q(request_token=request_token) | Q(auth_token=auth_token)
        ).exists():
            request_token = gen_secret_key(64)
            auth_token = gen_secret_key(64)
        return self.create(
            portal=portal,
            request_token=request_token,
            auth_token=auth_token,
        )


def token_creation_date():
    return datetime.datetime.now(tz=pytz.UTC)


class Token(models.Model):
    """
    An auth token used to authenticate a user.
    """

    portal = models.ForeignKey(
        Portal, verbose_name=_("portal"), on_delete=models.CASCADE
    )
    request_token = models.CharField(
        verbose_name=_("request token"), max_length=64, unique=True
    )
    auth_token = models.CharField(
        verbose_name=_("auth token"), max_length=64, unique=True
    )
    user = models.ForeignKey(
        User,
        verbose_name=_("user"),
        related_name="user_tokens",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(
        verbose_name=_("created at"), default=token_creation_date
    )

    objects = TokenManager()

    class Meta:
        verbose_name = _("(authentication token)")
        verbose_name_plural = _("(authentication tokens)")
        ordering = ("-created",)


class UserProfileManager(models.Manager):
    def fetch_for_user(self, user):
        if not user:
            raise AttributeError("Can't get UserProfile without user")
        return self.get(user=user)


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        verbose_name=_("user"),
        related_name="user_profile",
        on_delete=models.CASCADE,
    )

    portals = models.ManyToManyField(
        Portal,
        verbose_name=_("portals"),
        help_text="only used in the old v1 api",
        related_name="user_profiles",
        blank=True,
    )
    organisations = models.ManyToManyField(
        "Organisation",
        verbose_name=_("organisations"),
        help_text="only used in the old v1 api",
        related_name="user_profiles",
        blank=True,
    )
    roles = models.ManyToManyField(
        "OrganisationRole",
        related_name="user_profiles",
        help_text="only used in the old v1 api",
        verbose_name=_("roles (via organisation)"),
        blank=True,
    )

    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated on"), auto_now=True)
    migrated_at = models.DateTimeField(
        help_text="The last time the cognito/migrate_user was called for this user",
        null=True,
        blank=True,
    )

    objects = UserProfileManager()

    class Meta:
        verbose_name = _("user profile")
        verbose_name_plural = _("user profiles")
        ordering = ["user__username"]

    def __str__(self):
        if self.user:
            return "{}".format(self.user)
        else:
            return "UserProfile {}".format(self.pk)

    def update_all(self, data):
        self.user.email = data["email"]
        self.user.first_name = data["first_name"]
        self.user.last_name = data["last_name"]
        self.user.save()

    @property
    def username(self):
        return self.user.username

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def email(self):
        return self.user.email

    @property
    def organisation(self):
        """Return the name of one of this user's organisations, or None.

        For backward compatibility. Instead of many Organisation objects, a
        user used to have a single organisation string."""
        try:
            return self.organisations.all().order_by("id")[0:1].get().name
        except Organisation.DoesNotExist:
            return None

    @property
    def is_active(self):
        """
        Returns True when the account is active, meaning the User has not been
        deactivated by an admin.

        Note: unrelated to account activation.
        """
        return self.user.is_active

    def has_access(self, portal):
        """
        Returns True when this user has access to this portal.
        """
        if not portal:
            raise AttributeError("Need a valid Portal instance")
        if self.user.is_staff:
            # staff can access any site
            return True
        return self.portals.filter(pk=portal.pk).exists()

    def all_organisation_roles(self, portal, return_explanation=False):
        """Return a queryset of OrganisationRoles that apply to this profile.

        If ``return_explanation`` is True, return a dict with explanatory
        results, instead.
        """
        # First grab all applicable roles.
        relevant_roles_tied_to_the_portal = Role.objects.filter(portal=portal)

        # Two Q objects for filtering organisation roles I have access
        # to. Either directly via my profile or via for_all_users.
        tied_to_my_organisation_for_all_users = models.Q(
            for_all_users=True, organisation__user_profiles=self
        )
        tied_to_my_user_profile = models.Q(user_profiles=self)
        # All organisation roles I have access to. This does not yet take into
        # account the organisation roles I get via the role inheritance
        organisation_roles_i_can_access = OrganisationRole.objects.filter(
            tied_to_my_organisation_for_all_users | tied_to_my_user_profile
        )

        # Two criteria for filtering organisation roles.

        # The simple case is that an organisation role is both in our access
        # list AND it points at a relevant role. Bingo.
        relevant_role_and_direct_access = models.Q(
            id__in=organisation_roles_i_can_access,
            role__in=relevant_roles_tied_to_the_portal,
        )

        # The elaborate case is that a role must of course be a relevant
        # role. Then that same role must have a base role with an organisation
        # role that I can access. That same organisation role must also have
        # the same organisation as the organisation role I'm looking
        # from. Django ensures those "the same" items are really the
        # same.
        relevant_role_and_indirect_access_with_matching_org = models.Q(
            role__in=relevant_roles_tied_to_the_portal,
            role__base_roles__organisation_roles__in=organisation_roles_i_can_access,
            role__base_roles__organisation_roles__organisation=F("organisation"),
        )

        results = OrganisationRole.objects.filter(
            relevant_role_and_direct_access
            | relevant_role_and_indirect_access_with_matching_org
        ).distinct()

        if return_explanation:
            organisation_roles_directly = OrganisationRole.objects.filter(
                tied_to_my_user_profile
            )
            organisation_roles_via_organisation = OrganisationRole.objects.filter(
                tied_to_my_organisation_for_all_users
            ).distinct()
            direct_results = OrganisationRole.objects.filter(
                relevant_role_and_direct_access
            ).distinct()
            indirect_results = OrganisationRole.objects.filter(
                relevant_role_and_indirect_access_with_matching_org
            ).distinct()

            return {
                "relevant_roles_tied_to_the_portal": relevant_roles_tied_to_the_portal,
                "organisation_roles_directly": organisation_roles_directly,
                "organisation_roles_via_organisation": organisation_roles_via_organisation,
                "direct_results": direct_results,
                "indirect_results": indirect_results,
                "results": results,
            }

        return results


class Invitation(models.Model):
    name = models.CharField(
        verbose_name=_("name"), max_length=255, null=False, blank=False
    )
    email = models.EmailField(verbose_name=_("e-mail"), null=False, blank=False)
    organisation = models.CharField(
        verbose_name=_("organisation"), max_length=255, null=False, blank=False
    )
    language = models.CharField(
        verbose_name=_("language"), max_length=16, null=False, blank=False
    )
    portals = models.ManyToManyField(Portal, verbose_name=_("portals"), blank=True)
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    activation_key = models.CharField(
        verbose_name=_("activation key"),
        max_length=64,
        null=True,
        blank=True,
        unique=True,
    )
    activation_key_date = models.DateTimeField(
        verbose_name=_("activation key date"),
        null=True,
        blank=True,
        help_text=_(
            "Date on which the activation key was generated. " "Used for expiration."
        ),
    )
    is_activated = models.BooleanField(verbose_name=_("is activated"), default=False)
    activated_on = models.DateTimeField(
        verbose_name=_("activated on"), null=True, blank=True
    )
    user = models.ForeignKey(
        User, verbose_name=_("user"), null=True, blank=True, on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("(invitation)")
        verbose_name_plural = _("(invitation)")
        ordering = ["is_activated", "-created_at", "email"]

    def __str__(self):
        return "invitation for %s" % self.email

    def clean(self):
        if self.is_activated:
            if self.user is None:
                raise ValidationError(
                    "Invitation is marked as activated, but its " "user is not set."
                )
            if self.activated_on is None:
                raise ValidationError(
                    "Invitation is marked as activated, but its "
                    'field "activated_on" is not set.'
                )

    def _rotate_activation_key(self):
        if self.is_activated:
            raise Exception("user is already activated")

        # generate a new activation key
        self.activation_key = GenKey(Invitation, "activation_key")()

        # update key date so we can check for expiration
        self.activation_key_date = datetime.datetime.now(tz=pytz.UTC)
        self.save()

    def get_context(self, **extra):
        """Create the context for rendering the invitation email."""
        username = self.user.username if self.user else self.name
        context = {
            "name": username,
            "activation_key": self.activation_key,
            "expiration_days": settings.ACCOUNT_ACTIVATION_DAYS,
            "site_name": settings.SITE_NAME,
            "site_public_url_prefix": settings.SITE_PUBLIC_URL_PREFIX,
            "invitation": self,
        }
        context.update(extra)
        return context

    def send_new_activation_email(self):
        if self.is_activated:
            raise Exception("user is already activated")

        # generate a fresh key
        self._rotate_activation_key()

        # send this user an email containing the key
        # build a render context for the email template
        expiration_date = datetime.datetime.now(tz=pytz.UTC) + datetime.timedelta(
            days=settings.ACCOUNT_ACTIVATION_DAYS
        )

        ctx_dict = self.get_context(expiration_date=expiration_date)

        # switch to the users language
        old_lang = translation.get_language()
        translation.activate(self.language)

        # render the email subject and message using Django's templating
        subject = render_to_string(
            "lizard_auth_server/invitation_email_subject.txt", ctx_dict
        )
        # ensure email subject doesn't contain newlines
        subject = "".join(subject.splitlines())
        message = render_to_string("lizard_auth_server/invitation_email.html", ctx_dict)

        # switch language back
        translation.activate(old_lang)

        # send the actual email
        send_mail(subject, message, None, [self.email])

    def create_user(self, data):
        with transaction.atomic():
            if self.user is None:
                # create the Django auth user
                user = User.objects.create_user(
                    username=data["username"], password=data["new_password1"]
                )

                # immediately deactivate this user, no way to do this directly
                user.is_active = False
                user.save()

                # link the new user to the invitation
                self.user = user
                self.save()
            else:
                logger.warn(
                    "This invitation already has a user linked to it: %s", self.user
                )

    def activate(self, data):
        with transaction.atomic():
            user = self.user

            # create and fill the profile
            # this sets the additional attributes on the User model as well
            # get_profile deprecated in Django >= 1.7
            # profile = user.get_profile()
            profile = user.user_profile
            profile.update_all(data)

            # many-to-many, so save these after profile has been assigned an ID
            organisation, created = Organisation.objects.get_or_create(
                name=self.organisation
            )
            profile.organisations.add(organisation)

            profile.portals = self.portals.all()
            profile.save()

            # and mark the User as active
            user.is_active = True
            user.save()

            # set the activation flag on the Invitation
            self.activated_on = datetime.datetime.now(tz=pytz.UTC)
            self.is_activated = True
            self.save()


def create_new_uuid():
    return uuid.uuid4().hex


class RoleManager(models.Manager):
    def get_queryset(self):
        return super(RoleManager, self).get_queryset().select_related("portal")


class Role(models.Model):
    portal = models.ForeignKey(
        Portal, related_name="roles", verbose_name=_("portal"), on_delete=models.CASCADE
    )
    unique_id = models.CharField(
        verbose_name=_("unique id"),
        max_length=32,
        editable=False,
        unique=True,
        default=create_new_uuid,
    )
    code = models.CharField(
        verbose_name=_("code"),
        max_length=255,
        help_text=_("name used internally by the portal to identify the role"),
        null=False,
        blank=False,
    )
    name = models.CharField(
        verbose_name=_("name"),
        help_text=_("human-readable name"),
        max_length=255,
        null=False,
        blank=False,
    )
    inheriting_roles = models.ManyToManyField(
        "self",
        verbose_name=_("inheriting roles"),
        symmetrical=False,
        related_name="base_roles",
        help_text=_(
            "roles that are automatically inherited from us for "
            "organisations that have organisation roles pointing at "
            "both base and inheriting role."
        ),
        blank=True,
    )

    external_description = models.TextField(
        verbose_name=_("external description"), blank=True
    )
    internal_description = models.TextField(
        verbose_name=_("internal description"), blank=True
    )

    objects = RoleManager()

    class Meta:
        ordering = ["portal", "name"]
        unique_together = (("name", "portal"),)
        verbose_name = _("(role)")
        verbose_name_plural = _("(roles)")

    def __str__(self):
        return _("{name} on {portal}").format(name=self.name, portal=self.portal.name)

    def as_dict(self):
        return {
            "unique_id": self.unique_id,
            "code": self.code,
            "name": self.name,
            "external_description": self.external_description,
            "internal_description": self.internal_description,
        }


class Organisation(models.Model):
    name = models.CharField(
        verbose_name=_("name"), max_length=255, null=False, blank=False, unique=True
    )
    unique_id = models.CharField(
        verbose_name=_("unique id"), max_length=32, unique=True, default=create_new_uuid
    )
    roles = models.ManyToManyField(
        Role, through="OrganisationRole", verbose_name=_("roles"), blank=True
    )

    class Meta:
        ordering = ["name"]
        verbose_name = _("organisation")
        verbose_name_plural = _("organisations")

    def __str__(self):
        return self.name

    def as_dict(self):
        return {"name": self.name, "unique_id": self.unique_id}


class OrganisationRoleManager(models.Manager):
    def get_queryset(self):
        # Always use select_related on role and organisation, otherwise we
        # have to specify it in a *lot* of places.
        return (
            super(OrganisationRoleManager, self)
            .get_queryset()
            .select_related("role", "organisation", "role__portal")
        )


class OrganisationRole(models.Model):
    organisation = models.ForeignKey(
        Organisation,
        related_name="organisation_roles",
        verbose_name=_("organisation"),
        on_delete=models.CASCADE,
    )
    role = models.ForeignKey(
        Role,
        related_name="organisation_roles",
        verbose_name=_("role"),
        on_delete=models.CASCADE,
    )
    for_all_users = models.BooleanField(verbose_name=_("for all users"), default=False)

    objects = OrganisationRoleManager()

    class Meta:
        unique_together = (("organisation", "role"),)
        verbose_name = _("(organisation-role-mapping)")
        verbose_name_plural = _("(organisation-role-mappings)")

    def __str__(self):
        if self.for_all_users:
            return _("{role} for everybody in {org}").format(
                role=self.role, org=self.organisation
            )
        else:
            return "{role} in {org}".format(role=self.role, org=self.organisation)

    def clean(self):
        if self.role.code != BILLING_ROLE:
            return
        if self.role.portal.name != THREEDI_PORTAL:
            return
        # Hardcoded: we point at the 3di 'billing' role.
        if self.for_all_users:
            raise ValidationError(
                {
                    "for_all_users": [
                        _(
                            "The special 3di billing role is not allowed "
                            '"for all users"'
                        )
                    ]
                }
            )

    def as_dict(self):
        return {
            "organisation": self.organisation.as_dict(),
            "role": self.role.as_dict(),
        }
