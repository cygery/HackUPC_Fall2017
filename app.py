from flask import Flask, render_template, request
from flask_security import Security, login_required, SQLAlchemySessionUserDatastore, current_user
from database import db_session, init_db
from models import User, Role, Friends
import api
import json

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'REDACTED'
app.config['SECURITY_PASSWORD_SALT'] = 'REDACTED'

user_datastore = SQLAlchemySessionUserDatastore(db_session, User, Role)
security = Security(app, user_datastore)


@app.before_first_request
def create_user():
    init_db()


@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/friends', methods=['GET'])
@login_required
def friends():
    friends_dbo = User.query.join(Friends, User.id == Friends.user2_id).all()
    friends = {}
    for friend in friends_dbo:
        friends[friend.id] = {'name': friend.username, 'airport': friend.airport}

    return json.dumps({'friends': friends}), 200, {'Content-Type': 'application/json'}

@app.route('/airports', methods=['GET'])
@login_required
def airports():
    return json.dumps({'airports': api.AIRPORTS}), 200, {'Content-Type': 'application/json'}


@app.route('/airport', methods=['GET', 'POST'])
@login_required
def airport():
    if request.method == 'POST':
        current_user.airport = request.form['airport']
        db_session.commit()
        return json.dumps({'success': True}), 200, {'Content-Type': 'application/json'}
    else:
        return json.dumps({'airport': current_user.airport}), 200, {'Content-Type': 'application/json'}


@app.route('/dest_countries', methods=['GET', 'POST'])
@login_required
def dest_countries():
    if request.method == 'POST':
        current_user.dest_countries = request.form['dest_countries']
        db_session.commit()
        return json.dumps({'success': True}), 200, {'Content-Type': 'application/json'}
    else:
        return json.dumps({'dest_countries': current_user.dest_countries}), 200, {'Content-Type': 'application/json'}


@app.route('/country', methods=['GET', 'POST'])
@login_required
def country():
    if request.method == 'POST':
        current_user.country = request.form['country']
        db_session.commit()
        return json.dumps({'success': True}), 200, {'Content-Type': 'application/json'}
    else:
        return json.dumps({'country': current_user.country}), 200, {'Content-Type': 'application/json'}


@app.route('/getroute', methods=['POST'])
@login_required
def getroute():
    j = request.get_json()
    friend_ids = j['friend_ids']
    outboundDate = j['outboundDate']
    inboundDate = j['inboundDate']

    USERS = {}
    USERS[current_user.id] = {
        'country': current_user.country,
        'airport': current_user.airport,
        'dest_countries': current_user.dest_countries.split(','),
    }
    for friend_id in friend_ids:
        friend = User.query.filter(User.id == friend_id).first()
        USERS[friend_id] = {
            'country': friend.country,
            'airport': friend.airport,
            'dest_countries': friend.dest_countries.split(','),
        }
    route = api.getroute(USERS, outboundDate, inboundDate)

    return json.dumps({'route': route}), 200, {'Content-Type': 'application/json'}


if __name__ == '__main__':
    app.run()
