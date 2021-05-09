from models import User,Inovice
import os
import smtplib
from email.message import EmailMessage
import PyPDF2


from flask import Flask, current_app, flash, Response, request, render_template_string, render_template, jsonify, redirect, url_for
from flask_mongoengine import MongoEngine
from bson.objectid import ObjectId
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from flask_principal import Principal, Permission, RoleNeed, identity_changed, identity_loaded, Identity, AnonymousIdentity, UserNeed

from forms import LoginForm, RegistrationForm,AdminDeleteForm, AdminUpdateForm, AdminSendEmailForm,StudentMessage,uploadInovice,DownloadInovice
from models import ROLES

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
    return User.objects.get(id=user_id)


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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(username=form.username.data).first()
        if user.Blocked == 'true' or user.Blocked == 'True':
            flash('Your user is blocked adress Admin')
            return redirect(url_for('login'))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        identity_changed.send(current_app._get_current_object(),
                              identity=Identity(user.username))
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    try:
        form = RegistrationForm()
        if form.validate_on_submit():
            
            create_user(form)
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('login'))
        return render_template('register.html', title='Register', form=form)
    except:
        flash('username Already exists')
        return redirect('/register')

def create_Inovice(form,u):
    inovice = Inovice(Inovice_pdf=form.Inovice_pdf.data,inovice_Customer = u.username)
    inovice.save()


def create_user(form):
    user = User(username=form.username.data, email=form.email.data)
    user.role = form.role.data
    user.first_name = form.first_name.data
    user.last_name = form.last_name.data
    user.set_password(form.password.data)
    user.avatar = form.avatar.data
    user.save()

def Merge_pdf(user):
    inovices = Inovice.objects()
    for i in inovices:
        if i.inovice_Customer == user.username:
            pdfFile = open(r"C:\Users\eyalb\OneDrive\Desktop\exams\sample.pdf",'rb')
            pdfReader = PyPDF2.PdfFileReader(pdfFile)
            pdfWriter = PyPDF2.PdfFileWriter()
            for pageNum in range(pdfReader.numPages):
                pageObj = pdfReader.getPage(pageNum)
                pdfWriter.addPage(pageObj)
    pdfOutputFile = open('MergedFiles.pdf', 'wb')
    pdfWriter.write(pdfOutputFile)
    pdfOutputFile.close()
    pdfFile.close()






@app.route('/')
@app.route('/index')
@login_required
def index():
    user = User.objects(username=current_user.username).first()
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
        Merge_pdf(u)
        flash('Download seccessfull!')
        return redirect(url_for('index'))
    return render_template('DownloadPdf.html', title='DownloadInovice', form=form,user=u)
    # except:
    #     flash('cant Download document')
    #     return redirect('/index')



@app.route('/Customer/Inovices', methods=['GET','POST'])
@login_required
def Upload_inv():
    u = User.objects(username=current_user.username).first()
    form = uploadInovice()
    try:
        if form.validate_on_submit():
            create_Inovice(form,u)
            flash('Upload seccessfull!')
            return redirect(url_for('index'))
        return render_template('UploadInovice.html', title='UploadInovice', form=form,user=u)
    except:
        flash('cant upload document')
        return redirect('/index')














if __name__ == '__main__':
    app.run()



