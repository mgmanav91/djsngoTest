from import_export.forms import ImportForm
from django import forms
from Store.models import Store

class PackageForm(ImportForm):
    store = forms.ChoiceField(widget=forms.Select())

    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        print(Store.objects.all())
        self.fields['store'].choices = [[0, "-- Choose Store --"]] + [[s.user_id, s.shop_name] \
                for s in Store.objects.all()]
