from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import mysql.connector
import re
from textblob import TextBlob
from symspellpy import SymSpell
#import bcrypt  # Import bcrypt for password hashing

# Database connection details (replace with your own)
DATABASE_HOST = "localhost"
DATABASE_PORT = 3306
DATABASE_USER = "root"
DATABASE_PASSWORD = "admin"
DATABASE_NAME = "prowc"

# Flask app initialization
app = Flask(__name__)

# Configure secret key for session management (replace with a random string)
    # app.config['SECRET_KEY'] = 'shshshs dddd'
# Function to connect to MySQL database
def get_db_connection():
    return mysql.connector.connect(
        host=DATABASE_HOST,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        database=DATABASE_NAME
    )

# Create the Signup table if it doesn't exist
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


# Route for registration form display
@app.route('/register', methods=[ 'POST' ,'GET'])
def register():
    msg = ' '
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
             msg = 'Invalid email address!'
        if not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        # Hash password using a secure hashing algorithm (e.g., bcrypt)
         #hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


        conn = get_db_connection()
        cur = conn.cursor()

        # Check for existing username or email before inserting
    
        cur.execute("SELECT * FROM Signup WHERE username = %s OR email = %s ;", (username, email))
        existing_user = cur.fetchone()
        if existing_user:
            error_message = "Username or email already exists."
            return render_template('register.html', error=error_message)

        try:
            cur.execute("INSERT INTO Signup (username, email, password_hash) VALUES (%s, %s, %s) ;", (username, email, password))
            conn.commit()
            return  render_template('login.html')
  # Redirect to login page after successful registration
        except Exception as e:
            error_message = f"Registration failed: {e}"
            return render_template('register.html', error=error_message)
        finally:
            cur.close()
            conn.close()

    return render_template('register.html', error_message = msg)


# Secure password hashing function using bcrypt
#def hash_password(password):
    # Generate a random salt for each password
    #salt = bcrypt.gensalt()
    # Hash the password with the salt
    #hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    ##def verify_password(password, hashed_password):
    # Compare the password with the stored hash using the same salt
   # return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))



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

        # Validate password hash using a secure password comparison method
       # if not verify_password(password, user[3]):  # Implement secure password verification
            #error_message = "Invalid username or password."
           # return render_template('login.html', error=error_message)

        # Successful login (implementation details omitted for brevity)
        # ...

        return redirect(url_for('home'))  # Redirect to protected content after successful login
        # (assuming you have a 'home' or protected content route)

    return render_template('login.html')

# (Optional) Route for protected content accessible only after login
# (Implementation details omitted for brevity)
# Initialize SymSpell

sym_spell = SymSpell(max_dictionary_edit_distance=2)
dictionary_path = "frequency_dictionary_en_82_765.txt"

# Load dictionary and check if it's working
if not sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1):
    print("Error: Dictionary file not found or failed to load.")

def spell_check(text):
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
"""
@app.route('/spellchecker', methods=['POST', 'GET'])
def spellchecker():
    if request.method == 'POST':
        fieldvalues = request.form['fieldvalues']
        url = "https://jspell-checker.p.rapidapi.com/check"
        payload = {
            "language":"enUS",
            "fieldvalues":fieldvalues,
            "config": {
                "forceUpperCase": False,
                "ignoreIrregularCaps": False,
                "ignoreFirstCaps": True,
                "ignoreNumbers": True,
                "ignoreUpper": False,
                "ignoreDouble": False,
                "ignoreWordsWithNumbers": True,
            }
        }
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key":"ad8dd9e205msh1b46ee7d2f5246fp145c0bjsn4f9d4d717193",
            "X-RapidAPI-Host": "jspell-checker.p.rapidapi.com"
        }
        response = requests.request("POST", url, json=payload, headers=headers)
        response_dict = response.json()
       
        spelling_error_count = response_dict['spellingErrorCount'] 

        if spelling_error_count == 0:
                return render_template("spellchecker.html",fieldvalues=fieldvalues,speLling_error_count=spelling_error_count,response_dict = "no error")
        else:
            elements = response_dict['elements' ]
            error_list = []
            for element in elements:
                error = element['errors'][0]
                word = error['word']
                position = error['position' ]
                suggestions = error[ 'suggestions']
                error_list.append((word, position, suggestions) )

        return render_template("spellchecker.html", response_dict=response_dict,fieldvalues = fieldvalues)
    else:
        return render_template("spellchecker.html")
        
@app.route('/grammarcheck', methods=['POST','GET'])
def grammarCheck():
    if request.method == 'POST':
        text = request.form['text']
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        if sentiment==0.0:
            sentiment='15.020'
        else:
            sentiment
        noun_phrases = blob.noun_phrases
        text_noun_phrases = "\n".join(noun_phrases)
        return render_template('grammarcheck.html', sentiment=sentiment,noun_phrases=noun_phrases)
    return render_template('grammarcheck.html')
"""

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
                corrected_text = corrected_text.replace(incorrect_word, suggestions[0], 1)

            errors.append({
                "message": match["message"],
                "word": incorrect_word,
                "suggestions": suggestions
            })

        return render_template("grammarcheck.html", original_text=text, corrected_text=corrected_text, errors=errors)

    return render_template("grammarcheck.html")
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer



@app.route('/summarize', methods=['POST', 'GET'])
def summarize():
    if request.method == 'POST':
        text = request.form['text']
        num_sentences = int(request.form['num_sentences'])

        # Using Sumy for summarization
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, num_sentences)

        summarized_text = " ".join(str(sentence) for sentence in summary)

        return render_template("summarize.html", summary=summarized_text, original_text=text)

    return render_template("summarize.html", summary="", original_text="")
@app.route('/home')
def home():
    # ...

    return render_template('home.html')

if __name__ == "__main__":
    app.run(debug=True, port=5000)
