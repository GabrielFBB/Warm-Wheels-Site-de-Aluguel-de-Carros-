import os
import random
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, redirect,
    url_for, flash, request, send_from_directory
)
from flask_login import (
    LoginManager, login_user,
    logout_user, current_user,
    login_required
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from werkzeug.utils import secure_filename

from flask.cli import with_appcontext

from forms import (
    RegistrationForm, LoginForm,
    SearchForm, ReservationForm,
    PaymentForm, ContractForm, CategoryForm
)
from models import db, User, Vehicle, Reservation, PaymentMethod, Payment

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mude-para-uma-chave-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/images')

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# -----------------------
# User loader & filters
# -----------------------

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.template_filter('dmy')
def format_ddmmyyyy(value):
    if not value:
        return ''
    return value.strftime('%d/%m/%Y')


# -----------------------
# Database setup
# -----------------------

def setup_db():
    db.create_all()

    # Métodos de pagamento
    if not PaymentMethod.query.first():
        for name in ['Cartão', 'MB Way', 'Transferência']:
            db.session.add(PaymentMethod(name=name))
        db.session.commit()

    # Veículos iniciais
    if not Vehicle.query.first():
        today = datetime.utcnow().date()

        carros = [
            ('Opel', 'Corsa', 'economico', 'carro', 5, 25.0),
            ('Volkswagen', 'Golf', 'intermedio', 'carro', 5, 35.0),
            # … seus outros carros …
        ]
        motos = [
            ('Honda', 'CG 160', '', 'moto', 2, 18.0),
            ('Yamaha', 'MT-07', '', 'moto', 2, 45.0),
            ('Suzuki', 'GSX-S750', '', 'moto', 2, 55.0),
            # … suas outras motos …
        ]

        def rand_days(a, b):
            return timedelta(days=random.randint(a, b))

        to_seed = []
        for brand, model, cat, typ, cap, rate in carros + motos:
            # regra automática para motos
            if typ == 'moto':
                if brand.lower() == 'honda' and model.lower() == 'cg 160':
                    cat = 'economico'
                else:
                    cat = 'luxo'

            fn = f"{brand.lower().replace(' ', '_')}_{model.lower().replace(' ', '_')}.jpg"
            to_seed.append(Vehicle(
                brand=brand,
                model=model,
                category=cat,
                type=typ,
                capacity=cap,
                image_url=f'images/{fn}',
                daily_rate=rate,
                updated_at=today - rand_days(0, 365),
                last_legalization=today - rand_days(0, 365),
                next_review=today + rand_days(30, 180),
                available=True
            ))

        db.session.bulk_save_objects(to_seed)
        db.session.commit()

    # Sempre corrigir categorias das motos existentes
    motos = Vehicle.query.filter_by(type='moto').all()
    for m in motos:
        if m.brand.lower() == 'honda' and m.model.lower() == 'cg 160':
            m.category = 'economico'
        else:
            m.category = 'luxo'
    if motos:
        db.session.commit()


# -----------------------
# Routes: Auth & Upload
# -----------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('vehicle_list'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            client_category=form.client_category.data,
            max_budget=float(form.max_budget.data)
        )
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


@app.route('/upload', methods=['POST'])
def upload_image():
    f = request.files.get('file')
    if f and f.filename:
        filename = secure_filename(f.filename)
        dest = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(dest)
        flash('Image has been successfully uploaded.', 'success')
    else:
        flash('Image upload failed. Please try again.', 'error')
    return redirect(url_for('my_saved_images'))


@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# -----------------------
# Routes: Vehicles & Reservations
# -----------------------

@app.route('/veiculos')
def vehicle_list():
    form = SearchForm(request.args)
    today = datetime.utcnow().date()

    # Filtrar veículos baseado na categoria do cliente
    if current_user.is_authenticated:
        # Obter veículos disponíveis para a categoria do cliente
        available_vehicles = current_user.get_available_vehicles()
        # Aplicar filtros adicionais de disponibilidade
        vehicles = [v for v in available_vehicles if (
            v.available and
            v.last_legalization >= today - timedelta(days=365) and
            v.next_review >= today
        )]
        
        # Aplicar filtros de pesquisa se fornecidos
        if form.validate():
            if form.q.data:
                kw = form.q.data.lower()
                vehicles = [v for v in vehicles if (
                    kw in v.brand.lower() or kw in v.model.lower()
                )]
            if form.category.data:
                vehicles = [v for v in vehicles if v.category == form.category.data]
            if form.type.data in {'carro', 'moto'}:
                vehicles = [v for v in vehicles if v.type == form.type.data]
            if form.capacity_min.data:
                vehicles = [v for v in vehicles if v.capacity >= form.capacity_min.data]
            if form.value_max.data:
                vehicles = [v for v in vehicles if v.daily_rate <= float(form.value_max.data)]
        
        # Ordenar por preço diário
        vehicles = sorted(vehicles, key=lambda v: v.daily_rate)
        
    else:
        # Para usuários não autenticados, mostrar apenas veículos económicos
        qs = Vehicle.query.filter(
            Vehicle.available == True,
            Vehicle.daily_rate <= 50,
            Vehicle.last_legalization >= today - timedelta(days=365),
            Vehicle.next_review >= today
        )

        if form.validate():
            if form.q.data:
                kw = f"%{form.q.data}%"
                qs = qs.filter(
                    Vehicle.brand.ilike(kw) |
                    Vehicle.model.ilike(kw)
                )
            if form.category.data:
                qs = qs.filter(Vehicle.category == form.category.data)
            if form.type.data in {'carro', 'moto'}:
                qs = qs.filter(Vehicle.type == form.type.data)
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

    if (
        not vehicle.available or
        vehicle.last_legalization < today - timedelta(days=365) or
        vehicle.next_review < today
    ):
        flash('Veículo indisponível.', 'error')
        return redirect(url_for('vehicle_list'))

    form = ReservationForm()
    form.payment_method.choices = [
        (pm.id, pm.name) for pm in PaymentMethod.query.all()
    ]

    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data

        if end_date <= start_date:
            flash('A data de fim deve ser posterior à data de início.', 'error')
        else:
            days = (end_date - start_date).days
            total = days * vehicle.daily_rate

            res = Reservation(
                user_id=current_user.id,
                vehicle_id=vehicle.id,
                start_date=start_date,
                end_date=end_date,
                total_value=total,
                payment_method_id=form.payment_method.data
            )
            vehicle.available = False
            db.session.add(res)
            db.session.commit()

            flash('Reserva realizada com sucesso!', 'success')
            return redirect(url_for('payment_process', res_id=res.id))

    return render_template(
        'reservation_create.html',
        vehicle=vehicle,
        form=form
    )


@app.route('/minhas-reservas')
@login_required
def my_reservations():
    reservas = (
        Reservation.query
        .filter_by(user_id=current_user.id)
        .order_by(Reservation.created_at.desc())
        .all()
    )
    return render_template('my_reservations.html', reservations=reservas)


@app.route('/reservas/<int:res_id>/editar', methods=['GET', 'POST'])
@login_required
def reservation_edit(res_id):
    res = Reservation.query.get_or_404(res_id)
    if res.user_id != current_user.id:
        return redirect(url_for('my_reservations'))

    form = ReservationForm(obj=res)
    form.payment_method.choices = [
        (res.payment_method_id, res.payment_method.name)
    ]

    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data

        if end_date <= start_date:
            flash('A data de fim deve ser posterior à data de início.', 'error')
        else:
            days = (end_date - start_date).days
            res.start_date = start_date
            res.end_date = end_date
            res.total_value = days * res.vehicle.daily_rate
            db.session.commit()
            flash('Reserva atualizada!', 'success')
            return redirect(url_for('my_reservations'))

    return render_template(
        'reservation_edit.html',
        reservation=res,
        form=form
    )


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
    else:
        flash('Não foi possível cancelar essa reserva.', 'error')
    return redirect(url_for('my_reservations'))


@app.route('/pagamento/<int:res_id>', methods=['GET', 'POST'])
@login_required
def payment_process(res_id):
    reservation = Reservation.query.get_or_404(res_id)
    if reservation.user_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('my_reservations'))
    
    if reservation.status != 'Pendente':
        flash('Esta reserva já foi processada.', 'error')
        return redirect(url_for('my_reservations'))
    
    form = PaymentForm()
    if form.validate_on_submit():
        # Simular processamento de pagamento
        import uuid
        transaction_id = str(uuid.uuid4())
        
        # Criar registro de pagamento
        payment = Payment(
            reservation_id=reservation.id,
            amount=reservation.total_value,
            payment_status='Pago',
            payment_date=datetime.utcnow(),
            transaction_id=transaction_id
        )
        
        # Atualizar status da reserva
        reservation.status = 'Pago'
        reservation.contract_number = f"WW{reservation.id:06d}"
        
        db.session.add(payment)
        db.session.commit()
        
        flash('Pagamento processado com sucesso!', 'success')
        return redirect(url_for('contract_finalize', res_id=reservation.id))
    
    return render_template('payment.html', form=form, reservation=reservation)


@app.route('/contrato/<int:res_id>', methods=['GET', 'POST'])
@login_required
def contract_finalize(res_id):
    reservation = Reservation.query.get_or_404(res_id)
    if reservation.user_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('my_reservations'))
    
    if reservation.status != 'Pago':
        flash('Pagamento necessário antes de finalizar contrato.', 'error')
        return redirect(url_for('my_reservations'))
    
    form = ContractForm()
    if form.validate_on_submit():
        # Combinar data e hora de recolha
        pickup_datetime = datetime.combine(
            form.pickup_date.data,
            datetime.strptime(form.pickup_time.data, '%H:%M').time()
        )
        
        # Atualizar reserva
        reservation.pickup_date = pickup_datetime
        reservation.status = 'Concluído'
        
        db.session.commit()
        
        flash('Contrato finalizado com sucesso!', 'success')
        return redirect(url_for('contract_summary', res_id=reservation.id))
    
    return render_template('contract.html', form=form, reservation=reservation)


@app.route('/resumo/<int:res_id>')
@login_required
def contract_summary(res_id):
    reservation = Reservation.query.get_or_404(res_id)
    if reservation.user_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('my_reservations'))
    
    # Calcular custos
    total_days = reservation.calculate_total_days()
    total_cost = reservation.calculate_total_cost()
    
    return render_template('contract_summary.html', 
                         reservation=reservation,
                         total_days=total_days,
                         total_cost=total_cost)


@app.route('/minha-categoria', methods=['GET', 'POST'])
@login_required
def manage_category():
    form = CategoryForm()
    
    # Carregar dados atuais do utilizador
    if request.method == 'GET':
        form.client_category.data = current_user.client_category
        form.max_budget.data = current_user.max_budget
    
    if form.validate_on_submit():
        # Atualizar categoria e orçamento do utilizador
        current_user.client_category = form.client_category.data
        current_user.max_budget = float(form.max_budget.data)
        
        db.session.commit()
        
        flash('Categoria atualizada com sucesso!', 'success')
        return redirect(url_for('vehicle_list'))
    
    return render_template('manage_category.html', form=form)


if __name__ == '__main__':
    with app.app_context():
        setup_db()
    app.run(debug=True)
