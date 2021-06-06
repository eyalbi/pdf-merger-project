from flask.globals import session
from models import User,Inovice,Merged_pdf
import os
import smtplib
from email.message import EmailMessage
import PyPDF2
from datetime import datetime
from pdf_mail import sendpdf 
import schedule
from datetime import date

from flask import Flask, config, current_app, flash, Response, request, render_template_string, render_template, jsonify, redirect, url_for
from flask_mongoengine import MongoEngine
from bson.objectid import ObjectId
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from flask_principal import Principal, Permission, RoleNeed, identity_changed, identity_loaded, Identity, AnonymousIdentity, UserNeed

from forms import LoginForm, RegistrationForm,uploadInovice,DownloadInovice
from models import ROLES

#linoy's code
from flask_dropzone import Dropzone
basedir = os.path.abspath(os.path.dirname(__file__))
#linoy's code


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-MongoEngine settings
    MONGODB_SETTINGS = {
        'host': 'localhost:27017',
        'username': 'apiuser',
        'password': 'apipassword',
        'db': 'exams-io'
    }


app = Flask(__name__)
app.config.from_object(__name__+'.ConfigClass')


#linoy's code
app.config.update(
    UPLOADED_PATH = os.path.join(basedir, 'uploads'),
    DROPZONE_MAX_FILE_SIZE = 1024,
    DROPZONE_TIMEOUT = 5*60*1000),

app.config['DROPZONE_UPLOAD_MULTIPLE'] = True
app.config['DROPZONE_PARALLEL_UPLOADS'] = 5    


dropzone = Dropzone(app)

#linoy's code

db = MongoEngine()
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# create role based auth
principals = Principal(app)
admin_permission = Permission(RoleNeed('Admin'))
student_permission = Permission(RoleNeed('Student'))
lecturer_permission = Permission(RoleNeed('Lecturer'))

gmail_user = 'examsiomail@gmail.com'
gmail_password = '1q2w#E$R'

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except:
        redirect('index')


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, 'role'):
        identity.provides.add(RoleNeed(current_user.role))

#tzlil and linoy's changes
@app.route('/new', methods=['GET', 'POST'])
def login():
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form1 = LoginForm()
    form2 = RegistrationForm()
   
    if form1.validate_on_submit():
        user = User.objects(username=form1.username.data).first()
        if user is None or not user.check_password(form1.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form1.remember_me.data)
        identity_changed.send(current_app._get_current_object(),
                              identity=Identity(user.username))
        return redirect(url_for('index'))
    if form2.validate_on_submit():
            register(form2)
    return render_template('new.html', title='Sign In', form1=form1, form2=form2)

@app.route('/logout')
def logout():
    logout_user()
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register(form):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = form
    if form.validate_on_submit():  
        create_user(form)
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('index'))
    return render_template('new.html', title='Register', form=form)
    # else:
    #     flash('username Already exists')
    #     return redirect('/register')

def create_Inovice(form,u):
    inovice = Inovice(Inovice_pdf=form.Inovice_pdf.data,inovice_Customer = u.username)
    inovice.save()


def create_user(form):
    user = User(username=form.username1.data, email=form.email.data)
    user.role = form.role.data
    user.first_name = form.first_name.data
    user.last_name = form.last_name.data
    user.set_password(form.password1.data)
    user.avatar = form.avatar.data
    user.save()

def Merge_pdf(user):
    try:
        inovices = Inovice.objects(inovice_Customer = current_user.username)
        counter = 0 
        pdfWriter = PyPDF2.PdfFileWriter()
        for i in inovices:
            pdfFile = open(i.Inovice_pdf,'rb')
            pdfReader = PyPDF2.PdfFileReader(pdfFile)
            for pageNum in range(pdfReader.numPages):
                pdfWriter.addPage(pdfReader.getPage(pageNum))
        today = datetime.today()
        YandM = datetime(today.year, today.month, 1)
        timeString = str(YandM).split(" ")[0]

        loc = os.path.join(basedir, 'Downloads')
        pdfOutputFile = open(os.path.join(loc, '{0}-{1}-MergedFiles.pdf'.format(current_user.username,timeString)), 'wb')
        pdfWriter.write(pdfOutputFile)
        pdfOutputFile.close()
        pdfFile.close()
        return os.path.join(loc, '{0}-{1}-MergedFiles.pdf'.format(current_user.username,timeString))
    except:
        flash("Opps!! Error opening file!")

def send_merged():
    if date.today().day != 1:
        return
    inovices = Merged_pdf.objects()
    path = ""
    loc = os.path.join(basedir, 'Downloads')
    paths = loc.split('\\')
    seprator = '/'
    for i in inovices:
        k = sendpdf("{}".format(gmail_user), 
                        "{}".format(i.inovice_Accountant_mail), 
                        "{}".format(gmail_password), 
                        "Inovice from {}".format(current_user.username), 
                        "Hello, here is my inovices. Have a good day!", 
                        "{}".format(i.PdfPath.split('\\')[-1].split('.')[0]), 
                        "{}".format(seprator.join(paths))) 
        k.email_send()


@app.route('/')
@app.route('/index')
@login_required
def index():
    session['file'] = []
    user = User.objects(username=current_user.username).first()
    send_merged()
    if user.role == 'ACCOUNTANT':
        return render_template('Accountant.html', user=user)
    elif user.role == 'CUSTOMER':
        return render_template('Customer.html', user=user)
    else:
        return redirect(url_for('index'))


@app.route('/Customer/DownloadInoviceInovices', methods=['GET','POST'])
@login_required
def Download_merged_pdf():

    u = User.objects(username=current_user.username).first()
    form = DownloadInovice()
    # try:
    if form.validate_on_submit():
        Acountant_username = Inovice.objects(inovice_Customer = current_user.username).first().inovice_Accountant
        mail = User.objects(username = Acountant_username ).first().email
        pathtofile = Merge_pdf(u)
        merged = Merged_pdf(inovice_Accountant_mail = mail,PdfPath = pathtofile)
        merged.save()
        path = ""
        loc = os.path.join(basedir, 'Downloads')
        paths = loc.split('\\')
        seprator = '/'
        
        k = sendpdf("{}".format(gmail_user), 
                    "{}".format(mail), 
                    "{}".format(gmail_password), 
                    "Inovice from {}".format(current_user.username), 
                    "Hello, here is my inovices. Have a good day!",
                    "{}".format(pathtofile.split('\\')[-1].split('.')[0]), 
                    "{}".format(seprator.join(paths))) 

        
        k.email_send()
        flash('Download seccessfull!')
        return redirect(url_for('index'))
    return render_template('DownloadPdf.html', title='DownloadInovice', form=form,user=u)
    # except:
    #     flash('cant Download document')
    #     return redirect('/index')




@app.route('/Customer/DeletePdf', methods=['GET','POST'])
@login_required
def Delete_Pdf():
    u = User.objects(username=current_user.username).first()
    inovices = Inovice.objects(inovice_Customer = current_user.username)
    
    if request.method == 'POST':
        deletePDfList = request.form.getlist('checked')
        for d in deletePDfList:
            Deletepdf = Inovice.objects(Inovice_pdf = d ,inovice_Customer= current_user.username)
            Deletepdf.delete()
        return redirect(url_for('Delete_Pdf'))
    return render_template('DeletePdf.html', title='DownloadInovice',user=u,inovices = inovices)


def checkinovice(Path,accountant,Customer):
    I = Inovice.objects(Inovice_pdf = Path, inovice_Accountant = accountant,inovice_Customer = Customer )
    if I:
        return False
    return True 
@app.route('/Customer/upload', methods=['POST', 'GET'])
@login_required
def upload():
    
    user = User.objects(username=current_user.username).first()
    form = uploadInovice()
    form.inovice_Accountant.choices = [(u.username, u.username) for u in User.objects.filter(role = 'ACCOUNTANT')]
    if request.method == 'POST' and not form.validate_on_submit():
        for key, f in request.files.items():
            if key.startswith('file'):
                f.save(os.path.join(app.config['UPLOADED_PATH'], f.filename))
                session['file'].append(os.path.join(app.config['UPLOADED_PATH'], f.filename))
        redirect ('/')
    if form.validate_on_submit():
        for file in session['file']:
            pdf = Inovice(inovice_Customer = current_user.username,inovice_Accountant = form.inovice_Accountant.data)
            pdf.Inovice_pdf = file
            pdf.save()
    return render_template('test.html', user=user, form=form)


@app.route('/Customer/myProfile', methods=['POST', 'GET'])
@login_required
def myprofile():
    user = User.objects(username=current_user.username).first()
    return render_template('myProfile.html', title='myProfile', user=user)


if __name__ == '__main__':
    
    app.run()



