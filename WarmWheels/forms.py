from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
    IntegerField,
    DecimalField,
    DateField
)
from wtforms.validators import (
    DataRequired,
    Length,
    EqualTo,
    NumberRange,
    Optional
)

class RegistrationForm(FlaskForm):
    username         = StringField(
        'Username',
        validators=[DataRequired(), Length(3, 80)]
    )
    email            = StringField(
        'Email',
        validators=[DataRequired(), Length(6, 120)]
    )
    password         = PasswordField(
        'Password',
        validators=[DataRequired(), Length(6, 128)]
    )
    confirm_password = PasswordField(
        'Confirmar Password',
        validators=[DataRequired(), EqualTo('password')]
    )
    client_category  = SelectField(
        'Categoria de Cliente',
        choices=[
            ('Económico', 'Económico (até 50€/dia)'),
            ('Silver', 'Silver (até 250€/dia)'),
            ('Gold', 'Gold (até 600€/dia)'),
        ],
        validators=[DataRequired()]
    )
    max_budget       = DecimalField(
        'Orçamento Máximo (€)',
        places=2,
        validators=[DataRequired(), NumberRange(min=0, max=1000)]
    )
    submit           = SubmitField('Registar')


class LoginForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired()]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    submit   = SubmitField('Entrar')


class SearchForm(FlaskForm):
    q = StringField(
        'Marca/Modelo',
        validators=[Optional(), Length(max=50)]
    )
    category = SelectField(
        'Categoria',
        choices=[
            ('', 'Todas as categorias'),
            ('economico', 'Económico'),
            ('intermedio', 'Intermédio'),
            ('luxo', 'Luxo'),
            ('suv', 'SUV'),
        ],
        validators=[Optional()]
    )
    type = SelectField(
        'Tipo',
        choices=[
            ('', 'Todos os tipos'),
            ('carro', 'Carro'),
            ('moto', 'Moto'),
        ],
        validators=[Optional()]
    )
    capacity_min = IntegerField(
        'Capacidade mín.',
        validators=[Optional(), NumberRange(min=1)]
    )
    value_max = DecimalField(
        'Diária máx.',
        places=2,
        validators=[Optional(), NumberRange(min=0)]
    )
    submit = SubmitField('Filtrar')


class ReservationForm(FlaskForm):
    start_date     = DateField(
        'Data início',
        validators=[DataRequired()]
    )
    end_date       = DateField(
        'Data fim',
        validators=[DataRequired()]
    )
    payment_method = SelectField(
        'Forma de pagamento',
        coerce=int,
        validators=[DataRequired()]
    )
    submit         = SubmitField('Concluir reserva')


class PaymentForm(FlaskForm):
    card_number    = StringField(
        'Número do Cartão',
        validators=[DataRequired(), Length(16, 19)]
    )
    expiry_date    = StringField(
        'Data de Expiração (MM/YY)',
        validators=[DataRequired()]
    )
    cvv            = StringField(
        'CVV',
        validators=[DataRequired(), Length(3, 4)]
    )
    cardholder_name = StringField(
        'Nome do Portador',
        validators=[DataRequired()]
    )
    submit         = SubmitField('Processar Pagamento')


class ContractForm(FlaskForm):
    pickup_date    = DateField(
        'Data de Recolha',
        validators=[DataRequired()]
    )
    pickup_time    = SelectField(
        'Hora de Recolha',
        choices=[
            ('09:00', '09:00'),
            ('10:00', '10:00'),
            ('11:00', '11:00'),
            ('12:00', '12:00'),
            ('14:00', '14:00'),
            ('15:00', '15:00'),
            ('16:00', '16:00'),
            ('17:00', '17:00'),
        ],
        validators=[DataRequired()]
    )
    terms_accepted = SelectField(
        'Aceito os Termos e Condições',
        choices=[('yes', 'Sim, aceito os termos')],
        validators=[DataRequired()]
    )
    submit         = SubmitField('Finalizar Contrato')


class CategoryForm(FlaskForm):
    client_category = SelectField(
        'Categoria de Cliente',
        choices=[
            ('Económico', '🥉 Económico (até 50€/dia)'),
            ('Silver', '🥈 Silver (até 250€/dia)'),
            ('Gold', '🥇 Gold (até 600€/dia)'),
        ],
        validators=[DataRequired()]
    )
    max_budget     = DecimalField(
        'Orçamento Máximo (€)',
        places=2,
        validators=[DataRequired(), NumberRange(min=0, max=1000)]
    )
    submit         = SubmitField('Atualizar Categoria')
