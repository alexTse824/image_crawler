from django import forms


class SelectFilesForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    file_field = forms.FileField(widget=forms.FileInput(attrs={'multiple': True}), required=True)