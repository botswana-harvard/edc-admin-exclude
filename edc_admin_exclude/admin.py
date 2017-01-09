from django.conf import settings
from copy import copy
from django.core.exceptions import ImproperlyConfigured


class AdminExcludeFieldsMixin:

    """Declare with edc_visit tracking CrfModelMixin."""

    visit_codes = {}

    def __init__(self, *args, **kwargs):
        super(AdminExcludeFieldsMixin, self).__init__(*args, **kwargs)
        self._original_fields = None
        try:
            self.original_instructions = copy(self.instructions)
        except AttributeError:
            self.original_instructions = None
        if not self.visit_codes:
            raise ImproperlyConfigured(
                'Attribute visit_codes may not be None. Declare as a class attribute on the ModelAdmin')

    @property
    def original_fields(self):
        if not self._original_fields:
            self._original_fields = list(copy(self.fields))
            try:
                exclude = self.custom_exclude.values()
                for fields in exclude:
                    unknown_fields = [f for f in fields if f not in self.original_fields]
                    if unknown_fields:
                        raise ImproperlyConfigured(
                            'Custom exclude field(s) {} not found in ModelAdmin.field list. '
                            'See \'{}\''.format(unknown_fields, self.__class__.__name__))
            except AttributeError:
                pass
        return self._original_fields

    def contribute_to_extra_context(self, extra_context, request=None, object_id=None):
        extra_context = super(AdminExcludeFieldsMixin, self).contribute_to_extra_context(
            extra_context, request=request, object_id=object_id)
        visit_code = self.get_visit_code(request, object_id=object_id)
        instructions = self.get_custom_instructions(self.get_key(visit_code))
        extra_context.update(instructions=instructions)
        extra_context.update(admin_exclude_code=visit_code)
        return extra_context

    def get_form(self, request, obj=None, **kwargs):
        """Returns a form but customizes the fields list first."""
        visit_code = self.get_visit_code(request, obj)
        self.fields = self.get_custom_fields(request, obj, visit_code=visit_code)
        kwargs.update({'fields': self.fields, 'exclude': self.get_custom_exclude(request, obj)})
        return super(AdminExcludeFieldsMixin, self).get_form(request, obj, **kwargs)

    def get_fields(self, request, obj=None):
        """Returns fields but sets the fields attr before calling super."""
        self.fields = self.get_custom_fields(request, obj)
        return super(AdminExcludeFieldsMixin, self).get_fields(request, obj)

    def get_custom_fields(self, request, obj=None, visit_code=None):
        """Returns a list of field names less those to be excluded for the \'visit\' or None."""
        if self.original_fields:
            visit_code = visit_code or self.get_visit_code(request, obj)
            return list([f for f in self.original_fields if f not in self.get_custom_exclude(
                request, obj, visit_code)])
        return None

    def get_custom_exclude(self, request, obj=None, visit_code=None):
        """Returns a list of fields to be excluded."""
        exclude = []
        visit_code = visit_code or self.get_visit_code(request, obj)
        if visit_code:
            try:
                exclude = self.custom_exclude.get(self.get_key(visit_code), [])
            except AttributeError:
                pass
        return list(exclude)

    def get_custom_instructions(self, key):
        """Returns instructions for this \'key\' as a list."""
        try:
            instructions = self.original_instructions.get(key)
        except KeyError:
            instructions = None
        except AttributeError:
            instructions = self.original_instructions
        return instructions

    def get_visit_code(self, request, obj=None, object_id=None):
        """Returns the visit code from the instance or settings attr or returns None."""
        try:
            visit_code = self.get_visit(request, obj=obj, object_id=object_id).get_visit_code()
        except AttributeError:
            try:
                visit_code = settings.ADMIN_EXCLUDE_DEFAULT_CODE
            except AttributeError:
                visit_code = None
        return visit_code

    def get_visit(self, request, obj=None, object_id=None):
        """Returns a visit instance using the model instance or the request object or None."""
        visit_instance = None
        try:
            if obj:
                visit_instance = getattr(obj, self.visit_model_attr)
            elif object_id:
                visit_instance = self.model.objects.get(pk=object_id)
            else:
                pk = request.GET.get(self.visit_model_attr)
                if pk:
                    visit_instance = self.visit_model.objects.get(pk=pk)
        except AttributeError:
            pass
        return visit_instance

    def get_key(self, visit_code):
        """Returns the dictionary 'key' if the visit_code is in the dictionary 'value'."""
        if visit_code:
            for key, visit_code_list in self.visit_codes.items():
                if visit_code in visit_code_list:
                    return key
        return None
