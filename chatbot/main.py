from flask import Flask, request, jsonify, send_from_directory
import requests
import os
import json
import time
from datetime import datetime, timedelta
import logging
import pickle
import hashlib
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__, static_folder='static')

# ----- CONFIGURATION AVANCÉE -----
API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-20b:free"

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dossier pour sauvegarder l'historique
HISTORY_DIR = "chat_history"
os.makedirs(HISTORY_DIR, exist_ok=True)

# ----- PROMPT INTELLIGENT AMÉLIORÉ -----
PROMPT_FINANCE = """
Tu es un assistant polyvalent et compétent.

**IDENTITÉ ET TON :**
- Tu es un assistant professionnel sans nom spécifique
- NE JAMAIS utiliser de noms comme "Alexandre", "Clara", "Marie", etc.
- Utilise "je" ou "votre assistant" pour te référer à toi-même
- Ton style est professionnel, empathique et direct
- Évite les formules trop familières ou personnelles

**SPÉCIALITÉ PRINCIPALE :**
Tu es expert en conseils financiers avec des compétences approfondies dans :
- Analyse financière approfondie
- Planification budgétaire et épargne
- Investissements et portefeuille
- Gestion de dettes et crédits
- Planification retraite
- Optimisation fiscale
- Éducation financière
- Marchés financiers

**COMPÉTENCES GÉNÉRALES :**
Tu peux également aider sur d'autres sujets comme :
- Questions générales et connaissances diverses
- Conseils pratiques du quotidien
- Aide à la décision
- Explications conceptuelles
- Réflexions personnelles et professionnelles

**DIRECTIVES DE RÉPONSE :**
1. Donne des réponses COMPLÈTES et DÉTAILLÉES sans coupures
2. Structure tes réponses avec des sections claires
3. Utilise le format Markdown pour une meilleure lisibilité
4. Si la réponse est longue, organise-la avec des titres et sous-titres
5. Termine toujours tes réponses de manière naturelle, pas brusquement

**ADAPTATION AU SUJET :**
- Si la question est financière : fournis une analyse experte et détaillée
- Si la question est hors finance : réponds de manière complète et utile
- Reconnais quand une question dépasse tes limites et oriente vers des experts si nécessaire

**FORMAT DE RÉPONSE :**
- Commence par une brève introduction du sujet
- Développe les points principaux avec des explications claires
- Utilise des exemples concrets quand c'est pertinent
- Propose des actions pratiques et réalisables
- Termine par un résumé des points clés
- Encourage les questions de suivi

**IMPORTANT :**
- Ne te présente jamais avec un nom spécifique
- Les réponses doivent être fluides et naturelles
- Adapte la complexité au niveau de l'utilisateur
- Sois transparent sur les limites de tes conseils
- Maintenir un ton professionnel mais accessible
- Pour les sujets sensibles (médical, juridique), recommande de consulter des experts
"""

# ----- GESTION D'HISTORIQUE AVANCÉE -----
class AdvancedHistoryManager:
    def __init__(self, history_dir="chat_history"):
        self.history_dir = history_dir
        self.active_sessions = {}
        os.makedirs(history_dir, exist_ok=True)
    
    def get_session_file(self, session_id):
        """Retourne le fichier d'historique pour une session"""
        session_hash = hashlib.md5(session_id.encode()).hexdigest()
        return os.path.join(self.history_dir, f"{session_hash}.pkl")
    
    def load_history(self, session_id):
        """Charge l'historique d'une session depuis le fichier"""
        session_file = self.get_session_file(session_id)
        
        if os.path.exists(session_file):
            try:
                with open(session_file, 'rb') as f:
                    history = pickle.load(f)
                    # Nettoyer l'historique ancien
                    cleaned_history = self.clean_old_messages(history)
                    self.active_sessions[session_id] = cleaned_history
                    return cleaned_history
            except Exception as e:
                logger.error(f"Erreur chargement historique {session_id}: {e}")
        
        # Nouvelle session
        self.active_sessions[session_id] = []
        return []
    
    def save_history(self, session_id, history):
        """Sauvegarde l'historique d'une session"""
        try:
            session_file = self.get_session_file(session_id)
            with open(session_file, 'wb') as f:
                pickle.dump(history, f)
            self.active_sessions[session_id] = history
        except Exception as e:
            logger.error(f"Erreur sauvegarde historique {session_id}: {e}")
    
    def add_message(self, session_id, role, content, message_type="text", topic="general"):
        """Ajoute un message à l'historique"""
        if session_id not in self.active_sessions:
            self.load_history(session_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "type": message_type,
            "topic": topic,
            "tokens_estimate": len(content.split()) // 4
        }
        
        self.active_sessions[session_id].append(message)
        
        # Sauvegarde automatique
        self.save_history(session_id, self.active_sessions[session_id])
        
        # Nettoyage automatique si trop long
        if len(self.active_sessions[session_id]) > 100:
            self.cleanup_history(session_id)
    
    def get_conversation_history(self, session_id, max_messages=15):
        """Récupère l'historique de conversation"""
        if session_id not in self.active_sessions:
            self.load_history(session_id)
        
        history = self.active_sessions.get(session_id, [])
        return history[-max_messages:]
    
    def get_full_history(self, session_id):
        """Récupère tout l'historique d'une session"""
        if session_id not in self.active_sessions:
            self.load_history(session_id)
        return self.active_sessions.get(session_id, [])
    
    def cleanup_history(self, session_id):
        """Nettoie l'historique pour garder les messages récents"""
        if session_id in self.active_sessions:
            # Garde les 50 derniers messages
            self.active_sessions[session_id] = self.active_sessions[session_id][-50:]
            self.save_history(session_id, self.active_sessions[session_id])
    
    def clean_old_messages(self, history, max_age_days=30):
        """Nettoie les messages trop anciens"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        cleaned_history = []
        
        for message in history:
            try:
                message_date = datetime.fromisoformat(message['timestamp'])
                if message_date > cutoff_date:
                    cleaned_history.append(message)
            except:
                # Garde le message si erreur de date
                cleaned_history.append(message)
        
        return cleaned_history
    
    def get_session_stats(self, session_id):
        """Retourne les statistiques d'une session"""
        history = self.get_full_history(session_id)
        if not history:
            return None
        
        user_messages = [m for m in history if m['role'] == 'user']
        assistant_messages = [m for m in history if m['role'] == 'assistant']
        
        # Analyse des sujets
        topics = {}
        for msg in history:
            topic = msg.get('topic', 'general')
            topics[topic] = topics.get(topic, 0) + 1
        
        return {
            'total_messages': len(history),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'first_message': history[0]['timestamp'] if history else None,
            'last_message': history[-1]['timestamp'] if history else None,
            'total_tokens_estimate': sum(m.get('tokens_estimate', 0) for m in history),
            'topics_distribution': topics
        }
    
    def delete_history(self, session_id):
        """Supprime l'historique d'une session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        session_file = self.get_session_file(session_id)
        if os.path.exists(session_file):
            os.remove(session_file)
            return True
        return False
    
    def get_all_sessions(self):
        """Retourne la liste de toutes les sessions"""
        sessions = []
        for filename in os.listdir(self.history_dir):
            if filename.endswith('.pkl'):
                session_id = filename.replace('.pkl', '')
                stats = self.get_session_stats(session_id)
                if stats:
                    sessions.append({
                        'session_id': session_id,
                        'stats': stats
                    })
        return sessions

# Initialisation du gestionnaire d'historique
history_manager = AdvancedHistoryManager()

# ----- GESTION DE CONVERSATION INTELLIGENTE -----
class IntelligentConversationManager:
    def __init__(self):
        self.conversation_context = {}
    
    def clean_unwanted_names(self, content):
        """Nettoie les noms indésirables des réponses"""
        unwanted_names = [
            "Alexandre", "Clara", "Marie", "Jean", "Sophie", "Pierre",
            "Thomas", "Laura", "Nicolas", "Alice", "David", "Sarah",
            "Michael", "Jennifer", "Chris", "Emma", "Alex", "Anna",
            "Robert", "Lisa", "Mark", "Julia"
        ]
        
        cleaned_content = content
        for name in unwanted_names:
            patterns = [
                f"Je suis {name}",
                f"je suis {name}",
                f"{name}, votre conseiller",
                f"{name} votre conseiller",
                f"Mon nom est {name}",
                f"mon nom est {name}"
            ]
            
            for pattern in patterns:
                cleaned_content = cleaned_content.replace(
                    pattern, "Je suis votre assistant"
                )
        
        return cleaned_content
    
    def analyze_topic(self, message):
        """Analyse le sujet du message pour classification"""
        message_lower = message.lower()
        
        # Mots-clés financiers
        finance_keywords = [
            "budget", "épargne", "investissement", "bourse", "action", "obligation",
            "retraite", "prêt", "crédit", "dette", "taux", "intérêt", "banque",
            "compte", "livret", "assurance", "fiscalité", "impôt", "patrimoine",
            "finance", "économ", "placement", "portefeuille", "dividende",
            "courtier", "marché", "crypto", "bitcoin", "épargner", "dépenser",
            "revenu", "salaire", "pension", "allocation", "capital", "liquidité"
        ]
        
        # Mots-clés pour sujets sensibles
        sensitive_keywords = [
            "médical", "docteur", "médecin", "maladie", "santé", "médicament",
            "juridique", "avocat", "loi", "tribunal", "procès", "contrat",
            "psychologique", "dépression", "anxiété", "thérapie", "psychologue",
            "urgence", "suicide", "crise"
        ]
        
        if any(keyword in message_lower for keyword in finance_keywords):
            return "finance"
        elif any(keyword in message_lower for keyword in sensitive_keywords):
            return "sensitive"
        else:
            return "general"

conversation_manager = IntelligentConversationManager()

# ----- FONCTIONS INTELLIGENTES -----
def get_session_id():
    """Génère un ID de session unique"""
    user_agent = request.headers.get('User-Agent', '')
    ip_address = request.remote_addr
    unique_string = f"{ip_address}_{user_agent}_{time.time()}"
    return hashlib.md5(unique_string.encode()).hexdigest()

def create_intelligent_payload(messages, user_message):
    """Crée un payload optimisé pour des réponses intelligentes"""
    
    question_type = analyze_question_type(user_message)
    topic = conversation_manager.analyze_topic(user_message)
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": PROMPT_FINANCE},
            *messages
        ],
        "max_tokens": 2500,
        "temperature": 0.7,
        "top_p": 0.9,
        "frequency_penalty": 0.3,
        "presence_penalty": 0.2,
    }
    
    # Adaptation selon le type de question et le sujet
    if question_type == "complex":
        payload["max_tokens"] = 3000
    elif question_type == "simple":
        payload["max_tokens"] = 1500
    
    # Adaptation pour sujets sensibles
    if topic == "sensitive":
        payload["temperature"] = 0.5  # Plus conservateur
    
    return payload

def analyze_question_type(message):
    """Analyse le type de question pour adapter la réponse"""
    message_lower = message.lower()
    
    complex_keywords = [
        "plan détaillé", "stratégie complète", "analyse approfondie",
        "toutes les options", "comparaison détaillée", "guide complet",
        "étape par étape", "long terme", "portfolio", "investissement",
        "retraite", "patrimoine", "budget annuel", "épargne long terme",
        "explique en détail", "tous les aspects", "comprehensive"
    ]
    
    simple_keywords = [
        "bonjour", "salut", "merci", "quoi", "comment", "pourquoi",
        "définition", "explication simple", "rapide", "hello", "hi",
        "ça va", "comment vas-tu", "bien et toi"
    ]
    
    if any(keyword in message_lower for keyword in complex_keywords):
        return "complex"
    elif any(keyword in message_lower for keyword in simple_keywords):
        return "simple"
    
    return "standard"

def ensure_complete_response(response_text, topic):
    """Vérifie et complète les réponses coupées"""
    if not response_text.strip():
        return "Je n'ai pas pu générer une réponse complète. Pouvez-vous reformuler votre question ?"
    
    # Vérifie si la réponse semble coupée
    ending_marks = ['.', '!', '?', '```']
    last_char = response_text.strip()[-1] if response_text.strip() else ''
    
    if last_char not in ending_marks and len(response_text.split()) > 100:
        # La réponse semble coupée
        if "```" in response_text:
            # Code block non fermé
            response_text += "\n```"
        
        # Message de fin adapté au sujet
        if topic == "finance":
            response_text += "\n\n*Pour plus de détails sur des points financiers spécifiques, n'hésitez pas à poser des questions complémentaires.*"
        else:
            response_text += "\n\n*N'hésitez pas à me poser d'autres questions si vous souhaitez plus de détails.*"
    
    return response_text

# ----- ROUTES AVEC HISTORIQUE -----
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/chat', methods=['POST'])
def intelligent_chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id') or get_session_id()
        
        # Validation
        if not user_message:
            return jsonify({
                'reply': 'Veuillez entrer un message pour démarrer la conversation.',
                'error': 'empty_message'
            }), 400
        
        if len(user_message) > 2000:
            return jsonify({
                'reply': 'Votre message est trop long. Veuillez le diviser en plusieurs questions.',
                'error': 'message_too_long'
            }), 400
        
        # Analyse du sujet
        topic = conversation_manager.analyze_topic(user_message)
        
        # Charger l'historique
        conversation_history = history_manager.get_conversation_history(session_id)
        
        # Construction des messages
        messages = []
        for msg in conversation_history[-12:]:
            messages.append({
                "role": msg["role"], 
                "content": msg["content"]
            })
        
        messages.append({"role": "user", "content": user_message})
        
        # Headers
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': request.url_root,
            'X-Title': 'Assistant Intelligent Polyvalent'
        }
        
        # Payload intelligent
        payload = create_intelligent_payload(messages, user_message)
        
        logger.info(f"Session: {session_id} - Question: {user_message[:50]}... - Sujet: {topic}")
        
        # Requête
        timeout = 45 if analyze_question_type(user_message) == "complex" else 30
        response = requests.post(
            OPENROUTER_API_URL, 
            json=payload, 
            headers=headers,
            timeout=timeout
        )
        
        if response.status_code == 200:
            bot_response = response.json()['choices'][0]['message']['content']
            
            # Nettoyage et validation
            cleaned_response = conversation_manager.clean_unwanted_names(bot_response)
            complete_response = ensure_complete_response(cleaned_response, topic)
            
            # Sauvegarde dans l'historique avec classification du sujet
            history_manager.add_message(session_id, "user", user_message, topic=topic)
            history_manager.add_message(session_id, "assistant", complete_response, topic=topic)
            
            # Statistiques de la session
            session_stats = history_manager.get_session_stats(session_id)
            
            logger.info(f"Réponse générée - Session: {session_id} - Sujet: {topic}")
            
            return jsonify({
                'reply': complete_response,
                'session_id': session_id,
                'response_type': analyze_question_type(user_message),
                'topic': topic,
                'session_stats': session_stats
            })
            
        else:
            error_msg = f"Erreur API: {response.status_code}"
            logger.error(f"{error_msg} - Session: {session_id}")
            
            if response.status_code == 429:
                friendly_error = "Je suis actuellement très sollicité. Veuillez réessayer dans quelques instants."
            elif response.status_code >= 500:
                friendly_error = "Le service rencontre des difficultés techniques. Veuillez patienter."
            else:
                friendly_error = "Désolé, je n'ai pas pu traiter votre demande. Reformulez votre question s'il vous plaît."
            
            return jsonify({
                'reply': friendly_error,
                'error': 'api_error',
                'session_id': session_id
            }), 500
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout - Session: {session_id}")
        return jsonify({
            'reply': "Votre question nécessite une analyse approfondie qui prend plus de temps. Pouvez-vous la simplifier ou la diviser ?",
            'error': 'timeout',
            'session_id': session_id
        }), 504
        
    except Exception as e:
        logger.error(f"Erreur inattendue - Session: {session_id}: {str(e)}")
        return jsonify({
            'reply': "Une erreur inattendue s'est produite. Notre équipe technique en est informée.",
            'error': 'unexpected_error',
            'session_id': session_id
        }), 500

# ----- ROUTES D'HISTORIQUE -----
@app.route('/history/<session_id>', methods=['GET'])
def get_conversation_history(session_id):
    """Récupère l'historique complet d'une session"""
    try:
        history = history_manager.get_full_history(session_id)
        stats = history_manager.get_session_stats(session_id)
        
        return jsonify({
            'session_id': session_id,
            'history': history,
            'stats': stats,
            'total_messages': len(history)
        })
    except Exception as e:
        logger.error(f"Erreur récupération historique {session_id}: {e}")
        return jsonify({'error': 'history_not_found'}), 404

@app.route('/history/<session_id>/clear', methods=['DELETE'])
def clear_conversation_history(session_id):
    """Efface l'historique d'une session"""
    try:
        success = history_manager.delete_history(session_id)
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Historique effacé avec succès',
                'session_id': session_id
            })
        else:
            return jsonify({'error': 'session_not_found'}), 404
    except Exception as e:
        logger.error(f"Erreur effacement historique {session_id}: {e}")
        return jsonify({'error': 'clear_failed'}), 500

@app.route('/history/<session_id>/export', methods=['GET'])
def export_conversation_history(session_id):
    """Exporte l'historique au format texte"""
    try:
        history = history_manager.get_full_history(session_id)
        if not history:
            return jsonify({'error': 'no_history'}), 404
        
        # Format texte lisible
        export_text = f"Historique de conversation - Session: {session_id}\n"
        export_text += "=" * 50 + "\n\n"
        
        for i, message in enumerate(history, 1):
            timestamp = message['timestamp']
            role = "Utilisateur" if message['role'] == 'user' else "Assistant"
            content = message['content']
            topic = message.get('topic', 'general')
            
            export_text += f"{i}. [{timestamp}] {role} - Sujet: {topic}:\n"
            export_text += f"{content}\n"
            export_text += "-" * 30 + "\n"
        
        return jsonify({
            'session_id': session_id,
            'export_text': export_text,
            'total_messages': len(history)
        })
    except Exception as e:
        logger.error(f"Erreur export historique {session_id}: {e}")
        return jsonify({'error': 'export_failed'}), 500

@app.route('/sessions', methods=['GET'])
def list_all_sessions():
    """Liste toutes les sessions disponibles"""
    try:
        sessions = history_manager.get_all_sessions()
        return jsonify({
            'total_sessions': len(sessions),
            'sessions': sessions
        })
    except Exception as e:
        logger.error(f"Erreur liste sessions: {e}")
        return jsonify({'error': 'list_failed'}), 500

@app.route('/stats', methods=['GET'])
def get_global_stats():
    """Retourne les statistiques globales"""
    try:
        sessions = history_manager.get_all_sessions()
        total_messages = sum(session['stats']['total_messages'] for session in sessions)
        total_sessions = len(sessions)
        
        # Analyse des sujets globaux
        global_topics = {}
        for session in sessions:
            for topic, count in session['stats'].get('topics_distribution', {}).items():
                global_topics[topic] = global_topics.get(topic, 0) + count
        
        return jsonify({
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'average_messages_per_session': total_messages / total_sessions if total_sessions > 0 else 0,
            'topics_distribution': global_topics
        })
    except Exception as e:
        logger.error(f"Erreur stats globales: {e}")
        return jsonify({'error': 'stats_failed'}), 500

# Route de santé
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len(history_manager.active_sessions),
        'total_saved_sessions': len(history_manager.get_all_sessions())
    })

# Servir les fichiers statiques
@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    # Configuration
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    
    print("🤖 Assistant Intelligent Polyvalent démarré !")
    print(f"📍 URL: http://localhost:{port}")
    print(f"📊 Historique sauvegardé dans: {HISTORY_DIR}")
    print("💬 Compétences: Finance + Questions générales")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )