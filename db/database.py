import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'cunha_ffc')
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD', 'postgres')
        self.init_database()

    def get_connection(self):
        """Retorna uma conexão com o banco de dados PostgreSQL."""
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            return conn
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao banco de dados: {str(e)}")
            return None

    def init_database(self):
        """Inicializa o banco de dados com a tabela leads."""
        conn = self.get_connection()
        if not conn:
            logger.error("❌ Não foi possível conectar ao banco de dados")
            return

        try:
            cursor = conn.cursor()

            # Tabela de leads
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id SERIAL PRIMARY KEY,
                    cpf VARCHAR(11) UNIQUE NOT NULL,
                    nome VARCHAR(255) NOT NULL,
                    whatsapp VARCHAR(20) NOT NULL,
                    email VARCHAR(255),
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            logger.info("✅ Banco de dados inicializado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco de dados: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def save_lead(self, whatsapp_id, cpf, nome, email=None):
        """Salva um novo lead no banco de dados."""
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO leads (cpf, nome, whatsapp, email, data_cadastro, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (cpf) DO UPDATE SET
                    nome = EXCLUDED.nome,
                    whatsapp = EXCLUDED.whatsapp,
                    email = EXCLUDED.email,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            ''', (cpf, nome, whatsapp_id, email, datetime.now(), datetime.now()))

            lead_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"✅ Lead salvo: {cpf} - {nome}")
            return lead_id
        except Exception as e:
            logger.error(f"❌ Erro ao salvar lead: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()

    def get_lead_by_cpf(self, cpf):
        """Recupera um lead pelo CPF."""
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM leads WHERE cpf = %s', (cpf,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar lead: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()

    def get_lead_by_whatsapp(self, whatsapp_id):
        """Recupera um lead pelo ID do WhatsApp."""
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM leads WHERE whatsapp = %s', (whatsapp_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar lead: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()

    def get_all_leads(self):
        """Retorna todos os leads cadastrados."""
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM leads ORDER BY data_cadastro DESC')
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar leads: {str(e)}")
            return []
        finally:
            cursor.close()
            conn.close()

    def update_lead_email(self, cpf, email):
        """Atualiza o email de um lead."""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE leads SET email = %s, updated_at = %s WHERE cpf = %s
            ''', (email, datetime.now(), cpf))
            conn.commit()
            logger.info(f"✅ Email atualizado para CPF: {cpf}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar email: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()
