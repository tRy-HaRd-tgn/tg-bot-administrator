import os
import json
import uuid
from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, List, Any, Optional
import asyncio
import requests
from io import BytesIO
from PIL import Image

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from loguru import logger

api_bp = Blueprint('api', __name__)

# Импорт всех view-функций из api_views
from .api_views.allowed_file import allowed_file
from .api_views.run_async import run_async
from .api_views.get_chat_info_sync import get_chat_info_sync
from .api_views.get_campaigns import get_campaigns
from .api_views.get_campaign import get_campaign
from .api_views.create_campaign import create_campaign
from .api_views.delete_campaign import delete_campaign
from .api_views.toggle_campaign_status import toggle_campaign_status
from .api_views.complete_campaign import complete_campaign
from .api_views.get_chats import get_chats
from .api_views.add_chat import add_chat
from .api_views.delete_chat import delete_chat
from .api_views.update_chat_info import update_chat_info
from .api_views.get_campaigns_statistics import get_campaigns_statistics
from .api_views.get_chats_statistics import get_chats_statistics
from .api_views.get_calendar_events import get_calendar_events
from .api_views.update_all_chats_info import update_all_chats_info
from .api_views.test_chat import test_chat
from .api_views.test_chat_parameters import test_chat_parameters
from .api_views.get_chat_photo import get_chat_photo

@api_bp.route('/campaigns', methods=['GET'])
@api_bp.route('/campaigns/', methods=['GET'])
@login_required
def campaigns_route():
    return get_campaigns()

@api_bp.route('/campaigns/<campaign_id>', methods=['GET'])
@login_required
def campaign_route(campaign_id):
    return get_campaign(campaign_id)

@api_bp.route('/campaigns', methods=['POST'])
@login_required
def create_campaign_route():
    return create_campaign()

@api_bp.route('/campaigns/<campaign_id>', methods=['DELETE'])
@login_required
def delete_campaign_route(campaign_id):
    return delete_campaign(campaign_id)

@api_bp.route('/campaigns/<campaign_id>/toggle-status', methods=['POST'])
@login_required
def toggle_campaign_status_route(campaign_id):
    return toggle_campaign_status(campaign_id)

@api_bp.route('/campaigns/<campaign_id>/complete', methods=['POST'])
@login_required
def complete_campaign_route(campaign_id):
    return complete_campaign(campaign_id)

@api_bp.route('/chats', methods=['GET'])
@login_required
def get_chats_route():
    return get_chats()

@api_bp.route('/chats', methods=['POST'])
@login_required
def add_chat_route():
    return add_chat()

@api_bp.route('/chats/<chat_id>', methods=['DELETE'])
@login_required
def delete_chat_route(chat_id):
    return delete_chat(chat_id)

@api_bp.route('/chats/<chat_id>/update-info', methods=['POST'])
@login_required
def update_chat_info_route(chat_id):
    return update_chat_info(chat_id)

@api_bp.route('/statistics/campaigns', methods=['GET'])
@login_required
def get_campaigns_statistics_route():
    return get_campaigns_statistics()

@api_bp.route('/statistics/chats', methods=['GET'])
@login_required
def get_chats_statistics_route():
    return get_chats_statistics()

@api_bp.route('/calendar/events', methods=['GET'])
@login_required
def get_calendar_events_route():
    return get_calendar_events()

@api_bp.route('/chats/update-all-info', methods=['POST'])
@login_required
def update_all_chats_info_route():
    return update_all_chats_info()

@api_bp.route('/chats/<chat_id>/test', methods=['POST'])
@login_required
def test_chat_route(chat_id):
    return test_chat(chat_id)

@api_bp.route('/chats/<chat_id>/test-parameters', methods=['POST'])
@login_required
def test_chat_parameters_route(chat_id):
    return test_chat_parameters(chat_id)

@api_bp.route('/chat-photo/<file_id>', methods=['GET'])
@login_required
def get_chat_photo_route(file_id):
    return get_chat_photo(file_id)

# Здесь должны быть только декораторы и вызовы функций, например:
# @api_bp.route('/campaigns', methods=['GET'])
# @login_required
# def get_campaigns_route():
#     return get_campaigns()

# ... (аналогично для всех остальных роутов)