from flask import Flask,render_template,g,request,session,redirect,url_for
from database import get_db,init_db
from werkzeug.security import generate_password_hash,check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'postgres_db_con'):
        g.postgres_db_con.close()
    if hasattr(g,'postgres_db_cur'):
        g.postgres_db_cur.close()

@app.before_first_request
def create_tables():
    init_db()

def get_current_user():
    user_result = None
    if 'username' in session:
        user = session['username']
        db = get_db()
        db.execute('select id,name,password,expert,admin from users where name = %s',(user,))
        user_result = db.fetchone()
    return user_result

@app.route('/')
def index():
    user_details = get_current_user()
    db = get_db()
    db.execute('''
                                select questions.id as id,questions.question_text as question,
                                askers.name as asked_by,experts.name as expert 
                                from questions,users as askers,
                                users as experts 
                                where questions.asked_by_id = askers.id
                                and questions.expert_id = experts.id
                                and questions.answer_text is not null
                                ''')
    results = db.fetchall()
    return render_template('home.html',user=user_details,results=results)

@app.route('/register',methods=["GET","POST"])
def register():
    user_details = get_current_user()
    db = get_db()
    error_message = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        existing_user_cur = db.execute('select count(*) as count from users where name = ?',[username])
        no = existing_user_cur.fetchone()
        if no == 0:
            hashed_password = generate_password_hash(password,method='sha256')
            db.execute('insert into users(name,password,expert,admin) values(?,?,?,?)',[username,hashed_password,'0','0'])
            db.commit()
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error_message = "User already exists!"

    return render_template('register.html',user=user_details,error=error_message)

@app.route('/login',methods=["GET","POST"])
def login():
    user_details = get_current_user()
    user_error_message = None
    pass_error_message = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password,method='sha256')
        db = get_db()
        c = db.execute('select id,name,password from users where name = ?',[username])
        user_result = c.fetchone()
        if user_result:
            returned_password = user_result['password']
            if check_password_hash(returned_password,password):
                session['username'] = user_result['name']
                return redirect(url_for('index'))
            else:
                pass_error_message = "Passwords don't match"
        else:
            user_error_message = "User does not exist!"

    return render_template('login.html',user=user_details,user_error=user_error_message,pass_error=pass_error_message)

@app.route('/question/<question_id>')
def question(question_id):
    user_details = get_current_user()
    db = get_db()
    question_details_cur = db.execute('''
                                        select questions.question_text as question,
                                        questions.answer_text as answer,
                                        askers.name as asked_by,experts.name as expert
                                        from questions,users as askers,users as experts
                                        where questions.asked_by_id = askers.id 
                                        and questions.expert_id = experts.id 
                                        and questions.id = ?''',[question_id])
    details = question_details_cur.fetchall()
    return render_template('question.html',user=user_details,details=details)

@app.route('/answer/<question_id>',methods=["GET","POST"])
def answer(question_id):
    user_details = get_current_user()
    db = get_db()
    if request.method == "POST":
        answer = request.form['answer']
        db.execute('update questions set answer_text = ? where id =?',[answer,question_id])
        db.commit()
        return redirect(url_for('unanswered'))

    if user_details:
        if user_details['expert'] == 1:
            question_cur = db.execute('select id,question_text from questions where id = ?',[question_id])
            question = question_cur.fetchone()
            return render_template('answer.html',user=user_details,question=question)
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/ask',methods=["GET","POST"])
def ask():
    db = get_db()
    user_details = get_current_user()
    if request.method == "POST":
        question = request.form['question']
        expert_id = request.form['expert']
        ask_by_id = user_details['id']
        db.execute('insert into questions(question_text,asked_by_id,expert_id) values(?,?,?)',[question,ask_by_id,expert_id])
        db.commit()
        return redirect(url_for('index'))

    if user_details:
        expert_cur = db.execute('select id,name from users where expert = 1 and admin = 0')
        experts = expert_cur.fetchall()
        return render_template('ask.html',user=user_details,experts=experts)
    else:
        return redirect(url_for('login'))

@app.route('/unanswered')
def unanswered():
    user_details = get_current_user()
    if user_details:
        if user_details['expert'] == 1:
            db = get_db()
            unanswered_cur = db.execute('''
                                            select questions.id,questions.question_text,users.name from questions , users
                                             where questions.expert_id = ? 
                                             and questions.asked_by_id = users.id
                                             and questions.answer_text is NULL ''',[user_details['id']])
            unanswered_questions = unanswered_cur.fetchall()
            return render_template('unanswered.html',user=user_details,questions=unanswered_questions)
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/users')
def users():
    user_details = get_current_user()
    if user_details:
        if user_details['admin'] == 1:
            db = get_db()
            user_cur = db.execute('select id,name,expert,admin from users where admin != 1')
            users = user_cur.fetchall()
            return render_template('users.html',user=user_details,users=users)
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/promote/<user_id>')
def promote(user_id):
    user_details = get_current_user()
    if user_details:
        if user_details['admin'] == 1:
            db = get_db()
            db.execute('update users set expert = case when expert = 1 then 0 else 1 end where id = ?',[user_id])
            db.commit()
            return redirect(url_for('users'))
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username',None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
