# edc-admin-exclude


Change the ModelAdmin fields in realtime by specifying a dictionary of "exclude" lists.

A ModelForm may need to change in a longitudunal survey by adding or excluding fields based on the timepoint.

For example, on a 4 question survey administered at 4 timepoints T0, T1, T2, T3 where at T0 all four questions are asked and at T1-T3 questions 1, 2 and 4 are asked.

Since you probably have multiple forms to administered at each time point, start with `visit` model:

	class SubjectVisit(models.Model):
	
		report_datetime = models.DateTimeField()
		code = models.CharField(maxlength=10)

		class Meta:
			app_label = 'my_app'

 and create a base model class that each longitudinal model will use:

	class BaseLongitudinalModel(models.Model):
		
		subject_visit = models.ForeignKey(SubjectVisit)
		
		def get_visit_code(self)
			return self.subject_visit.visit_code

		class Meta:
			abstract = True

A longitudinal model will look like this:

	class MyModel(BaseLongitudinalModel):
		
		field1 = models.CharField(maxlength=10)
		field2 = models.CharField(maxlength=10)
		field3 = models.CharField(maxlength=10, null=True)
		field4 = models.CharField(maxlength=10)

		class Meta:
			app_label = 'my_app'

For the `edc_admin_exclude.AdminExcludeFieldsMixin`, create a base class the specifies a few required class attributes from your visit model:

	class MyAdminExcludeFieldsMixin(AdminExcludeFieldsMixin):
	
		visit_model = SubjectVisit
		visit_attr = 'subject_visit'
		visit_codes = {'baseline': ['T0'], 'annual': ['T1', T2', 'T3']}

Declare your admin class like this:

	class MyModelAdmin(MyAdminExcludeFieldsMixin, admin.ModelAdmin):
	
		fields = (
		    'subject_visit',
		    'field1', 
		    'field2', 
		    'field3', 
		    'field4'
		)
		
		custom_exclude = {'annual': ['field3']} 

	admin.site.register(MyModel, MyModelAdmin)

The baseline questionnaire (T0) shows the default fields while the annual questionnare shows all but 'field3'.

You can add instructions to the top of each form. First override the `change_form.html` as described in the Django docs. Use the block `form_top`:

	{% block form_top %}
		<b>Instructions:</b> {% for instruction in instructions %}{{ instruction|safe }}<BR>{% endfor %}
		<p><i>{{ required_instructions|safe }}</i></p>
	{% endblock %}

## TODO
Workout dependency to edc_base model admin and in a admin template
