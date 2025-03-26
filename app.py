from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import mysql.connector
import re
from textblob import TextBlob
from symspellpy import SymSpell
import os
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

# Flask app initialization
app = Flask(__name__)

# Function to connect to MySQL database
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),  # Default to 3306 if no port
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

# Create the Signup table if it doesn't exist
def create_signup_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Signup (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# Call this function 
create_signup_table()

# Route for registration form display
@app.route('/register', methods=['POST', 'GET'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        if not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'

        conn = get_db_connection()
        cur = conn.cursor()

        # Check for existing username or email before inserting
        cur.execute("SELECT * FROM Signup WHERE username = %s OR email = %s;", (username, email))
        existing_user = cur.fetchone()
        if existing_user:
            error_message = "Username or email already exists."
            return render_template('register.html', error=error_message)

        try:
            cur.execute("INSERT INTO Signup (username, email, password_hash) VALUES (%s, %s, %s);", (username, email, password))
            conn.commit()
            return render_template('login.html')  # Redirect to login page after successful registration
        except Exception as e:
            error_message = f"Registration failed: {e}"
            return render_template('register.html', error=error_message)
        finally:
            cur.close()
            conn.close()

    return render_template('register.html', error_message=msg)

# Route for login form display
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM Signup WHERE username = %s", (username,))
        user = cur.fetchone()

        if user is None:
            error_message = "Invalid username or password."
            return render_template('login.html', error=error_message)

        return redirect(url_for('home'))  # Redirect to protected content after successful login

    return render_template('login.html')

# Initialize SymSpell
sym_spell = SymSpell(max_dictionary_edit_distance=2)
dictionary_path = "frequency_dictionary_en_82_765.txt"

# Load dictionary and check if it's working
if not sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1):
    print("Error: Dictionary file not found or failed to load.")

def spell_check(text):
    if not text.strip():
        return text  # Return original text if empty

    suggestions = sym_spell.lookup_compound(text, max_edit_distance=2)
    corrected_text = suggestions[0].term if suggestions else text

    # Ensure proper sentence formatting
    corrected_text = re.sub(r'([.!?])(\w)', r'\1 \2', corrected_text)  # Add space after punctuation
    corrected_text = corrected_text.capitalize()  # Capitalize first letter

    return corrected_text

@app.route('/spellchecker', methods=['POST', 'GET'])
def spellchecker():
    if request.method == 'POST':
        text = request.form['fieldvalues']
        corrected_text = spell_check(text)
        return render_template("spellchecker.html", original=text, corrected=corrected_text)
    return render_template("spellchecker.html")

@app.route('/grammarcheck', methods=['POST', 'GET'])
def grammar_check():
    if request.method == 'POST':
        text = request.form['text']
        url = "https://api.languagetool.org/v2/check"
        params = {'text': text, 'language': 'en-US'}
        response = requests.post(url, data=params).json()

        errors = []
        corrected_text = text

        for match in response.get("matches", []): 
            incorrect_word = match["context"]["text"]
            suggestions = [sug["value"] for sug in match["replacements"]]
            
            if suggestions:
                corrected_text = corrected_text.replace(incorrect_word, suggestions[0], 1)  # Replace first occurrence only

            errors.append({
                "message": match["message"],
                "word": incorrect_word,
                "suggestions": suggestions
            })

        return render_template("grammarcheck.html", original_text=text, corrected_text=corrected_text, errors=errors)

    return render_template("grammarcheck.html")

@app.route('/summarize', methods=['POST', 'GET'])
def summarize():
    if request.method == 'POST':
        text = request.form['text']
        num_sentences = request.form.get('num_sentences', '3')  # Default to 3 sentences
        try:
            num_sentences = int(num_sentences)
        except ValueError:
            num_sentences = 3

        # Using Sumy for summarization
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, num_sentences)

        summarized_text = " ".join(str(sentence) for sentence in summary)

        return render_template("summarize.html", summary=summarized_text, original_text=text)

    return render_template("summarize.html", summary="", original_text="")

@app.route('/home')
def home():
    return render_template('home.html')

if __name__ == "__main__":
    app.run(debug=True, port=5000)
