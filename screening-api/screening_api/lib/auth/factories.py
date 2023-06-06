from factory import Factory
from factory.faker import Faker
import jwt

from screening_api.lib.auth.models import User


class UserFactory(Factory):

    user_id = Faker('random_int')
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    email = Faker('safe_email')
    account_id = Faker('random_int')
    account_name = Faker('company')
    account_descendants = Faker('text')
    role = Faker('job')
    exp = Faker('future_datetime')
    iss = Faker('text')

    class Meta:
        model = User


class UserTokenFactory:

    algorithm = 'HS256'

    def __init__(self, secret_key):
        self.secret_key = secret_key

    def create(self, user):
        return jwt.encode(
            user._asdict(), self.secret_key,
            algorithm=self.algorithm,
        )
