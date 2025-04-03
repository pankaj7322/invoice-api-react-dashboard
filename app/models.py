from app import db

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(255), nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"<Invoice {self.invoice_number}>"
