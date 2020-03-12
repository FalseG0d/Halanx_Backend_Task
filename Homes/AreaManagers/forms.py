from django import forms
from rest_framework.exceptions import ValidationError

from Homes.Houses.models import Space
from Homes.Houses.utils import SpaceAvailabilityCategories


class SpaceUpdateForm(forms.ModelForm):
    space_id = forms.IntegerField(disabled=True)

    def __init__(self, *args, **kwargs):
        super(SpaceUpdateForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['space_id'].label = ""
            self.fields['space_id'].initial = instance.pk
            self.fields['space_id'].widget.attrs['size'] = "10"
            # print(dir(self.fields['space_id']))

    def clean_space_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.id

        raise ValidationError({'detail':'Object does not exists'})

    class Meta:
        model = Space
        fields = ['space_id', 'name', 'availability', ]
