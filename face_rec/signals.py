from django.db.models.signals import post_save
from django.contrib.auth.models import User,Group
from .models import student_profile

def student_profiles(sender,instance,created,**kwargs):
	if created:
		group=Group.objects.get(name='student')
		instance.groups.add(group)
		student_profile.objects.create(user=instance,name=instance.username,)
		print("Profile Created")

post_save.connect(student_profiles,sender=User)