from flaskblog import db
from flaskblog.models import User

user = User.query.filter_by(email=input('Enter email: ')).first()
if user:
	user.admin = True
	db.session.commit()
	print('Admin created')
else:
	print('No user')