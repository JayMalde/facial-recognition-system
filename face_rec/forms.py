from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


# class StudentForm(ModelForm):
# 	class Meta():
# 		model=Student
# 		fields='__all__'
# 		exclude=['user']		

class CreateUserForm(UserCreationForm):
	class Meta:
		model=User
		fields=['username','email','password1','password2']

