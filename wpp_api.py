from flask import Flask, request, jsonify
import requests
import os
import logging
from dotenv import load_dotenv
from services.ura import URAService

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
ura = URAService()

class WppApi:
    def __init__(self):
        self.app = Flask(__name__)
        self.VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
        self.ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
        self.API_URL = 'https://graph.facebook.com/v25.0/'
        self.PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
        
        logger.info(f"✅ VERIFY_TOKEN configurado: {'Sim' if self.VERIFY_TOKEN else 'NÃO'}")
        logger.info(f"✅ ACCESS_TOKEN configurado: {'Sim' if self.ACCESS_TOKEN else 'NÃO'}")
        
        # Register routes
        self.app.add_url_rule('/webhook', 'verify_webhook', self.verify_webhook, methods=['GET'])
        self.app.add_url_rule('/webhook', 'handle_message', self.handle_message, methods=['POST'])

    def verify_webhook(self):
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode and token:
            if mode == 'subscribe' and token == self.VERIFY_TOKEN:
                print('WEBHOOK_VERIFIED')
                return challenge, 200
            else:
                return 'Forbidden', 403
        return 'Bad Request', 400

    def handle_message(self):
        try:
            data = request.get_json()
            logger.info(f"📩 Payload recebido: {data}")

            if not data:
                return jsonify({'status': 'no data'}), 200

            if 'entry' in data:
                for entry in data['entry']:
                    for change in entry.get('changes', []):
                        if change.get('field') == 'messages':
                            value = change.get('value', {})
                            
                            # 👇 LOG COMPLETO
                            logger.info(f"🔄 Value: {value}")

                            messages = value.get('messages', [])

                            for message in messages:
                                sender_id = message.get('from')
                                message_text = ''

                                if message.get('text'):
                                    message_text = message['text'].get('body', '')
                                elif message.get('button'):
                                    message_text = message['button'].get('payload') or message['button'].get('text', '')
                                elif message.get('interactive'):
                                    interactive = message['interactive']
                                    button_reply = interactive.get('button_reply') or interactive.get('list_reply')
                                    if button_reply:
                                        message_text = button_reply.get('id') or button_reply.get('title', '')

                                message_text = message_text.strip()
                                logger.info(f"💬 De: {sender_id} | Msg: {message_text}")

                                if message_text:
                                    self.process_user_message(sender_id, message_text)

            return jsonify({'status': 'ok'}), 200

        except Exception as e:
            logger.error(f"❌ ERRO NO WEBHOOK: {str(e)}")
            return jsonify({'error': str(e)}), 200  # 👈 IMPORTANTE: nunca retornar erro

    def process_user_message(self, sender_id, message_text):
        reply_payload = ura.get_response(sender_id, message_text)
        if reply_payload:
            self.send_message(sender_id, reply_payload)

    def send_message(self, recipient_id, message_payload):
        url = f"{self.API_URL}{self.PHONE_NUMBER_ID}/messages"
        headers = {
            'Authorization': f'Bearer {self.ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        payload = {
            'messaging_product': 'whatsapp',
            'to': recipient_id
        }

        if isinstance(message_payload, str):
            payload.update({
                'type': 'text',
                'text': {'body': message_payload}
            })
        else:
            payload.update(message_payload)

        logger.info(f"📤 Enviando mensagem para {recipient_id}")
        logger.info(f"URL: {url}")
        logger.info(f"Payload: {payload}")

        try:
            response = requests.post(url, json=payload, headers=headers)
            logger.info(f"Status: {response.status_code}")

            if response.status_code == 200:
                logger.info(f"✅ Mensagem enviada com sucesso!")
                return response.json()
            else:
                logger.error(f"❌ Erro na API: {response.text}")
                return response.json()
        except Exception as e:
            logger.error(f"❌ Exceção: {str(e)}")
            return {'error': str(e)}

    def run(self, debug=True, port=5001):
        self.app.run(debug=debug, port=port)