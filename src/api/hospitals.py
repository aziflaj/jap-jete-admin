from flask import Blueprint, abort, request
from pushjack import GCMClient
import bcrypt
import db

import os
import json
import requests
import config
import time, datetime
from utils import ApiResponse, to_timestamp
from decorators import hospital_login


BASE_PATH = os.path.join("/api/v1", "hospitals")
hospitals = Blueprint('hospitals', __name__, url_prefix=BASE_PATH)


@hospitals.route('/gcm-message/', methods=['POST'])
def gcm_message():
    if request.data.get('message'):
        gcmClient = GCMClient(api_key=os.environ.get('GCM_API_KEY'))

        alert = {
            'subject': 'Subject goes here', # TODO: set a better subject
            'message': request.data.get('message')
        }

        session = db.Session()
        gcm_id_list = [user.gcm_id for user in session.query(db.User).all()]
        session.close()

        response = gcmClient.send(gcm_id_list,
                                  alert,
                                  time_to_live=3600)
        if response:
            return ApiResponse({
                'message': 'Mesazhi u dergua'
            })
        else:
            return ApiResponse({
                'message': 'Father, why have you forsaken me?'
            })
    else:
        return ApiResponse({
            'message': 'Can\'t send a blank message...'
        })


@hospitals.route('/donations')
def demo_history():
    session = db.Session()
    users = session.query(db.User).all()
    result = []
    for u in users:
        donations = session.query(db.UserHistory).filter_by(user_id=u.user_id).all()
        result.append({
            'user': u.user_id,
            'history': [{
                'date': to_timestamp(d.donation_date),
                'amount': d.amount,
                'hospital': d.hospital.name
            } for d in donations]
        })
    session.close()
    return ApiResponse({
        'history': result
    })


@hospitals.route('/donations/<id>')
def demo_user_history(id):
    session = db.Session()
    user = session.query(db.User).filter_by(user_id=id).first()
    if not user:
        return ApiResponse({
            'status': 'error',
            'message': 'No user with id {0} found'.format(id)
        })

    donations = session.query(db.UserHistory).filter_by(user_id=user.user_id).all()
    result = {
        'user': user.user_id,
        'history': [{
            'date': to_timestamp(d.donation_date),
            'amount': d.amount,
            'hospital': d.hospital.name
        } for d in donations]
    }
    session.close()
    return ApiResponse({
        'history': result
    })


@hospitals.route('/campaigns/', methods=['GET'])
# @require_login
def get_campaigns_by_bloodtype():
    session = db.Session()
    user_id = request.args.get('user_id', 0)

    # filter by user Blood Type
    user = session.query(db.User).filter_by(user_id=user_id).first()
    if not user:
        return ApiResponse({
            'status': 'error',
            'message': 'No user with id {0} found'.format(user_id)
        })

    campaigns_blood = session.query(db.CampaignBlood).filter_by(blood_type=user.blood_type).all()
    campaigns = [
        {
            'name': c.campaign.name,
            'hospital': c.campaign.hospital.name,
            'message': c.campaign.message,
            'start_date': to_timestamp(c.campaign.start_date),
            'end_date': to_timestamp(c.campaign.end_date)
        } for c in campaigns_blood]
    session.close()

    # return data
    return ApiResponse({
        "campaigns": campaigns
    })


@hospitals.route('/campaigns/', methods=['POST'])
# @require_login
def create_campaign():
    session = db.Session()
    data = json.loads(request.data)

    hospital = session.query(db.Hospital).first() # TODO: Dont use 1st
    name = data['name']
    message = data['message']
    bloodtypes = data['bloodtypes']
    start_date = datetime.datetime.now()
    end_date = datetime.datetime.now() + datetime.timedelta(days=10)
    campaign = db.Campaign(hospital._id, name, message, start_date, end_date)
    session.add(campaign)
    session.commit()

    for bloodtype in bloodtypes:
        campaign_blood = db.CampaignBlood(campaign._id, bloodtype)
        session.add(campaign_blood)

    session.commit()
    session.close()

    return ApiResponse({
        'status': 'ok'
    })



@hospitals.route('/login/', methods=['POST'])
def login_hospital():
    data = json.loads(request.data)

    username = data['username']
    password = data['password'].encode('ascii', 'replace')

    session = db.Session()
    h = session.query(db.Hospital).filter_by(username=username).first()
    pwd = h.password.encode('ascii', 'replace')

    if not h or bcrypt.hashpw(password, pwd) != pwd:
        session.close()
        return ApiResponse(config.ACCESS_DENIED_MSG, status='403')

    h.login()
    session.add(h)
    session.commit()
    response = ApiResponse({
        'id': h._id,
        'session_token': h.session_token
    })
    session.close()
    return response


@hospitals.route('/logout/', methods=['POST'])
@hospital_login
def logout():
    data = json.loads(request.data)
    session = db.Session()
    hospital_id = data['hospital_id']
    # TODO: shiko per injection
    hospital = session.query(db.Hospital).filter_by(_id=hospital_id).first()
    hospital.logout()
    session.add(hospital)
    session.commit()
    session.close()
    return ApiResponse({
        'status': 'ok'
    })

# @hospitals.route('/whoami/', methods=['GET'])
# @hospital_login
# def things():
#     session = db.Session()
#     hospital_id = request.args.get('hospital_id', 0)
#     h = session.query(db.Hospital).filter_by(_id=hospital_id).first()
#     if h:
#         return ApiResponse({
#             'data': {
#                 'id': h._id,
#                 'name': h.name,
#                 'email': h.email,
#                 'address': h.address,
#                 'contact': h.contact
#             }
#         })
#     else:
#         return ApiResponse({
#             'data': 'none'
#         })