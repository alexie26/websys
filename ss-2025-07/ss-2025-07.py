"""Webbasierte Systeme - Gruppe 07
"""
# Import benötigter Flask-Module
from flask import Flask, render_template, request, g, redirect, url_for, session, flash
from functools import wraps
#functionen verpacket um eigenschaften nicht zu verlieren


# Import MySQL-Connector
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

# Import der Verbindungsinformationen zur Datenbank:
# Variable DB_HOST: Servername des MySQL-Servers
# Variable DB_USER: Nutzername
# Variable DB_PASSWORD: Passwort
# Variable DB_DATABASE: Datenbankname
from db.db_credentials import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE

app = Flask(__name__)
app.secret_key = "pjfjojefjiejifjiewohfihrieugffuifhoihi"


@app.before_request
def before_request():
    """ Verbindung zur Datenbank herstellen """
    g.con = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
                                    database=DB_DATABASE)


@app.teardown_request
def teardown_request(exception):
    """ Verbindung zur Datenbank trennen """
    con = getattr(g, 'con', None)
    if con is not None:
        con.close()


@app.route('/')
def startseite():
    """Startseite"""
    return render_template('index.html')



@app.route('/asidiropou')
def asidiropou_profil():
    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT * FROM asidiropou')
    daten = cursor.fetchall()
    print(daten)
    cursor.close()
    return render_template('asidiropou.html', daten=daten)


@app.route('/Bsaifo')
def bsaifo():
    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT * FROM Bsaifo')
    daten = cursor.fetchall()
    print(daten)
    cursor.close()
    return render_template('Bsaifo.html', daten=daten)


@app.route('/galkudsy')
def galkudsy():
    cursor = g.con.cursor(dictionary=True)
    cursor.execute('Select id, beschreibung From galkudsy')  # sql Befehl erwarten
    daten = cursor.fetchall()
    cursor.close()
    return render_template('galkudsy.html', daten=daten)

@app.route('/alexandra')
def alexandra():
    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT * FROM mrosu')
    data = cursor.fetchall()
    print(data)
    cursor.close()
    return render_template('alexandra.html', data=data)


# wenn du kein login hast kommst du nicht in seite
#
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('rolle') != 'Admin':
            flash('Zugriff verweigert: Nur für Admins!', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
#-------------------------LOGIN ------------------#

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bitte einloggen', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

#-------routes-----------------------------------#
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        benutzername = request.form['benutzername']
        password = request.form['password']

        cursor = g.con.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Login WHERE Benutzername = %s', (benutzername,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['Passwort'], password):  # Passwort mit dem Hash vergleichen
            session['user_id'] = user['Login_ID']
            session['benutzername'] = user['Benutzername']
            session['rolle'] = user['Rolle']
            session['nutzer_id'] = user['FK_Nutzer_ID']
            flash('Login erfolgreich!', 'success')

            if session['rolle'] == 'Admin':
                return redirect(url_for('admin_dashboard'))
            elif session['rolle'] == 'Anbieter':
                return redirect(url_for('anbieter'))
            else:
                return redirect(url_for('nutzer'))
        else:
            flash('Benutzername oder Passwort falsch', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

# Registrierung-Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Nutzerdaten aus dem Formular
        vorname = request.form['vorname']
        nachname = request.form['nachname']
        email = request.form['email']
        strasse = request.form['strasse']
        hausnummer = request.form['hausnummer']
        plz = request.form['plz']
        ort = request.form['ort']
        telefon = request.form['telefon']
        profilbild = request.form.get('profilbild',
                                      '')  # Sicherstellen, dass ein leerer String gesetzt wird, wenn kein Profilbild angegeben ist

        # Logindaten aus dem Formular
        benutzername = request.form['benutzername']
        password = request.form['password']
        rolle = request.form.get('rolle')  # Standardwert 'Nutzer', wenn nichts angegeben
        print(rolle)
        cursor = g.con.cursor()
#hallo
        try:
            cursor.execute("""
                INSERT INTO Nutzer (Vorname, Nachname, EMail, Strasse, Hausnummer, PLZ, ORT, ProfilBild, Telefon)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (vorname, nachname, email, strasse, hausnummer, plz, ort, profilbild, telefon))
            g.con.commit()
            print("Nutzer angelegt")
            nutzer_id = cursor.lastrowid  # ID des neuen Nutzers
            hashed_password = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO Login (Benutzername, Passwort, Rolle, FK_Nutzer_ID)
                VALUES (%s, %s, %s, %s)
            """, (benutzername, hashed_password, rolle, nutzer_id))
            g.con.commit()
            print("Login angelegt")

            flash("Registrierung erfolgreich!", "success")
            return redirect(url_for('login'))

        except mysql.connector.IntegrityError:
            flash("Benutzername oder E-Mail existiert bereits", "danger")
            return redirect(url_for('register'))

        finally:
            cursor.close()

    return render_template("register.html")

@app.route('/logout')
def logout():
    session.clear()
    flash('Sie wurden erfolgreich ausgeloggt', "info")

    return redirect(url_for('index'))


@app.route('/admin')
@admin_required
def admin_dashboard():
    cursor = g.con.cursor(dictionary=True)
    cursor.execute("""
        SELECT l.Login_ID, l.Benutzername, l.Rolle, 
               n.Vorname, n.Nachname, n.Email 
        FROM Login l 
        JOIN Nutzer n ON l.FK_Nutzer_ID = n.Nutzer_ID
    """)
    benutzerliste = cursor.fetchall()
    cursor.close()

    return render_template('admin.html', benutzerliste=benutzerliste)


# ---------- BENUTZER BEARBEITEN ----------------
@app.route('/admin/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    cursor = g.con.cursor(dictionary=True)
    if request.method == 'POST':
        rolle = request.form['rolle']
        cursor.execute("UPDATE Login SET Rolle = %s WHERE Login_ID = %s", (rolle, user_id))
        g.con.commit()
        flash("Benutzer aktualisiert", "success")
        return redirect(url_for('admin_dashboard'))

    cursor.execute("SELECT * FROM Login WHERE Login_ID = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return render_template('edit_user.html', user=user)

# ---------- BENUTZER LÖSCHEN -------------------
@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    cursor = g.con.cursor()
    cursor.execute("DELETE FROM Login WHERE Login_ID = %s", (user_id,))
    g.con.commit()
    cursor.close()
    flash("Benutzer gelöscht", "info")
    return redirect(url_for('admin_dashboard'))

# ---------- FOTOGALERIE ------------------------
@app.route('/admin/fotos')
@admin_required
def fotos_list():
    cursor = g.con.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Fotos")
    fotos = cursor.fetchall()
    cursor.close()
    return render_template('fotos_list.html', fotos=fotos)

@app.route('/admin/fotos/neu', methods=['GET', 'POST'])
@admin_required
def foto_neu():
    if request.method == 'POST':
        titel = request.form['titel']
        beschreibung = request.form['beschreibung']
        bild_url = request.form['bild_url']
        cursor = g.con.cursor()
        cursor.execute("INSERT INTO Fotos (Titel, Beschreibung, Bild_URL) VALUES (%s, %s, %s)",
                       (titel, beschreibung, bild_url))
        g.con.commit()
        cursor.close()
        flash("Foto hinzugefügt", "success")
        return redirect(url_for('fotos_list'))
    return render_template('foto_form.html')

# Start der Flask-Anwendung
if __name__ == '__main__':
    app.run(debug=True)
