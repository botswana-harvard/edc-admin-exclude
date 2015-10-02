from django.contrib import admin
from django.db import models
from django.test import TestCase
from edc_admin_fields.admin import AdminExcludeFieldsMixin
from django.utils import timezone
from django.test.utils import override_settings
from django.test.client import RequestFactory
from django.core.exceptions import ImproperlyConfigured


class Visit(models.Model):

    visit_datetime = models.DateTimeField(default=timezone.now())
    code = models.CharField(max_length=25, null=True)

    def get_visit_code(self):
        return self.code

    class Meta:
        app_label = 'edc_admin_fields'


class MyTestModel(models.Model):

    visit = models.ForeignKey(Visit)
    field1 = models.CharField(max_length=25, null=True)
    field2 = models.CharField(max_length=25, null=True)
    field3 = models.CharField(max_length=25, null=True)
    field4 = models.CharField(max_length=25, null=True)

    class Meta:
        app_label = 'edc_admin_fields'


class MyTestModelAdmin(AdminExcludeFieldsMixin, admin.ModelAdmin):

    visit_model = Visit
    visit_attr = 'visit'
    visit_codes = {'annual': ['T1', 'T2', 'T3']}
    fields = ('field1', 'field2', 'field3', 'field4')
    custom_exclude = {'annual': ['field3']}


class BadTestModelAdmin(AdminExcludeFieldsMixin, admin.ModelAdmin):

    visit_model = Visit
    visit_attr = 'visit'
    visit_codes = {'annual': ['T1', 'T2', 'T3']}
    fields = ('field1', 'field2', 'field3', 'field4')
    custom_exclude = {'annual': ['field3', 'field7']}


class TestAdminFields(TestCase):

    def setUp(self):

        try:
            del admin.site._registry[MyTestModel]
        except KeyError:
            pass
        admin.site.register(MyTestModel, MyTestModelAdmin)
        admin.autodiscover()
        self.model_admin = admin.site._registry.get(MyTestModel)

    def test_bad(self):
        try:
            del admin.site._registry[MyTestModel]
        except KeyError:
            pass
        self.assertRaises(ImproperlyConfigured, admin.site.register, MyTestModel, BadTestModelAdmin)

    def test_set_fields_by_visit_code(self):
        visit = Visit.objects.create(code='T1')
        MyTestModel.objects.create(visit=visit)
        request = RequestFactory()
        request.GET = {'visit': visit}
        form = self.model_admin.get_form(request)
        self.assertEqual(form.base_fields.keys(), ['field1', 'field2', 'field4'])

    def test_set_fields_by_visit_code2(self):
        visit = Visit.objects.create(code='T0')
        MyTestModel.objects.create(visit=visit)
        request = RequestFactory()
        request.GET = {'visit': visit}
        form = self.model_admin.get_form(request)
        self.assertEqual(form.base_fields.keys(), ['field1', 'field2', 'field3', 'field4'])

    @override_settings(ADMIN_EXCLUDE_DEFAULT_CODE='T1')
    def test_set_fields_by_visit_code3(self):
        visit = Visit.objects.create(code='T0')
        MyTestModel.objects.create(visit=visit)
        request = RequestFactory()
        request.GET = {'visit': None}
        form = self.model_admin.get_form(request)
        self.assertEqual(form.base_fields.keys(), ['field1', 'field2', 'field4'])

    @override_settings(ADMIN_EXCLUDE_DEFAULT_CODE='T0')
    def test_set_fields_by_visit_code4(self):
        visit = Visit.objects.create(code='T0')
        MyTestModel.objects.create(visit=visit)
        request = RequestFactory()
        request.GET = {'visit': None}
        form = self.model_admin.get_form(request)
        self.assertEqual(form.base_fields.keys(), ['field1', 'field2', 'field3', 'field4'])

    @override_settings(ADMIN_EXCLUDE_DEFAULT_CODE='T0')
    def test_set_fields_by_visit_code5(self):
        request = RequestFactory()
        form = self.model_admin.get_form(request)
        self.assertEqual(form.base_fields.keys(), ['field1', 'field2', 'field3', 'field4'])
