from django import forms
from django.utils.functional import curry

TextField = curry(forms.CharField, widget = forms.Textarea) # From http://www.djangosnippets.org/snippets/1505/
