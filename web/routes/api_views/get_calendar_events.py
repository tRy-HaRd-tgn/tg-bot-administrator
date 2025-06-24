from datetime import datetime, timedelta
from flask import jsonify, current_app
from loguru import logger
from flask_login import login_required

def get_calendar_events():
    """Получение событий для календаря"""
    try:
        scheduler = current_app.scheduler
        campaigns = list(scheduler.campaigns.values())
        events = []
        for campaign in campaigns:
            try:
                if not campaign.get('start_date') or not campaign.get('end_date'):
                    continue
                status = campaign.get('status', 'draft')
                post_time = campaign.get('post_time', '12:00')
                start_date = datetime.fromisoformat(campaign['start_date']).date()
                end_date = datetime.fromisoformat(campaign['end_date']).date()
                publication_dates = []
                days_of_week = campaign.get('days_of_week', '')
                if days_of_week:
                    weekdays = [int(day) for day in days_of_week.split(',') if day.isdigit()]
                    current_date = start_date
                    while current_date <= end_date:
                        if (current_date.weekday() + 1) % 7 + 1 in weekdays:
                            publication_dates.append(current_date)
                        current_date += timedelta(days=1)
                specific_dates = campaign.get('specific_dates', '')
                if specific_dates:
                    dates = specific_dates.split(',')
                    for date_str in dates:
                        try:
                            date_obj = datetime.fromisoformat(date_str).date()
                            if start_date <= date_obj <= end_date:
                                publication_dates.append(date_obj)
                        except:
                            continue
                if not publication_dates:
                    if campaign.get('repeat_enabled', False):
                        current_date = start_date
                        while current_date <= end_date:
                            publication_dates.append(current_date)
                            current_date += timedelta(days=1)
                    else:
                        publication_dates.append(start_date)
                publication_dates = list(set(publication_dates))
                for pub_date in publication_dates:
                    events.append({
                        'title': campaign.get('name', 'Без названия'),
                        'date': pub_date.isoformat(),
                        'time': post_time,
                        'type': 'campaign',
                        'description': campaign.get('message_text', '')[:100] + '...' if len(campaign.get('message_text', '')) > 100 else campaign.get('message_text', ''),
                        'campaign_id': campaign.get('id'),
                        'campaign_name': campaign.get('name'),
                        'status': status,
                        'chats': campaign.get('chats', []),
                        'media_files': campaign.get('media_files', []),
                        'buttons': campaign.get('buttons', [])
                    })
            except Exception as e:
                logger.error(f"Ошибка при обработке кампании для календаря: {e}")
                continue
        return jsonify({'events': events})
    except Exception as e:
        logger.error(f"Ошибка при получении событий календаря: {e}")
        return jsonify({'error': str(e)}), 500 