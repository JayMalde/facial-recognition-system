from django.db import models
from django.contrib.auth.models import User

class student_profile(models.Model):
    user=models.OneToOneField(User,null=True,blank=True,on_delete=models.CASCADE)
    student_id = models.CharField(primary_key=True,max_length=20)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length = 100)
    phone = models.CharField(max_length =  50)
    email = models.CharField(max_length = 50)
    description = models.CharField(max_length = 200)
    mark = (
            ('Absent', 'Absent'),
            ('Present', 'Present'),
            ) 
    attendance = models.CharField(max_length=20,default='Absent', choices=mark)
    profile_pic=models.ImageField(default="static/images/nobody.jpg")

    def __str__(self):
        return self.student_id

class student_attendance(models.Model):
    roll=models.ForeignKey(student_profile, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=50)
    date=models.DateField(max_length=50)
    time=models.TimeField(max_length=50)

    def __str__(self):
        return self.name
