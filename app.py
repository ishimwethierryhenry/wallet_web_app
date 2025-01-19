from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import datetime

# Initialize Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wallet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database models
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Float, default=0.0)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # "in" or "out"
    date = db.Column(db.DateTime, default=datetime.datetime.now)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    limit = db.Column(db.Float, nullable=False)

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add_account', methods=['POST'])
def add_account():
    data = request.json
    new_account = Account(name=data['name'], balance=data.get('balance', 0.0))
    db.session.add(new_account)
    db.session.commit()
    return jsonify({"message": "Account added successfully!"})

@app.route('/add_category', methods=['POST'])
def add_category():
    data = request.json
    new_category = Category(name=data['name'])
    db.session.add(new_category)
    db.session.commit()
    return jsonify({"message": "Category added successfully!"})

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    data = request.json
    account = Account.query.get(data['account_id'])
    if not account:
        return jsonify({"error": "Account not found!"}), 404

    amount = data['amount']
    if data['type'] == 'out' and account.balance < amount:
        return jsonify({"error": "Insufficient balance!"}), 400

    transaction = Transaction(
        account_id=data['account_id'],
        category_id=data.get('category_id'),
        amount=amount,
        type=data['type']
    )

    account.balance += amount if data['type'] == 'in' else -amount
    db.session.add(transaction)
    db.session.commit()
    return jsonify({"message": "Transaction added successfully!"})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"error": "Please provide start_date and end_date!"}), 400

    try:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD!"}), 400

    transactions = Transaction.query.filter(Transaction.date >= start_date, Transaction.date <= end_date).all()
    report = [
        {
            "id": t.id,
            "account_id": t.account_id,
            "category_id": t.category_id,
            "amount": t.amount,
            "type": t.type,
            "date": t.date.strftime('%Y-%m-%d %H:%M:%S')
        } for t in transactions
    ]
    return jsonify(report)

# Initialize database
if __name__ == '__main__':
    with app.app_context():  # Set up the application context
        db.create_all()  # Create all database tables
    app.run(debug=True)  # Start the Flask app

