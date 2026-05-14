import re
from .ura_utils import UraUtils
from db.database import Database

class URAService:
    CPF_PATTERN = re.compile(r'(\d{11})')
    db_ffc = Database()  # Instância do banco de dados para salvar leads 
    
    def __init__(self, database=None):
        self.sessions = {}
        self.ura_utils = UraUtils()
        self.database = self.db_ffc  # Use a instância do banco de dados da classe

    def main_menu_payload(self, body_text=None):
        if body_text is None:
            body_text = '🎓 Bem-vindo ao atendimento do Curso Preparatório e Pré-vestibular!\n\nEscolha uma opção abaixo:'
        return self.ura_utils.build_button_payload(
            body_text,
            [
                {'type': 'reply', 'reply': {'id': '1', 'title': '1 - Curso Preparatório'}},
                {'type': 'reply', 'reply': {'id': '2', 'title': '2 - Pré-Vestibular'}},
                {'type': 'reply', 'reply': {'id': '3', 'title': '3 - Atendente humano'}},
                {'type': 'reply', 'reply': {'id': '0', 'title': '0 - Menu principal'}}
            ]
        )

    def preparatorio_menu_payload(self):
        return self.ura_utils.build_button_payload(
            '📘 Bem vindo ao FFC\n\n Força e Foco Cursos \n\nEscolha a opção desejada:',
            [
                {'type': 'reply', 'reply': {'id': '1a', 'title': '1a - Horários e modalidades'}},
                {'type': 'reply', 'reply': {'id': '1b', 'title': '1b - Valores e pagamento'}},
                {'type': 'reply', 'reply': {'id': '1c', 'title': '1c - Como se inscrever'}},
                {'type': 'reply', 'reply': {'id': '0', 'title': '0 - Menu principal'}}
            ]
        )

    def pre_vestibular_menu_payload(self):
        return self.ura_utils.build_button_payload(
            '🏆 Pré-Vestibular:\n\nEscolha a opção desejada:',
            [
                {'type': 'reply', 'reply': {'id': '2a', 'title': '2a - Calendário e horários'}},
                {'type': 'reply', 'reply': {'id': '2b', 'title': '2b - Investimento e condições'}},
                {'type': 'reply', 'reply': {'id': '2c', 'title': '2c - Inscrições'}},
                {'type': 'reply', 'reply': {'id': '0', 'title': '0 - Menu principal'}}
            ]
        )

    def get_response(self, sender_id, message_text):
        normalized = self.ura_utils.normalize_input(message_text)
        session = self.sessions.get(sender_id, {})

        if session.get('personal_data') is None and session.get('stage') not in ['ASK_CPF', 'ASK_NAME']:
            self.sessions[sender_id] = {'stage': 'ASK_CPF'}
            return self.ura_utils.build_text_payload(
                'Olá! Para começar, por favor envie apenas o seu CPF sem pontos ou hífens.\n\n'
                'Exemplo: 12345678909'
            )

        if normalized in ['menu', 'iniciar', 'olá', 'ola', 'oi', 'bom dia', 'boa tarde', 'boa noite'] and session.get('personal_data'):
            self.sessions[sender_id]['stage'] = 'MAIN_MENU'
            return self.main_menu_payload()

        stage = self.sessions.get(sender_id, {'stage': 'MAIN_MENU'})['stage']

        if stage == 'ASK_CPF':
            return self.handle_cpf(sender_id, message_text)
        elif stage == 'ASK_NAME':
            return self.handle_name(sender_id, message_text)
        elif stage == 'ASK_EMAIL':
            return self.handle_email(sender_id, message_text)
        elif stage == 'MAIN_MENU':
            return self.handle_main_menu(sender_id, normalized)
        elif stage == 'PREPARATORIO_MENU':
            return self.handle_preparatorio_menu(sender_id, normalized)
        elif stage == 'PRE_VESTIBULAR_MENU':
            return self.handle_pre_vestibular_menu(sender_id, normalized)
        else:
            self.sessions[sender_id] = {'stage': 'MAIN_MENU'}
            return self.main_menu_payload()

    def handle_cpf(self, sender_id, message_text):
        cpf_match = self.CPF_PATTERN.search(message_text)
        if not cpf_match:
            return self.ura_utils.build_text_payload(
                'Não consegui identificar um CPF válido. Por favor envie seu CPF sem pontos ou hífens.\n\n'
                'Exemplo: 12345678909'
            )

        cpf = self.ura_utils.normalize_cpf(cpf_match.group(1))
        if not cpf:
            return self.ura_utils.build_text_payload(
                'CPF inválido. Envie seu CPF sem pontos ou hífens.\n\n'
                'Exemplo: 12345678909'
            )

        self.sessions[sender_id] = {
            'stage': 'ASK_NAME',
            'personal_data': {'cpf': cpf}
        }
        return self.ura_utils.build_text_payload(
            f'CPF {cpf} registrado com sucesso. Agora, por favor envie seu nome completo.'
        )

    def handle_name(self, sender_id, message_text):
        name = self.ura_utils.normalize_input_upper(message_text)
        if not name or len(name) < 5:
            return self.ura_utils.build_text_payload(
                'Por favor, envie seu nome completo.\n\n'
                'Exemplo: João da Silva'
            )

        session = self.sessions.get(sender_id, {})
        personal_data = session.get('personal_data', {})
        personal_data['name'] = name
        self.sessions[sender_id] = {
            'stage': 'ASK_EMAIL',
            'personal_data': personal_data
        }

        return self.main_menu_payload(
            f'Obrigado, {name}! CPF {personal_data.get("cpf")} registrado.\n\nEscolha uma opção abaixo:'
        )
        
    def handle_email(self, sender_id, message_text):
        email = self.ura_utils.normalize_input(message_text)
        if not email or '@' not in email:
            return self.ura_utils.build_text_payload(
                'Por favor, envie um endereço de email válido.\n\n'
                'Exemplo: seuemail@hotmail.com'
            )
        session = self.sessions.get(sender_id, {})
        personal_data = session.get('personal_data', {})
        personal_data['email'] = email
        self.sessions[sender_id] = {
            'stage': 'MAIN_MENU',
            'personal_data' : personal_data
        }
        
        # Salvar lead no banco de dados
        if self.database:
            cpf = personal_data.get('cpf')
            name = personal_data.get('name')
            self.database.save_lead(sender_id, cpf, name, email)
            
        return self.main_menu_payload(
            f'Obrigado, {personal_data.get("name")}! CPF {personal_data.get("cpf")} e E-mail {personal_data.get("email")} registrados.\n\nEscolha uma opção abaixo:'
        )

    def handle_main_menu(self, sender_id, message_text):
        if message_text == '1':
            self.sessions[sender_id] = {'stage': 'PREPARATORIO_MENU'}
            return self.preparatorio_menu_payload()
        elif message_text == '2':
            self.sessions[sender_id] = {'stage': 'PRE_VESTIBULAR_MENU'}
            return self.pre_vestibular_menu_payload()
        elif message_text == '3':
            self.sessions[sender_id] = {'stage': 'MAIN_MENU'}
            return self.ura_utils.build_text_payload(
                '🙋‍♂️ Um atendente humano entrará em contato em breve.\n\n'
                'Envie "menu" para voltar ao menu principal.'
            )
        elif message_text == '0':
            self.sessions[sender_id] = {'stage': 'MAIN_MENU'}
            return self.main_menu_payload()
        else:
            return self.ura_utils.build_text_payload(
                'Desculpe, não entendi.\n\n'
                'Envie "menu" para ver as opções novamente.\n'
                'Digite 1 para Curso Preparatório, 2 para Pré-Vestibular ou 3 para atendente humano.'
            )

    def handle_preparatorio_menu(self, sender_id, message_text):
        if message_text == '1a':
            return self.ura_utils.build_text_payload(
                '🕒 Horários e modalidades Preparatório:\n'
                '- Turmas presenciais e online.\n'
                '- Plantões de dúvidas e revisões.\n\n'
                'Envie 0 para voltar ao menu principal ou "menu" a qualquer momento.'
            )
        elif message_text == '1b':
            return self.ura_utils.build_text_payload(
                '💳 Valores e pagamento Preparatório:\n'
                '- Planos mensais a partir de R$ XXX.\n'
                '- Parcelamento no cartão em até 3x.\n\n'
                'Envie 0 para voltar ao menu principal ou "menu" a qualquer momento.'
            )
        elif message_text == '1c':
            return self.ura_utils.build_text_payload(
                '📝 Inscrição Preparatório:\n'
                '- Envie seus dados: nome completo, telefone e ano escolar.\n'
                '- Um consultor entrará em contato para finalizar a matrícula.\n\n'
                'Envie 0 para voltar ao menu principal ou "menu" a qualquer momento.'
            )
        elif message_text == '0':
            self.sessions[sender_id] = {'stage': 'MAIN_MENU'}
            return self.main_menu_payload()
        else:
            return self.ura_utils.build_text_payload(
                'Opção inválida.\n\n'
                'Digite 1a, 1b ou 1c para saber mais sobre o Preparatório, ou 0 para voltar ao menu principal.'
            )

    def handle_pre_vestibular_menu(self, sender_id, message_text):
        if message_text == '2a':
            return self.ura_utils.build_text_payload(
                '📅 Calendário e horários Pré-Vestibular:\n'
                '- Aulas intensivas e simulados semanais.\n\n'
                'Envie 0 para voltar ao menu principal ou "menu" a qualquer momento.'
            )
        elif message_text == '2b':
            return self.ura_utils.build_text_payload(
                '💲 Investimento Pré-Vestibular:\n'
                '- Planos a partir de R$ YYY.\n'
                '- Condições especiais para inscrições antecipadas.\n\n'
                'Envie 0 para voltar ao menu principal ou "menu" a qualquer momento.'
            )
        elif message_text == '2c':
            return self.ura_utils.build_text_payload(
                '📝 Inscrição Pré-Vestibular:\n'
                '- Envie seus dados: nome completo e telefone.\n'
                '- Um consultor retornará para finalizar a matrícula.\n\n'
                'Envie 0 para voltar ao menu principal ou "menu" a qualquer momento.'
            )
        elif message_text == '0':
            self.sessions[sender_id] = {'stage': 'MAIN_MENU'}
            return self.main_menu_payload()
        else:
            return self.ura_utils.build_text_payload(
                'Opção inválida.\n\n'
                'Digite 2a, 2b ou 2c para saber mais sobre o Pré-Vestibular, ou 0 para voltar ao menu principal.'
            )
