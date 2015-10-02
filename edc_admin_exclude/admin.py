from more_itertools import unique_everseen

from django.conf import settings
from copy import copy
from django.core.exceptions import ImproperlyConfigured


class AdminExcludeFieldsMixin(object):

    """Model Admin for models with a foreignkey to the subject visit model."""

    visit_model = None
    visit_attr = None
    visit_codes = {}
    original_fields = None

    def __init__(self, *args, **kwargs):
        super(AdminExcludeFieldsMixin, self).__init__(*args, **kwargs)
        self.original_fields = copy(self.fields)
        for fields in self.custom_exclude.values():
            unknown_fields = [f for f in fields if f not in self.original_fields]
            if unknown_fields:
                raise ImproperlyConfigured(
                    'Custom exclude field(s) {} not found in ModelAdmin.field list. '
                    'See \'{}\''.format(unknown_fields, self.__class__.__name__))

    def get_custom_exclude(self, request, obj=None):
        exclude = []
        try:
            if obj:
                code = getattr(obj, self.visit_attr).get_visit_code()
            else:
                code = request.GET.get(self.visit_attr).get_visit_code()
        except AttributeError:
            try:
                code = settings.ADMIN_EXCLUDE_DEFAULT_CODE
            except AttributeError:
                code = None
        if code:
            exclude = self.custom_exclude.get(self.get_label(code), [])
        return exclude

    def get_label(self, code):
        if code:
            for label, code_list in self.visit_codes.items():
                if code in code_list:
                    return label
        return None

    def get_fields(self, request, obj=None):
        if self.original_fields:
            return [f for f in self.original_fields if f not in self.get_custom_exclude(request, obj)]
        form = self.get_form(request, obj, fields=None)
        return list(form.base_fields) + list(unique_everseen(self.get_readonly_fields(request, obj)))

    def get_form(self, request, obj=None, **kwargs):
        self.fields = self.get_fields(request, obj)
        kwargs.update({'exclude': self.get_custom_exclude(request, obj)})
        form = super(AdminExcludeFieldsMixin, self).get_form(request, obj, **kwargs)
        return form
