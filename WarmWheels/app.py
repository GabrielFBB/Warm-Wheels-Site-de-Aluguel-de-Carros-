from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

from models import db, User, Vehicle, Reservation, PaymentMethod
from forms import RegistrationForm, LoginForm, SearchForm, ReservationForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mude-para-uma-chave-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_first_request
def setup_db():
    db.create_all()
    if not PaymentMethod.query.first():
        for name in ['Cartão', 'MB Way', 'Transferência']:
            db.session.add(PaymentMethod(name=name))
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('vehicle_list'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data,
                    email=form.email.data,
                    password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Conta criada com sucesso!', 'success')
        return redirect(url_for('vehicle_list'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('vehicle_list'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Login efetuado!', 'success')
            return redirect(url_for('vehicle_list'))
        flash('Credenciais inválidas.', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/veiculos')
def vehicle_list():
    form = SearchForm(request.args)
    today = datetime.utcnow().date()
    qs = Vehicle.query.filter(
        Vehicle.available == True,
        Vehicle.last_legalization >= today - timedelta(days=365),
        Vehicle.next_review >= today
    )
    if form.validate():
        if form.q.data:
            kw = f"%{form.q.data}%"
            qs = qs.filter(
                Vehicle.brand.ilike(kw) | Vehicle.model.ilike(kw)
            )
        if form.category.data:
            qs = qs.filter_by(category=form.category.data)
        if form.type.data:
            qs = qs.filter_by(type=form.type.data)
        if form.capacity_min.data:
            qs = qs.filter(Vehicle.capacity >= form.capacity_min.data)
        if form.value_max.data:
            qs = qs.filter(Vehicle.daily_rate <= float(form.value_max.data))
    vehicles = qs.order_by(Vehicle.daily_rate).all()
    return render_template('vehicle_list.html', form=form, vehicles=vehicles)

@app.route('/reservar/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def reservation_create(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    today = datetime.utcnow().date()
    if not vehicle.available:
        flash('Veículo não disponível.', 'error')
        return redirect(url_for('vehicle_list'))
    if vehicle.last_legalization < today - timedelta(days=365) or vehicle.next_review < today:
        flash('Veículo indisponível por legalização/revisão.', 'error')
        return redirect(url_for('vehicle_list'))

    form = ReservationForm()
    form.payment_method.choices = [
        (pm.id, pm.name) for pm in PaymentMethod.query.all()
    ]
    if form.validate_on_submit():
        d1 = form.start_date.data
        d2 = form.end_date.data
        if d2 <= d1:
            flash('Data de fim deve ser posterior à data de início.', 'error')
        else:
            days = (d2 - d1).days
            total = days * vehicle.daily_rate
            res = Reservation(
                user_id=current_user.id,
                vehicle_id=vehicle.id,
                start_date=d1,
                end_date=d2,
                total_value=total,
                payment_method_id=form.payment_method.data
            )
            vehicle.available = False
            db.session.add(res)
            db.session.commit()
            flash('Reserva concluída!', 'success')
            return redirect(url_for('my_reservations'))
    return render_template('reservation_create.html', vehicle=vehicle, form=form)

@app.route('/minhas-reservas')
@login_required
def my_reservations():
    res_list = Reservation.query.filter_by(user_id=current_user.id)\
                               .order_by(Reservation.created_at.desc()).all()
    return render_template('my_reservations.html', reservations=res_list)

@app.route('/reservas/<int:res_id>/editar', methods=['GET', 'POST'])
@login_required
def reservation_edit(res_id):
    res = Reservation.query.get_or_404(res_id)
    if res.user_id != current_user.id:
        return redirect(url_for('my_reservations'))
    form = ReservationForm(obj=res)
    form.payment_method.choices = [(res.payment_method_id, res.payment_method.name)]
    if form.validate_on_submit():
        d1 = form.start_date.data
        d2 = form.end_date.data
        if d2 <= d1:
            flash('Data de fim deve ser posterior à data de início.', 'error')
        else:
            days = (d2 - d1).days
            res.start_date  = d1
            res.end_date    = d2
            res.total_value = days * res.vehicle.daily_rate
            db.session.commit()
            flash('Reserva atualizada!', 'success')
            return redirect(url_for('my_reservations'))
    return render_template('reservation_edit.html', reservation=res, form=form)

@app.route('/reservas/<int:res_id>/cancelar', methods=['POST'])
@login_required
def reservation_cancel(res_id):
    res = Reservation.query.get_or_404(res_id)
    if res.user_id == current_user.id:
        vehicle = res.vehicle
        db.session.delete(res)
        vehicle.available = True
        db.session.commit()
        flash('Reserva cancelada.', 'success')
    return redirect(url_for('my_reservations'))

if __name__ == '__main__':
    app.run(debug=True)
