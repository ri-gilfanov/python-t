from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.contrib.auth.models import PermissionsMixin
from django.forms import TextInput
from django.core.validators import DecimalValidator, MaxValueValidator, MinValueValidator
from mail_templated import send_mail


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone, password, **extra_fields):
        if not phone:
            raise ValueError('Номер телефона должен быть указан')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя"""

    # общая информация
    last_name = models.CharField('фамилия', max_length=30, blank=True)
    first_name = models.CharField('имя', max_length=30)
    patronymic = models.CharField('отчество', max_length=30, blank=True)
    birth_date = models.DateField('дата рождения', blank=True, null=True)
    phone = models.DecimalField(
        'номер телефона',
        max_digits=10,
        decimal_places=0,
        unique=True,
        validators=[MaxValueValidator(9999999999), MinValueValidator(1000000000)],
        error_messages={
            'min_value': 'Номер телефона указывается без восьмёрки, должен содержать 10 цифр и не должен начинаться с 0',
            'unique': 'Пользователь с таким номера телефона уже существует',
        },
    )
    email = models.EmailField('электронная почта', blank=True)
    default_delivery = models.TextField('адрес доставки по-умолчанию', max_length=256, blank=True)
    date_joined = models.DateTimeField('дата регистрации', default=timezone.now)

    # данные клиента
    wholesale_buyer_request = models.BooleanField('заявка оптовика', default=False)
    buyer_type = models.ForeignKey('shop.BuyerType', models.CASCADE, blank=True, null=True,
                                   verbose_name='тип клиента')
    seller = models.ForeignKey('self', models.CASCADE, blank=True, null=True,
                               verbose_name='менеджер клиента', related_name='buyer_set')

    # права доступа
    is_staff = models.BooleanField(
        'статус персонала',
        default=False,
        help_text='Отметьте, если пользователь может входить в административную часть сайта.',
    )
    is_seller = models.BooleanField(
        'менеджер по продажам',
        default=False,
        help_text='Отметьте, чтобы пользователь мог взаимодействовать только со своими клиентами.',
    )
    is_active = models.BooleanField(
        'активный',
        default=True,
        help_text='Отметьте, если пользователь должен считаться активным. Уберите эту отметку вместо удаления учётной записи.',
    )



    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self):
        string = ''
        if self.last_name and self.first_name and self.patronymic:
            string = '%s %s.%s.' % (self.last_name, self.first_name[0], self.patronymic[0])
        elif self.last_name and self.first_name:
            string = '%s %s.' % (self.last_name, self.first_name[0])
        elif self.first_name and self.patronymic:
            string = '%s.%s.' % (self.first_name[0], self.patronymic[0])
        return string if string else str(self.phone)

    def get_full_name(self):
        full_name_list = [s for s in (self.last_name, self.first_name, self.patronymic) if s]
        full_name = ' '.join(full_name_list)
        return full_name if full_name else str(self.phone)

    def get_short_name(self):
        short_name_list = [s for s in (self.first_name, self.patronymic) if s]
        short_name = ' '.join(short_name_list)
        return short_name if short_name else str(self.phone)

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)


    def save(self, *args, **kwargs):
        post_obj = self
        if post_obj.__class__.objects.filter(id=post_obj.id).exists():
            pre_obj = post_obj.__class__.objects.get(id=post_obj.id)
            # автоснятие заявки оптовика при установке типа покупателя
            if pre_obj.wholesale_buyer_request == True and post_obj.buyer_type != None:
                post_obj.wholesale_buyer_request = False
        if post_obj.wholesale_buyer_request == True:
            context = {'buyer': self}
            from_email = 'piton-t@piton-t.ru'
            recipient_list = []
            for email in ['ri.gilfanov@yandex.ru']:
                if email:
                    recipient_list.append(email)
            send_mail('users/new_wholesale_buyer_email.html', context, from_email, recipient_list=recipient_list)
        super(User, self).save(*args, **kwargs)
