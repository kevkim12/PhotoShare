######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>, Kevin Kim <kevkim@bu.edu>, Jiahao Huamani <jhuamani@bu.edu>
# Group project by: Kevin Kim <kevkim@bu.edu>, Jiahao Huamani <jhuamani@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import base64
import os
import flask
from flask import Flask, g, request, render_template
from flaskext.mysql import MySQL
import flask_login
import re

#for getting current date
from datetime import date

mysql = MySQL()
app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')

# These defaults preserve the original local setup. Override them with
# environment variables outside development.
app.config['MYSQL_DATABASE_USER'] = os.getenv('MYSQL_DATABASE_USER', 'root')
app.config['MYSQL_DATABASE_PASSWORD'] = os.getenv('MYSQL_DATABASE_PASSWORD', 'cs460cs460')
app.config['MYSQL_DATABASE_DB'] = os.getenv('MYSQL_DATABASE_DB', 'photoshare')
app.config['MYSQL_DATABASE_HOST'] = os.getenv('MYSQL_DATABASE_HOST', 'localhost')
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

def get_connection():
	if 'db_conn' not in g:
		g.db_conn = mysql.connect()
	return g.db_conn

@app.teardown_appcontext
def close_connection(error=None):
	db_conn = g.pop('db_conn', None)
	if db_conn is not None:
		db_conn.close()

class ConnectionProxy:
	def cursor(self):
		return get_connection().cursor()

	def commit(self):
		return get_connection().commit()

class CursorProxy:
	def execute(self, *args, **kwargs):
		g.db_cursor = get_connection().cursor()
		return g.db_cursor.execute(*args, **kwargs)

	def fetchall(self):
		return g.db_cursor.fetchall()

	def fetchone(self):
		return g.db_cursor.fetchone()

conn = ConnectionProxy()
cursor = CursorProxy()

@app.template_filter('photo_data_uri')
def photo_data_uri(photo_blob):
	if not photo_blob:
		return ''
	encoded = base64.b64encode(photo_blob).decode('ascii')
	return 'data:image/jpeg;base64,{0}'.format(encoded)

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

login_status = False

@login_manager.request_loader
def request_loader(request):
	email = request.form.get('email')
	if not email:
		return
	users = getUserList()
	if email not in str(users):
		return
	user = User()
	user.id = email
	cursor = conn.cursor()
	cursor.execute("SELECT password FROM Users WHERE email = %s", (email,))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	password = request.form.get('password')
	if password is None:
		return
	if login_status == False:
		return
	else:
		user.is_authenticated = password == pwd
		return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

def getTagPhotos(word):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id IN (SELECT picture_id FROM Associate WHERE word = %s)", (word,))
	return cursor.fetchall()

def getUserTagPhotos(word):
	cursor = conn.cursor()
	cursor.execute(
		"SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id IN (SELECT picture_id FROM Associate WHERE word = %s) AND user_id = %s",
		(word, getUserIdFromEmail(flask_login.current_user.id))
	)
	return cursor.fetchall()

def getAlbumPhotos(aid):
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id IN (SELECT picture_id FROM Contains WHERE album_id = %s)", (aid,))
    return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getPhotoDetails(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id = %s", (pid,))
	return cursor.fetchall()

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return render_template('login.html')
	#The request method is POST (page is recieving data)
	email = flask.request.form.get('email', '').strip()
	password = flask.request.form.get('password', '')
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = %s", (email,)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if password == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return render_template('login.html', error='Email and password did not match.')

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
	login_status = True
	return render_template('register.html', suppress=False)

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
		gender=request.form.get('gender')
		hometown=request.form.get('hometown')
		birthday=request.form.get('birthday')
	except:
		login_status = False
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, firstname, lastname, gender, hometown, birthday, score) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')".format(email, password, firstname, lastname, gender, hometown, birthday, 0)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		login_status = True
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		print('oof')
		login_status = False
		return render_template('register.html', suppress=True)

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = %s", (uid,))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
	return cursor.fetchone()[0]

def getEmailFromUserID(user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM Users WHERE user_id = %s", (user_id,))
    return cursor.fetchone()[0]

def getCommentId(comment):
	cursor = conn.cursor()
	cursor.execute("SELECT comment_id FROM Comments WHERE comment_id = %s", (comment,))

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email FROM Users WHERE email = %s", (email,)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

def get_photo_comments(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT text FROM Comments WHERE comment_id IN (SELECT comment_id FROM Has WHERE picture_id = %s)", (picture_id,))
	return [row[0] for row in cursor.fetchall()]

def get_photo_tags(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT word FROM Associate WHERE picture_id = %s", (picture_id,))
	return [row[0] for row in cursor.fetchall()]

def get_photo_like_count(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM Likes WHERE picture_id = %s", (picture_id,))
	result = cursor.fetchone()
	return result[0] if result else 0

def current_user_liked_photo(picture_id):
	if not flask_login.current_user.is_authenticated:
		return False
	cursor = conn.cursor()
	cursor.execute(
		"SELECT user_id, picture_id FROM Likes WHERE user_id = %s AND picture_id = %s",
		(getUserIdFromEmail(flask_login.current_user.id), picture_id)
	)
	return cursor.fetchone() is not None

def current_user_owns_photo(picture_id):
	if not flask_login.current_user.is_authenticated:
		return False
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Pictures WHERE picture_id = %s", (picture_id,))
	photo_owner = cursor.fetchone()
	return bool(photo_owner and photo_owner[0] == getUserIdFromEmail(flask_login.current_user.id))

def create_photo_comment(picture_id, comment_text):
	comment_text = (comment_text or '').strip()
	if not comment_text:
		return

	cursor = conn.cursor()
	cursor.execute("INSERT INTO Comments (text) VALUES (%s)", (comment_text,))
	conn.commit()
	comment_id = getattr(cursor, 'lastrowid', None)
	if not comment_id:
		cursor.execute("SELECT LAST_INSERT_ID()")
		comment_id = cursor.fetchone()[0]
	cursor.execute("INSERT INTO Has (comment_id, picture_id) VALUES (%s, %s)", (comment_id, picture_id))
	conn.commit()

	if flask_login.current_user.is_authenticated:
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		cursor.execute("INSERT INTO Made (user_id, comment_id) VALUES (%s, %s)", (user_id, comment_id))
		conn.commit()
		cursor.execute("UPDATE Users SET score = score + 1 WHERE user_id = %s", (user_id,))
		conn.commit()

def render_photo_detail(picture_id):
	context = {
		'photo': getPhotoDetails(picture_id),
		'comments': get_photo_comments(picture_id),
		'totalLikes': get_photo_like_count(picture_id),
		'tags': get_photo_tags(picture_id),
	}

	if flask_login.current_user.is_authenticated:
		context['notsame'] = not current_user_owns_photo(picture_id)
		context['liked'] = current_user_liked_photo(picture_id)
		return render_template('photo.html', **context)

	return render_template('photovisitor.html', **context)

@app.route('/albums/<path:subpath>/add_comment', methods=['POST'])
def add_comment(subpath):
	if "photo" in subpath:
		picture_id = request.form.get('picture_id')
		create_photo_comment(picture_id, request.form.get('addcomment'))
		return render_photo_detail(picture_id)

	return render_template('photos.html', photos=getAlbumPhotos(subpath))


@app.route('/albums/<path:subpath>/add_like', methods=['POST'])
@flask_login.login_required
def add_like(subpath):
	if "photo" in subpath:
		picture_id = request.form.get('picture_id')
		cursor = conn.cursor()
		cursor.execute(
			"INSERT IGNORE INTO Likes (user_id, picture_id) VALUES (%s, %s)",
			(getUserIdFromEmail(flask_login.current_user.id), picture_id)
		)
		conn.commit()
		return render_photo_detail(picture_id)

	return render_template('photos.html', photos=getAlbumPhotos(subpath))
		
@app.route('/albums/<path:subpath>/add_unlike', methods=['POST'])
@flask_login.login_required
def add_unlike(subpath):
	if "photo" in subpath:
		picture_id = request.form.get('picture_id')
		cursor = conn.cursor()
		cursor.execute(
			"DELETE FROM Likes WHERE user_id = %s AND picture_id = %s",
			(getUserIdFromEmail(flask_login.current_user.id), picture_id)
		)
		conn.commit()
		return render_photo_detail(picture_id)

	return render_template('photos.html', photos=getAlbumPhotos(subpath))


@app.route('/albums/<path:subpath>', methods=['GET'])
def display_photos(subpath):
	if "likes" in subpath:
		ns = re.findall(r'\d+', subpath)
		picture_id = ns[0]
		cursor.execute("SELECT email FROM Users WHERE user_id IN (SELECT user_id FROM Likes WHERE picture_id = %s)", (picture_id,))
		likes_list = [row[0] for row in cursor.fetchall()]
		return render_template('likes.html', likesby=likes_list)

	if "photo" in subpath:
		ns = re.findall(r'\d+', subpath)
		return render_photo_detail(ns[0])

	return render_template('photos.html', photos=getAlbumPhotos(subpath))


@app.route('/userAlbums', methods=['GET'])
@flask_login.login_required
def userAlbums():
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, albumname FROM Albums WHERE user_id = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
	albumsv = cursor.fetchall()
	albums_list = [(row[1], "albums/" + str(row[0])) for row in albumsv]
	return render_template('userAlbums.html', albums=albums_list)

@app.route('/userAlbums', methods=['POST'])
@flask_login.login_required
def add_album():
	albumname=request.form.get('albumname')
	cursor = conn.cursor()
	print(albumname)
	cursor.execute("INSERT INTO Albums (date, albumname, user_id) VALUES ('{0}', '{1}', '{2}')".format(date.today(), albumname, getUserIdFromEmail(flask_login.current_user.id)))
	conn.commit()
	cursor.execute("SELECT album_id, albumname FROM Albums WHERE user_id = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
	albumsv = cursor.fetchall()
	albums_list = [(row[1], "albums/" + str(row[0])) for row in albumsv]
	return render_template('userAlbums.html', albums=albums_list)

@app.route('/modifyAlbums', methods=['GET'])
@flask_login.login_required
def modifyAlbums():
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, albumname FROM Albums WHERE user_id = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
	albumsv = cursor.fetchall()
	albums_list = [(row[1], row[0]) for row in albumsv]
	return render_template('modifyAlbums.html', albums=albums_list)

@app.route('/modifyAlbums', methods=['POST'])
@flask_login.login_required
def delete_album():
	cursor = conn.cursor()
	selected_album = request.form.get('delete_album')
	cursor.execute("SELECT picture_id FROM Contains WHERE album_id = '{0}'".format(selected_album))
	picture_ids = cursor.fetchall()
	for picture_id in picture_ids:
		cursor.execute("DELETE FROM Likes WHERE picture_id = '{0}'".format(picture_id[0]))
		cursor.execute("DELETE FROM Associate WHERE picture_id = '{0}'".format(picture_id[0]))
		cursor.execute("DELETE FROM Contains WHERE picture_id = '{0}'".format(picture_id[0]))
		cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}'".format(picture_id[0]))
	cursor.execute("DELETE FROM Contains WHERE album_id = '{0}'".format(selected_album))
	cursor.execute("DELETE FROM Albums WHERE album_id = '{0}'".format(selected_album))
	conn.commit()
	cursor.execute("SELECT album_id, albumname FROM Albums WHERE user_id = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
	albumsv = cursor.fetchall()
	albums_list = [(row[1], row[0]) for row in albumsv]
	return render_template('modifyAlbums.html', albums=albums_list)

@app.route('/modifyPhoto/<path:subpath>', methods=['GET'])
@flask_login.login_required
def modifyPictures(subpath):
	return render_template('modifyPictures.html', photos=getAlbumPhotos(subpath), base64=base64, album_id=subpath)

@app.route('/modifyPhoto/<path:subpath>', methods=['POST'])
@flask_login.login_required
def delete_photo(subpath):
	pid = request.form.get('picture_id')
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Has WHERE picture_id = '{0}'".format(pid))
	cursor.execute("DELETE FROM Comments WHERE comment_id IN (SELECT comment_id FROM Has WHERE picture_id = '{0}')".format(pid))
	cursor.execute("DELETE FROM Likes WHERE picture_id = '{0}'".format(pid))
	cursor.execute("DELETE FROM Associate WHERE picture_id = '{0}'".format(pid))
	cursor.execute("DELETE FROM Contains WHERE picture_id = '{0}'".format(pid))
	cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}'".format(pid))
	conn.commit()
	return render_template('modifyPictures.html', photos=getAlbumPhotos(subpath), base64=base64, album_id=subpath)


@app.route("/friends", methods=['GET'])
@flask_login.login_required
def friends():
	cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
	friendsv = cursor.fetchall()
	friends_list = []
	for i in range(len(friendsv)):
		cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(friendsv[i][0]))
		result = cursor.fetchall()
		if result:
			friends_list.append(result[0][0])
	return render_template('friends.html', friends=friends_list)

@app.route('/friends', methods=['POST'])
@flask_login.login_required
def add_friend():
	addfriend = request.form.get('addfriend')
	print("XXX_DATA_XXX:", addfriend)
	if cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(addfriend)) and cursor.execute("SELECT * FROM Friends WHERE user_id2 = '{0}' AND user_id1 = '{1}'".format(getUserIdFromEmail(addfriend), getUserIdFromEmail(flask_login.current_user.id))) == 0:
		print(1)
		friend_id = getUserIdFromEmail(addfriend)
		cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}', '{1}')".format(getUserIdFromEmail(flask_login.current_user.id), friend_id))
		conn.commit()
		cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}', '{1}')".format(friend_id, getUserIdFromEmail(flask_login.current_user.id)))
		conn.commit()
		cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
		friendsv = cursor.fetchall()
		friends_list = []
		for i in range(len(friendsv)):
			cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(friendsv[i][0]))
			result = cursor.fetchall()
			if result:
				friends_list.append(result[0][0])
		return render_template('friends.html', friends=friends_list)
	else:
		print(2)
		cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
		friendsv = cursor.fetchall()
		friends_list = []
		for i in range(len(friendsv)):
			cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(friendsv[i][0]))
			result = cursor.fetchall()
			if result:
				friends_list.append(result[0][0])
		return render_template('friends.html', friends=friends_list)
	
recommendations_list = {}
@app.route('/friendRecs', methods=['GET'])
@flask_login.login_required
def display_recs():
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(user_id))
	friendsv = cursor.fetchall()
	friends_list = []
	for i in range(len(friendsv)):
		cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(friendsv[i][0]))
		result = cursor.fetchall()
		if result:
			friends_list.append(result[0][0])
	recommendations = {}
	for friend in friends_list:
		cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(getUserIdFromEmail(friend)))
		friend_friends = cursor.fetchall()
		for friend_friend in friend_friends:
			friend_email = getEmailFromUserID(friend_friend[0])
			if friend_email != user_id and friend_email not in friends_list:
				if friend_email not in recommendations:
					recommendations[friend_email] = 1
				else:
					recommendations[friend_email] += 1
	sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
	recommendations_list = [x[0] for x in sorted_recommendations]
	for i in range(len(recommendations_list)):
		if recommendations_list[i] == getEmailFromUserID(user_id):
			recommendations_list.pop(i)
			break
	print("DONE")
	print(recommendations_list)
	return render_template('friendRecs.html', users=recommendations_list)

@app.route('/friendRecs', methods=['POST'])
@flask_login.login_required
def friendRecs():
	selected_friend = request.form.get('friend_email')
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}', '{1}')".format(getUserIdFromEmail(flask_login.current_user.id), getUserIdFromEmail(selected_friend))) 
	conn.commit()
	for i in range(len(recommendations_list)):
		if recommendations_list[i] == getUserIdFromEmail(selected_friend):
			recommendations_list.pop(i)
			break
	return render_template('friendRecs.html', users = recommendations_list)

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		selected_album = request.form.get('album')
		print(selected_album)
		cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption) VALUES (%s, %s, %s )", (photo_data, uid, caption))
		conn.commit()
		cursor.execute("SELECT album_id FROM Albums WHERE albumname = '{0}' AND user_id = '{1}'".format(selected_album, uid))
		aid = cursor.fetchall()
		cursor.execute("SELECT picture_id FROM Pictures WHERE user_id = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
		pid = cursor.fetchall()
		print("aid: ", aid)
		print("pid: ", pid)
		cursor.execute('''INSERT INTO Contains (album_id, picture_id) VALUES (%s, %s)''', (aid[0][0], pid[-1][0]))
		conn.commit()
		cursor.execute("UPDATE Users Set score = score + 1 WHERE user_id = '{0}'".format(uid))
		conn.commit()
		tag_num = 1
		added_words = []
		while True:
			try:
				tag_val = request.form.get("tag" + str(tag_num))
				if tag_val == None:
					break
				tag_num += 1
				if tag_val != "":
					if tag_val not in added_words:
						added_words.append(tag_val)
						if cursor.execute("SELECT word FROM Tag WHERE word = '{0}'".format(tag_val)) == 0:
							cursor.execute("INSERT INTO Tag (word) VALUES ('{0}')".format(tag_val))
							conn.commit()
							cursor.execute("INSERT INTO Associate (picture_id, word) VALUES ('{0}', '{1}')".format(pid[-1][0], tag_val))
							conn.commit()
						else:
							cursor.execute("INSERT INTO Associate (picture_id, word) VALUES ('{0}', '{1}')".format(pid[-1][0], tag_val))
							conn.commit()
				elif tag_val == None:
					break
			except:
				break
		return render_template('photos.html', photos=getAlbumPhotos(aid[0][0]), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		print("oo")
		cursor = conn.cursor()
		cursor.execute("SELECT album_id, albumname FROM Albums WHERE user_id = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
		albumsv = cursor.fetchall()
		albums_list = [row[1] for row in albumsv]
		print(albums_list)
		return render_template('upload.html', albums=albums_list)
#end photo uploading code

@app.route('/albums', methods=['GET'])
def display_albums():
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, albumname FROM Albums")
	albumsv = cursor.fetchall()
	albums_list = [(row[1], "albums/" + str(row[0])) for row in albumsv]
	return render_template('albums.html', albums=albums_list)

@app.route('/photosearch', methods=['GET'])
def display_photosearch():
	return render_template('photosearch.html')

@app.route('/photosearch', methods=['POST'])
def search_tag():
	tags = request.form.get("tagSearch")
	tag_split = tags.split()
	arr = ()
	for word in tag_split:
		arr = arr + getTagPhotos(word)
	return render_template('photosearch.html', photos = arr, base64=base64)

@app.route('/tags/<path:subpath>', methods=['GET'])
def display_tag_photos(subpath):
	if "yours" in subpath:
		tag = subpath.split("/")[0]
		return render_template('tagsyours.html', photos=getUserTagPhotos(tag), tag=tag, base64=base64)
	else:
		try:
			user = flask_login.current_user.id
			return render_template('tags.html', photos=getTagPhotos(subpath),tag=subpath,cansee = True, base64=base64)
		except:
			return render_template('tags.html', photos=getTagPhotos(subpath),tag=subpath,cansee = False, base64=base64)
	


@app.route('/leaderboard', methods=['GET'])
def display_leaderboard():
	cursor = conn.cursor()
	cursor.execute("SELECT email,score FROM USERS ORDER BY score DESC LIMIT 10")
	leaderboardv = cursor.fetchall()
	leaderboard_list = [(row[0], row[1]) for row in leaderboardv]
	cursor.execute("SELECT Tag.word, COUNT(*) AS count FROM Tag JOIN Associate ON Tag.word = Associate.word GROUP BY Tag.word ORDER BY count DESC LIMIT 3")
	tagleaderboardv = cursor.fetchall()
	tagleaderboard_list = [(row[0], row[1]) for row in tagleaderboardv]
	return render_template('leaderboard.html', leaderboard=leaderboard_list, tagleaderboard=tagleaderboard_list)

@app.route("/comments", methods=['GET'])
def display_commentSearch():
	return render_template('comments.html')

@app.route("/comments", methods=['POST'])
def search_comment():
	comment = request.form.get('commentSearch')
	cursor = conn.cursor()
	# cursor.execute("SELECT email FROM Users WHERE user_id IN (SELECT user_id FROM Made WHERE comment_id IN (SELECT comment_id FROM Comments WHERE text = '{0}'))".format(comment))
	cursor.execute("SELECT Users.email, COUNT(*) FROM Users INNER JOIN Made ON Users.user_id = Made.user_id INNER JOIN Comments ON Made.comment_id = Comments.comment_id WHERE Comments.text = '{0}' GROUP BY Users.email".format(comment))
	commentv = cursor.fetchall()
	sorted_data = sorted(commentv, key=lambda x: x[1], reverse=True)
	sorted_emails = [x[0] for x in sorted_data]
	print(sorted_emails)
	return render_template('comments.html', comments = sorted_emails, text=comment)

@app.route("/photoRecs", methods=['GET'])
@flask_login.login_required
def display_photoRecs():
	cursor = conn.cursor()
	tag_query = "SELECT word, COUNT(*) AS tag_count FROM Associate JOIN Pictures ON Associate.picture_id = Pictures.picture_id WHERE Pictures.user_id = '{user_id}' GROUP BY word ORDER BY tag_count DESC LIMIT 3"
	cursor.execute(tag_query.format(user_id = getUserIdFromEmail(flask_login.current_user.id)))
	tags = cursor.fetchall()
	print("tags: ", tags)
	if tags == ():
		return render_template('photoRecs.html', photos=[])
	else:
		photos_query = "SELECT p.picture_id, p.imgdata, p.caption, COUNT(*) AS match_count, COUNT(DISTINCT a.word) AS tag_count FROM Associate a JOIN Pictures p ON a.picture_id = p.picture_id WHERE a.word IN ({tags}) AND p.user_id != {user_id} AND a.picture_id NOT IN (SELECT picture_id FROM Associate WHERE word NOT IN ({tags})) GROUP BY a.picture_id ORDER BY match_count DESC, tag_count ASC"
		tag_names = [f"'{tag[0]}'" for tag in tags]
		photos_query = photos_query.format(tags=','.join(tag_names), user_id=getUserIdFromEmail(flask_login.current_user.id))
		cursor.execute(photos_query)
		photos = cursor.fetchall()
		print("p", photos)
	return render_template('photoRecs.html', photos=photos, base64=base64)

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to PhotoShare')

@app.route("/utils/test.html", methods=['GET'])
def test():
	return render_template('test.html')

@app.route("/utils/script.js", methods=['GET'])
def javascript():
	return render_template('script.js')

@app.route("/minimal-table.css", methods=['GET'])
def tableDesign():
	return render_template('minimal-table.css')





if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(
		port=int(os.getenv('PORT', 5000)),
		debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
	)
