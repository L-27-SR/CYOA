from django import forms

class BookForm(forms.Form):
    book_title = forms.CharField(label="Book or Movie title", max_length=255, widget=forms.TextInput(attrs={"placeholder":"e.g. Harry Potter and the Philosopher's Stone"}))

class CharacterChoiceForm(forms.Form):
    character = forms.CharField(widget=forms.HiddenInput())


class SignupForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"placeholder": "username"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "password"}))


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"placeholder": "username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "password"}))
