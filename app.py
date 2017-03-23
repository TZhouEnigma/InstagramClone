
import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
from datetime import date

#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'DADADA'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users") 
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd 
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')  

@app.route("/register", methods=['POST'])
def register_user():
	try:
            email=request.form.get('email')
            password=request.form.get('password')
            firstname=request.form.get('firstname')
            lastname=request.form.get('lastname')
            dob=request.form.get('dob')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print cursor.execute("INSERT INTO Users (FirstName,LastName,DOB,email, password,contribution) VALUES ('{0}', '{1}','{2}','{3}','{4}',{5})".format(firstname,lastname,dob,email, password,0))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print "couldn't find all tokens"
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
            uid = getUserIdFromEmail(flask_login.current_user.id)
            try:
                if(request.form['albumname']):
                    print "caption"
                    albumname=request.form.get('albumname')
                    conn=mysql.connect()
                    cursor = conn.cursor()
                    cursor.execute("select owner_uid from albums where name='{0}'".format(albumname))
                    temp3=cursor.fetchall()
                    print "daa",temp3
                    if temp3 and temp3[0][0]==uid:##if the user already has taht album name
                        print "lima",temp3[0][0]
                        # albumname=null;
                        return render_template('upload.html',systemprompt="you already have that album!")
                    else:
                        cursor.execute("INSERT INTO Albums(owner_uid,DOC,Name) values({0},'{1}','{2}')".format(uid,str(date.today().isoformat()),albumname))
                        conn.commit()
                        print "caption2"
                        print "lina"
                        return render_template('upload.html',systemprompt="you have added a new album "+str(albumname))
                return render_template('hello.html')
            except:
                    imgfile = request.files['photo']
                    caption = request.form.get('caption')
                    album = request.form.get('album')
                    initialtag=request.form.get('tag')
                    print "cap and alb img",caption,album,imgfile
                    if not imgfile or not album:
                        return render_template('upload.html',systemprompt="image file and album are required!")
                    photo_data = base64.standard_b64encode(imgfile.read())
                    conn=mysql.connect()
                    cursor = conn.cursor()
                    cursor.execute("SELECT Album_id from Albums where Name='{0}' and owner_uid={1}".format(album,uid))
                    albumid=cursor.fetchall()
                    if not albumid:
                        cursor.execute("INSERT INTO Albums(owner_uid,DOC,Name) values({0},'{1}','{2}')".format(uid,str(date.today().isoformat()),album))
                        conn.commit()
                    cursor.execute("SELECT Album_id from Albums where Name='{0}' and owner_uid={1}".format(album,uid))
                    albumid=cursor.fetchall()
                    album_id=albumid[0][0]
                    cursor.execute("SELECT Contribution from users where user_id={0}".format(uid))
                    temp=cursor.fetchall()
                    temp2=temp[0][0]+1
                    cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption,album_id) VALUES ('{0}','{1}', '{2}',{3} )".format(photo_data,uid, caption,album_id))
                    print album_id,"dsaa"
                    cursor.execute("UPDATE USERS SET CONTRIBUTION={0} where user_id={1}".format(temp2,uid))
                    conn.commit()
                    cursor.execute("SELECT max(PICTURE_ID) from pictures".format(photo_data,uid,caption,album_id))#max id cuz pid is unique
                    t_mp=cursor.fetchall()
                    pcid=t_mp[0][0]
                    if initialtag:#if the user has entered a tag
                        conn=mysql.connect()
                        cursor = conn.cursor()
                        cursor.execute("SELECT TAG_ID from TAGs where TagText='{0}' ".format(initialtag))
                        t_n=cursor.fetchall()
                        if not t_n:#if the tah doesn't exist
                            cursor.execute("INSERT INTO TAGs(tagtext) Values('{0}')".format(initialtag))
                            conn.commit()
                        cursor.execute("SELECT TAG_ID from TAGs where TagText='{0}' ".format(initialtag))
                        t_n=cursor.fetchall()
                        tn=t_n[0][0]
                        cursor.execute("INSERT INTO TAGPIC(tag_id,picture_id) values({0},{1})".format(tn,pcid))
                        conn.commit()
                    return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid) )
	#The method is GET so we return a  HTML form to upload the a photo.
        else:
            return render_template('upload.html')
#end photo uploading code
@app.route('/viewall', methods=['GET', 'POST'])
def viewbytag():
    likee=False
    youmaylike="null"
    conn=mysql.connect()
    cursor=conn.cursor()
    cursor.execute("SELECT comment_text,comment_doc,picture_id,comment_owner_id FROM COMMENTS")
    com_=cursor.fetchall()
    cursor.execute("SELECT firstname,lastname,user_id from Users")
    user_name=cursor.fetchall()
    try:
         uid = getUserIdFromEmail(flask_login.current_user.id)
         conn=mysql.connect()
         cursor = conn.cursor()
         cursor.execute("SELECT TAGTEXT FROM TAGS WHERE TAG_ID IN (SELECT TAG_ID FROM TAGPIC WHERE PICTURE_ID IN (SELECT PICTURE_ID FROM PICTURES WHERE USER_ID={0}))".format(uid))
         you_maylike=cursor.fetchall()
         youmaylike=you_maylike
         likee=True
         print youmaylike
    except:
        youmaylike=[["can't make suggesion o visistors"]]
    conn=mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT count(tag_id) from tags")
    tag_count=cursor.fetchall()
    tagcount=tag_count[0][0]
    tagnames=[['no tag yet!']]
    if tagcount>0:
        print tagcount
        cursor.execute("SELECT tagtext from tags where tag_id in (select  tag_id from (select tag_id,count(*) as frequency from tagpic group by tag_id order by count(*) desc) as t where frequency>=(select count(tag_id) from tagpic)/{0}) ".format(tagcount) )#calculate average tag per pic >
        tag_names=cursor.fetchall()
        tagnames=tag_names
    if(request.method=='POST'):
        print " this class got me like TAT"
        try:
            #request.form['searchbytag']#if the tag exist
            tagsearched=request.form['searchbytag']
            conn=mysql.connect()
            cursor = conn.cursor()
            print "your mom",tagsearched
            cursor.execute("SELECT TAG_ID from TAGs where TagText='{0}' ".format(tagsearched))
            t_ame=cursor.fetchall()
            print t_ame
            tname=t_ame[0][0]
            cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id in (select picture_id from tagpic where tag_id={0})".format(tname))
            imgd=cursor.fetchall()
            print "uyea",tname
            if not imgd:
                return render_template('viewall.html',prompt="no photo under such tag!",topfive=tagnames,maylike=youmaylike)
            else:
                return render_template('viewall.html',pdata=imgd,prompt="here are all photos under tag "+str(tagsearched),topfive=tagnames,tnname=str(tagsearched),maylike=youmaylike,like=likee,com=com_,username=user_name)
        except:
            return render_template('viewall.html',prompt="no one has used this tag yet!",topfive=tagnames,maylike=youmaylike)
    return render_template('viewall.html',topfive=tagnames,maylike=youmaylike)

@app.route('/viewall/<item>/<int:id>', methods=['GET', 'POST'])
def clicktag(item,id):
    uid=1000000
    enablelike=False
    user_name="anounemous user"
    warning=[]
    l_id=[]
    user_like=[]
    youmaylike=[]
    tagnames=[]
    try:
        uid = getUserIdFromEmail(flask_login.current_user.id)
        enablelike=True
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("select user_id,picture_id from likes")
        l_id=cursor.fetchall()
        cursor.execute("select firstname,lastname,user_id from users")
        user_like=cursor.fetchall()
        conn=mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT TAGTEXT FROM TAGS WHERE TAG_ID IN (SELECT TAG_ID FROM TAGPIC WHERE PICTURE_ID IN (SELECT PICTURE_ID FROM PICTURES WHERE USER_ID={0}))".format(uid))
        you_maylike=cursor.fetchall()
        youmaylike=you_maylike
        cursor.execute("SELECT count(tag_id) from tags")
        tag_count=cursor.fetchall()
        tagcount=tag_count[0][0]
        cursor.execute("SELECT tagtext from tags where tag_id in (select  tag_id from (select tag_id,count(*) as frequency from tagpic group by tag_id order by count(*) desc) as t where frequency>=(select count(tag_id) from tagpic)/{0}) ".format(tagcount) )#calculate average tag per pic >
        tag_names=cursor.fetchall()
        tagnames=tag_names
    except:
        print"gg"

    if str(item)=="no one has used this tag yet!":
        return render_template('viewall.html')
    else:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT imgdata, picture_id,user_id, caption FROM Pictures WHERE picture_id in (select picture_id from tagpic where tag_id in (SELECT TAG_ID from TAGs where TagText='{0}'))".format(item))
        imgd=cursor.fetchall()
        cursor.execute("SELECT comment_text,comment_doc,picture_id,comment_owner_id FROM COMMENTS")
        com_=cursor.fetchall()
        cursor.execute("SELECT firstname,lastname,user_id from Users")
        user_name=cursor.fetchall()
        #print com_
        if request.method=='POST':
            try:
                flag=False
                try:
                    uid = getUserIdFromEmail(flask_login.current_user.id)
                    enablelike=True
                    flag=True
                    print uid,"uid","said"
                    if flag and request.form['likes']:
                        conn = mysql.connect()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO LIKES(USER_ID,PICTURE_ID) VALUES({0},{1})".format(uid,int(id)))
                        conn.commit()
                except:
                    if flag:
                        warning="cannot like the same pic twice!!!!!!!!!"
                    print "anony",user_name #the user is a unregistered user
                comment=request.form['comment']
                if comment:
                    print date.today().isoformat()
                    cursor.execute("SELECT user_id from pictures where picture_id={0}".format(int(id)))
                    temp_id=cursor.fetchall()
                    tempid=temp_id[0][0]
                    print tempid,"dadssww",comment
                    if uid==tempid and uid!=1000000:
                        print "changenow uid is","here is comment",uid,tempid
                        uid=-1
                    print "now uid is",uid
                    if uid!=-1:
                        print "charu"
                        cursor.execute("INSERT INTO COMMENTS(comment_owner_id, picture_id,comment_doc,comment_text) values({0},{1},'{2}','{3}'); ".format(uid,id,str(date.today().isoformat()),str(comment)))
                        conn.commit()
                    cursor.execute("SELECT Contribution from users where user_id={0}".format(uid))
                    temp=cursor.fetchall()
                    print temp,uid
                    if int(uid)!=1000000:
                        try:
                            temp2=temp[0][0]+1
                            cursor.execute("UPDATE USERS SET CONTRIBUTION={0} where user_id={1}".format(temp2,uid))
                            print "beofe"
                            conn.commit()
                            print "here"
                        except:
                            print "catcehed execp"
                            return render_template('viewall.html',prompt="you can't comment on your own photo!",topfive=tagnames)
            except:
                try:
                    if request.form['likes']:
                        print "caonibamo"
                except:
                    print "no like"
                print "dsaas",user_name
                if not flag==True:
                    return render_template('viewall.html',prompt="you can't comment on your own photo!",topfive=tagnames)
        print "dsaas ali",user_name,"warning",warning
        return render_template('viewall.html',pdatb=imgd,prompt="here are all photos under tag "+str(item),tnname=str(item),com=com_,username=user_name,like=enablelike,warn=warning,lid=l_id,userlike=user_like,maylike=youmaylike,topfive=tagnames)


@app.route('/seefriend', methods=['GET', 'POST'])
@flask_login.login_required
def friend():
    fullname=""
    alreadyfriended=[]
    flag=False
    if request.method == 'GET':
        print "HAHBAN"
    if request.method == 'POST':
        print "dsada"
        try:
            if(request.form['seefriend']):
                #print request.form['seefriend']
                uid = getUserIdFromEmail(flask_login.current_user.id)
                conn = mysql.connect()
                cursor = conn.cursor()
                cursor.execute("SELECT firstname,lastname,friend_email from Friends,Users WHERE email=my_email and user_id= '{0}'".format(uid))
                data = []
                for item in cursor:
                    data.append(item)
                
                print data
                return render_template('seefriend.html',data=data)
        except:
                try:
                    if(request.form['searchfriend']):
                        print "dididi"
                        first = request.form['friendfirstname']
                        last = request.form['friendlastname']
                        fullname=first+last
                        print fullname
                        conn = mysql.connect()
                        cursor = conn.cursor()
                #print query
                #try query
                        cursor.execute("SELECT email from Users WHERE FirstName='{0}' and LastName='{1}'".format(first,last))
                        dataa = []
                        for item in cursor:
                            print "name is ",item
                            dataa.append(item)
                        if not dataa:
                            datta="name not found"
                            print "na name"
                            return render_template('seefriend.html',errormessage=datta)
                        print "dadasda11"
                        return render_template('seefriend.html', dataa = dataa)
                except:
                        try:
                            if(request.form['addfriend']):
                                friendemail = request.form['friendemail']
                                print "ada friend",friendemail
                                uid = getUserIdFromEmail(flask_login.current_user.id)
                                conn = mysql.connect()
                                cursor = conn.cursor()
                                cursor.execute("SELECT email from Users where email not IN (SELECT my_email FROM FRIENDS WHERE friend_email='{0}') and user_id={1}".format(friendemail,uid))
                                myemail= cursor.fetchall()
                                print "sig",myemail,uid
                                if not myemail:
                                    print "dasdasgg"
                                    flag=True
                                cursor.execute("INSERT INTO Friends(my_email, friend_email) VALUES ('{0}','{1}');".format(myemail[0][0],friendemail))
                                conn.commit()
                                conn = mysql.connect()
                                cursor = conn.cursor()
                                cursor.execute("SELECT firstname,lastname from Users WHERE email='{0}'".format(myemail[0][0]))
                                temppo=cursor.fetchall()
                                myfriendemail=temppo[0][0]
                                print "friended!",myfriendemail,"huh"
                                return render_template('seefriend.html',name=myfriendemail)#dadsa
                            return render_template('seefriend.html')
                        except:
                            if flag:
                                alreadyfriended="you two are already friends!"
                            return render_template('seefriend.html',errormessage=alreadyfriended)
                                               #return render_template('seefriend.html')
                return render_template('seefriend.html')
    else:
        print "dididi2"
        return render_template('seefriend.html')


@app.route('/viewphoto', methods=['GET', 'POST'])
@flask_login.login_required
def viewphoto():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    conn=mysql.connect()
    cursor=conn.cursor()
    cursor.execute("select name from albums where owner_uid={0}".format(uid))
    albumm=cursor.fetchall()
    if(request.method=='POST'):
        try:
            if(request.form['tagsearch']):
                tagn=request.form['tagsearch']
                conn=mysql.connect()
                cursor=conn.cursor()
                print "here"
                cursor.execute("select imgdata, picture_id, caption FROM Pictures where user_id={0} and picture_id in (select picture_id from tagpic where tag_id in (select tag_id from tags where tagtext='{1}'))".format(uid,tagn))
                albumm=cursor.fetchall()
                return render_template('viewphoto.html',tagphotos=albumm,tagname=tagn)
        except:
            tagname=request.form['tagname']
            conn=mysql.connect()
            cursor=conn.cursor()
            print "tagge"
            cursor.execute("select tag_id from tags where tagtext='{0}'".format(tagname))
            tag_id=cursor.fetchall()
            tagid=tag_id[0][0]
            cursor.execute("select picture_id from TagPic where tag_id={0}".format(tagid))
            pic_tag=cursor.fetchall()
            print pic_tag
            print albumm
    return render_template('viewphoto.html',albums=albumm)
@app.route('/viewphoto/<item>', methods=['GET', 'POST'])
@flask_login.login_required
def testa(item):
    print "ddd"
    uid = getUserIdFromEmail(flask_login.current_user.id)
    conn=mysql.connect()
    cursor=conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE album_id IN (select album_id from albums where owner_uid={0} and name='{1}')".format(uid,str(item)))
    img=cursor.fetchall()
    print "ddd2",uid,item,"dasdsa"
    if request.method =='POST':
        print "ls"
        try:
            if request.form['addtag']:
                tagname=request.form['tag']
                uid = getUserIdFromEmail(flask_login.current_user.id)
                conn=mysql.connect()
                cursor=conn.cursor()
                print "gg1"
                picid=request.form['pid']
                print "gg"
                try:
                    cursor.execute("INSERT INTO TAGS(tagtext) VALUES('{0}')".format(tagname))
                    conn.commit()
                except:
                    print "alreadey added"
                cursor.execute("select tag_id from tags where tagtext='{0}'".format(tagname))
                tagidt=cursor.fetchall()
                tagid=tagidt[0][0]
                print tagid,picid
                cursor.execute("INSERT INTO TAGPIC(tag_id,picture_id) VALUES('{0}','{1}')".format(tagid,pid))
                conn.commit()
                print "tag name is ",tagname
        except:
               print "dsaa"
    return render_template('photos.html',pics=img,name=str(item))

@app.route('/viewphoto/<item>/<id>', methods=['GET', 'POST'])
@flask_login.login_required
def testc(item,id):
    uid = getUserIdFromEmail(flask_login.current_user.id)
    conn=mysql.connect()
    cursor=conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE album_id IN (select album_id from albums where owner_uid={0} and name='{1}')".format(uid,str(item)))
    img=cursor.fetchall()
    print "hahaniba"
    if request.method =='POST':
        print "ls"
        try:
            if request.form['addtag']:
                tagname=request.form['tag']
                uid = getUserIdFromEmail(flask_login.current_user.id)
                conn=mysql.connect()
                cursor=conn.cursor()
                print "gg"
                try:
                    cursor.execute("INSERT INTO TAGS(tagtext) VALUES('{0}')".format(tagname))
                    conn.commit()
                except:
                    print "alreadey added"
                cursor.execute("select tag_id from tags where tagtext='{0}'".format(tagname))
                tagidt=cursor.fetchall()
                tagid=tagidt[0][0]
                print tagid,id
                cursor.execute("INSERT INTO TAGPIC(tag_id,picture_id) VALUES({0},{1})".format(tagid,int(id)))
                conn.commit()
                print "tag name is ",tagname
        except:
               print "haaww"
    return render_template('photos.html',pics=img,name=str(item))

@app.route('/goback.html/<item>/<id>')
@flask_login.login_required
def testb(item,id):
    uid = getUserIdFromEmail(flask_login.current_user.id)
    conn=mysql.connect()
    cursor=conn.cursor()
    id=int(id)
    cursor.execute("DELETE FROM likes WHERE picture_id={0}".format(id))
    cursor.execute("DELETE FROM TAGPIC WHERE picture_id={0}".format(id))
    cursor.execute("DELETE FROM Pictures WHERE picture_id={0}".format(id))
    cursor.execute("DELETE FROM comments WHERE picture_id={0}".format(id))
    print "DELETE FROM Pictures WHERE picture_id=",id,"has been executed"
    conn.commit()
    print type(id),type(uid)
    print "kobe"
    lebron='/viewphoto.html/'+item
    print lebron,type(lebron)
    return render_template('goback.html',path=str(item))

@app.route('/viewphoto/delete/<item>')
@flask_login.login_required
def deletealbum(item):
    uid = getUserIdFromEmail(flask_login.current_user.id)
    conn=mysql.connect()
    cursor=conn.cursor()
    cursor.execute("SELECT album_id FROM Albums WHERE owner_uid={0} and Name='{1}'".format(uid,str(item)))
    album_id=cursor.fetchall()[0][0]
    print album_id
    cursor.execute("DELETE FROM TagPic WHERE picture_id in(select picture_id from albums where album_id={0})".format(int(album_id)))
    conn.commit()
    cursor.execute("DELETE FROM comments WHERE picture_id in(select picture_id from albums where album_id={0})".format(int(album_id)))
    conn.commit()
    cursor.execute("DELETE FROM likes WHERE picture_id in(select picture_id from albums where album_id={0})".format(int(album_id)))
    conn.commit()
    cursor.execute("DELETE FROM Pictures WHERE user_id={0} and album_id={1}".format(uid,int(album_id)))
    conn.commit()
    conn=mysql.connect()
    cursor=conn.cursor()
    cursor.execute("DELETE FROM Albums where NAME='{0}' AND owner_uid={1}".format(str(item),uid))
    conn.commit()
    conn=mysql.connect()
    cursor=conn.cursor()
    cursor.execute("select name from albums where owner_uid={0}".format(uid))
    albumm=cursor.fetchall()
    print item,"deleted"
    return render_template('viewphoto.html',albums=albumm)
#default page
@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)
