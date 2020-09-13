from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from .forms import CreateUserForm
from django.contrib.auth.decorators import login_required
from face_recognition_system.settings import BASE_DIR
from .models import student_profile,student_attendance
from django.views import View
from django.core.mail import EmailMessage
from django.conf import settings
from .decorators import unauthenticated_user,allowed_users,admin_only
import os
import cv2
from PIL import Image
import numpy as np
import pandas as pd
import time
import datetime
import csv

@login_required(login_url='login')
@allowed_users(allowed_roles=['teacher','admin'])
def create_dataset(request):        
    Id=request.POST['userId']
    name=request.POST['userId1']
    cam = cv2.VideoCapture(0)
    detector = cv2.CascadeClassifier(BASE_DIR+'/algorithms/haarcascade_frontalface_default.xml')
    sampleNum=0
    while(True):
        ret, img = cam.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)
        for (x,y,w,h) in faces:
            cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)        
            #incrementing sample number 
            sampleNum=sampleNum+1
            #saving the captured face in the dataset folder TrainingImage
            cv2.imwrite(BASE_DIR+"/static/images/TrainingImage/"+name +"."+Id +'.'+ str(sampleNum) + ".jpg", gray[y:y+h,x:x+w])
            #display the frame
            cv2.imshow('frame',img)
            #wait for 100 miliseconds 
        if cv2.waitKey(100) & 0xFF == ord('q'):
            break
        # break if the sample number is morethan 100
        elif sampleNum>60:
            break
    cam.release()
    cv2.destroyAllWindows() 
    # res = "Images Saved for ID : " + Id +" Name : "+ name
    row = [Id , name]
    with open('StudentDetails/StudentDetails.csv','a+') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(row)
    csvFile.close()
    return redirect('home')

@allowed_users(allowed_roles=['teacher','admin'])
@login_required(login_url='login')
def trainer(request):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier(BASE_DIR+'/algorithms/haarcascade_frontalface_default.xml')
    faces,Id = getImagesAndLabels(BASE_DIR+"/static/images/TrainingImage/")
    recognizer.train(faces, np.array(Id))
    recognizer.save(BASE_DIR+"/algorithms/TrainingImageLabel/Trainner.yml")
    cv2.destroyAllWindows()
    return redirect('home')

def getImagesAndLabels(path):
    #get the path of all the files in the folder
    imagePaths=[os.path.join(path,f) for f in os.listdir(path)] 
    #print(imagePaths)
    
    #create empth face list
    faces=[]
    #create empty ID list
    Ids=[]
    #now looping through all the image paths and loading the Ids and the images
    for imagePath in imagePaths:
        #loading the image and converting it to gray scale
        pilImage=Image.open(imagePath).convert('L')
        #Now we are converting the PIL image into numpy array
        imageNp=np.array(pilImage,'uint8')
        #getting the Id from the image
        Id=int(os.path.split(imagePath)[-1].split(".")[1])
        # extract the face from the training image sample
        faces.append(imageNp)
        Ids.append(Id)     
        cv2.imshow("Training", imageNp)
        cv2.waitKey(10)   
    return faces,Ids

@login_required(login_url='login')
@allowed_users(allowed_roles=['teacher','admin'])
def TrackImages(request):
    recognizer = cv2.face.LBPHFaceRecognizer_create()#cv2.createLBPHFaceRecognizer()
    recognizer.read(BASE_DIR+'/algorithms/TrainingImageLabel/Trainner.yml')
    harcascadePath = "algorithms/haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(harcascadePath);    
    df=pd.read_csv(BASE_DIR+"/StudentDetails/StudentDetails.csv")
    cam = cv2.VideoCapture(0)
    font = cv2.FONT_HERSHEY_SIMPLEX        
    col_names =  ['Id','Name','Date','Time']
    attendance = pd.DataFrame(columns = col_names)   
    minW = 0.1*cam.get(3)
    minH = 0.1*cam.get(4) 
    while True:
        ret, im =cam.read()
        gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale( 
                gray,
                scaleFactor = 1.2,
                minNeighbors = 5,
                minSize = (int(minW), int(minH)),
        )    
        for(x,y,w,h) in faces:
            cv2.rectangle(im,(x,y),(x+w,y+h),(225,0,0),2)
            Id, conf = recognizer.predict(gray[y:y+h,x:x+w])                                   
            if(conf < 100):
                ts = time.time()      
                date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                aa=df.loc[df['Id'] == Id]['Name'].values
                name=(" ".join(aa))
                tt=str(Id)+"-"+aa
                attendance.loc[len(attendance)] = [Id,name,date,timeStamp]
                student=student_profile.objects.get(student_id=Id)
                data=student_attendance.objects.create(roll=student,name=name,date=date,time=timeStamp)
                data.save()
                user=student_profile.objects.filter(student_id=Id).update(attendance='Present')
                if user:
                    messages.success(request, 'Attendance Saved For ' + str(Id))
                    cam.release()
                    cv2.destroyAllWindows()
                return redirect('/profile/'+ str(Id))
            else:
                Id='Unknown'                
                tt=str(Id)  
            if(conf > 75):
                noOfFile=len(BASE_DIR+("ImagesUnknown"))+1
                cv2.imwrite("ImagesUnknown/Image"+str(noOfFile) + ".jpg", im[y:y+h,x:x+w])            
            cv2.putText(im,str(tt),(x,y+h), font, 1,(255,255,255),2)        
        attendance=attendance.drop_duplicates(subset=['Id'],keep='first')    
        cv2.imshow('im',im) 
        if (cv2.waitKey(1)==ord('q')):
            break
    ts = time.time()  
    date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    Hour,Minute,Second=timeStamp.split(":")
    fileName="Attendance/Attendance_"+date+"_"+Hour+"-"+Minute+"-"+Second+".csv"
    attendance.to_csv(fileName,index=False)
    cam.release()
    cv2.destroyAllWindows()
    return redirect('home')

def addStudent(request):
    if request.method=='POST':
        id = request.POST.get('rollno', '')
        name = request.POST.get('username','')
        address=request.POST.get('address', '')
        mob= request.POST.get('mobileno', '')
        email=request.POST.get('email', '')
        desc=request.POST.get('desc','')
        user=student_profile(student_id=id,name=name,address=address,phone=mob,email=email,description=desc)
        user.save()
        if user:
            messages.success(request, 'Account was created sfor ' + name)
            return redirect('home')
        else:
            return messages.success(request,'Internal Server Error')
        return render(request,'face_rec/add_student.html')
    return render(request, 'face_rec/add_student.html')

def registerPage(request):
    form=CreateUserForm()
    if request.method=='POST':
        form=CreateUserForm(request.POST)
        if form.is_valid():
            user=form.save()
            username=form.cleaned_data.get('username')
            messages.success(request,'Account Was Created For '+username)
            return redirect('login')
    context={'form':form}
    return render(request,'face_rec/add_teacher.html',context)

def loginPage(request):
    if request.method=='POST':
        username=request.POST.get('username','')
        password=request.POST.get('password','')
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.info(request,'Username Or Password is Incorrect')
    context={}
    return render(request,'face_rec/login.html',context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['teacher','admin'])
def deleteStudent(request,pk):
    student=student_profile.objects.get(student_id=pk)
    if request.method=='POST':
        student.delete()
        return redirect('/')
    context={'student':student}
    return render(request,'face_rec/delete.html',context)

# @unauthenticated_user
# @login_required(login_url='login')
@allowed_users(allowed_roles=['teacher','admin'])
def home(request):
    return render(request,'face_rec/dashboard.html')

def logoutUser(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
@allowed_users(allowed_roles=['teacher','admin','student'])
def profile(request,pk):
    id = int(pk)
    request.FILES
    if request.method=='POST':
        id = int(pk)
        name = request.POST.get('username','')
        address=request.POST.get('address', '')
        mob= request.POST.get('mobileno', '')
        email=request.POST.get('email', '')
        desc=request.POST.get('desc','')
        user=student_profile(student_id=id,name=name,address=address,phone=mob,email=email,description=desc)
        user.save()
        if user:
            messages.success(request, 'Account was Updated For ' + name)
        else:
            return messages.success(request,'Internal Server Error')
        return render(request,'face_rec/student_profile.html')
    student=student_profile.objects.filter(student_id=id)
    attendance=student_attendance.objects.filter(roll=id)
    present=student_attendance.objects.filter(roll=pk).count()
    absent=60-present
    context={'student':student,'attendance':attendance,'present':present,'absent':absent}
    return render(request,'face_rec/student_profile.html',context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['teacher','admin'])
def all_students(request):
    student=student_profile.objects.all()
    total_students_absent=student_profile.objects.filter(attendance='Absent').count()
    total_students_present=student_profile.objects.filter(attendance='Present').count()
    total_students=student_profile.objects.count()
    context={'student':student,'total_students':total_students,'total_students_present':total_students_present,'total_students_absent':total_students_absent}
    return render(request,'face_rec/total.html',context)

def about(request):
    return render(request,'face_rec/about.html')
   
@login_required(login_url='login')
@allowed_users(allowed_roles=['teacher','admin'])
def absent_students(request):
    student=student_profile.objects.filter(attendance='Absent').all()
    total_students_absent=student_profile.objects.filter(attendance='Absent').count()
    total_students_present=student_profile.objects.filter(attendance='Present').count()
    total_students=student_profile.objects.count()
    context={'student':student,'total_students':total_students,'total_students_present':total_students_present,'total_students_absent':total_students_absent}
    return render(request,'face_rec/total.html',context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['teacher','admin'])
def report(request):
    student=student_profile.objects.all()
    total_students_present=student_profile.objects.filter(attendance='Present').count()
    total_students=student_profile.objects.count()
    ts = time.time()  
    date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%M-%d')
    timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    context={'student':student,'total_students':total_students,'total_students_present':total_students_present,'date':date,'time':timeStamp}
    return render(request,'face_rec/report.html',context)  

@login_required(login_url='login')
@allowed_users(allowed_roles=['teacher','admin'])
def send_file(request):
    return render(request,'face_rec/file.html')

@login_required(login_url='login')
@allowed_users(allowed_roles=['teacher','admin'])
def send(request):
    if request.method=='POST':
        request.POST, request.FILES
        subject = request.POST.get('title')
        message = request.POST.get('subject')
        email = request.POST.get('email')
        files = request.FILES.getlist('file')
        try:
            mail = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [email])
            for f in files:
                mail.attach(f.name, f.read(), f.content_type)
            mail.send()
            # messages.success(request,"File Sent To " + email)
            return render(request,'face_rec/file.html',{'error_message': 'Sent email to %s'%email})
        except:
            return render(request,'face_rec/file.html',{'error_message': 'Either the attachment is too big or corrupt'})

    return render(request,'face_rec/file.html',{'error_message': 'Unable to send email. Please try again later'})