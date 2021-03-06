import redis
from porm.model import Model, ModelException
from porm.validators import StringValidator, LengthValidator, RegexValidator, ValidatorException, EmailValidator, EqualToValidator, NumberRangeValidator, IPAddressValidator
from porm.fields import StringField, NumberField, FieldException
from unittest import TestCase
from StringIO import StringIO
import sys
import pytest

class TestORM(TestCase):

    def test_basic_saving(self):
        class User(Model):
            name = StringField(index=True)
            surname = StringField()

        user = User()
        user.name = 'Peter'
        user.surname = 'Pan'
        user.save()

        connection = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
        assert connection.hget('User:Peter', 'surname') == 'Pan'

    def test_basic_validation(self):
        class User(Model):
            name = StringField(
                               index=True,
                               validators= [
                                            StringValidator(),
                                            LengthValidator(min_length=0, max_length=20),
                                            RegexValidator('^A')
                                            ])
            surname = StringField()

        with pytest.raises(ValidatorException):
            user = User()
            user.name = 'Peter2'
            user.surname = 'Pan2'

    def test_lenght_validation(self):
        class User(Model):
            name = StringField(
                               index=True,
                               validators= [
                                            StringValidator(),
                                            LengthValidator(min_length=0, max_length=20),
                                            ])
            surname = StringField()

        user = User()
        user.name = 'Peter2'
        user.surname = 'Pan2'
        with pytest.raises(ValidatorException):
            user.name = 'Peter2Peter2Peter2Peter2Peter2Peter2'

    def test_range_validation(self):
        class User(Model):
            name = StringField(index=True)
            age = NumberField(validators=[NumberRangeValidator(min=0, max=10)])

        user = User()
        user.name = 'Peter2'
        user.age = 5
        with pytest.raises(ValidatorException):
            user.age = 11

    def test_email_validation(self):
        class User(Model):
            name = StringField(
                               index=True,
                               validators= [
                                            LengthValidator(min_length=0, max_length=20),
                                            RegexValidator('^A')
                                            ])
            surname = StringField()
            email = StringField(
                                validators= [
                                            EmailValidator()
                                ])

        with pytest.raises(ValidatorException):
            user = User()
            user.name = 'Peter2'
            user.surname = 'Pan2'
            user.email = 'test|test.com'

    def test_equalto_validation(self):
        class User(Model):
            name = StringField(
                               index=True,
                               validators= [
                                            LengthValidator(min_length=0, max_length=20),
                                            EqualToValidator('Peter2')
                                            ])
            surname = StringField()

        user = User()
        user.name = 'Peter2'
        user.surname = 'Pan2'
        with pytest.raises(ValidatorException):
            user.name = 'Peter3'

    def test_prefix(self):
        class User(Model):
            name = StringField(index=True)
            age = NumberField()

        user = User(prefix='my_partition')
        user.name = 'Peter4'
        user.age = 15
        user.save()

        assert user.exists() == True
        connection = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
        assert connection.hget('my_partition:User:Peter4', 'age') == str(15)

    def test_exists_key(self):
        class User(Model):
            name = StringField(
                               index=True,
                               validators= [
                                            LengthValidator(min_length=0, max_length=20)
                                            ])
            surname = StringField()

        user = User()
        user.name = 'Peter2'
        user.surname = 'Pan2'
        user.save()

        assert user.exists() == True

    def test_free_key(self):
        class User(Model):
            name = StringField(
                               index=True,
                               validators= [
                                            LengthValidator(min_length=0, max_length=20)
                                            ])
            surname = StringField()

        user = User()
        user.name = 'Peter3'
        user.surname = 'Pan3'
        user.save()
        assert user.exists() == True
        user.free()
        assert user.exists() == False

    def test_ip_validation(self):
        class User(Model):
            name = StringField(
                               index=True,
                               validators= [
                                            LengthValidator(min_length=0, max_length=20),
                                            EqualToValidator('Peter2')
                                            ])
            ip = StringField(validators =[
                                            StringValidator(),
                                            IPAddressValidator()
                                        ])

        user = User()
        user.name = 'Peter2'
        user.ip = '127.0.0.1'
        with pytest.raises(ValidatorException):
            user.ip = '1234.456.12.12'

    def test_finding(self):
        class User(Model):
            name = StringField(index=True)
            surname = StringField()

        user = User()
        user.name = 'Peter7'
        user.surname = 'Pan'
        user.save()

        found_user = User.find('Peter7')
        assert found_user.surname.get() == 'Pan'

    def test_finding_with_numeric_parameter(self):
        class User(Model):
            name = StringField(index=True)
            surname = StringField()
            age = NumberField()

        user = User()
        user.name = 'Peter8'
        user.surname = 'Pan'
        user.age = 15
        user.save()

        found_user = User.find('Peter8')
        assert found_user.age.get() == 15

    def test_non_finding(self):
        class User(Model):
            name = StringField(index=True)
            surname = StringField()

        found_user = User.find('NonExist')
        assert found_user.surname.get() == found_user.name.get() == None

    def test_str_output(self):
        class User(Model):
            name = StringField(index=True)
            surname = StringField()
            age = NumberField()

        user = User()
        user.name = 'Peter'
        user.surname = 'Pan'
        user.age = 15
        stdout = sys.stdout
        sys.stdout = reportSIO = StringIO()

        print user
        out = reportSIO.getvalue()
        sys.stdout = stdout
        assert out == "{'age': 15, 'surname': 'Pan', 'name': 'Peter'}\n"

    def test_extra_data_from_db(self):
        class User(Model):
            name = StringField(index=True)
            surname = StringField()
            typo_in_age = NumberField()

        with pytest.raises(ModelException):
            User.find('Peter')

    def test_default_value(self):
        class User(Model):
            name = StringField(index=True)
            surname = StringField()
            age = NumberField()
            address = StringField(default='default value')

        user = User()
        user.name = 'Peter'
        user.surname = 'Pan'
        user.age = 15

        assert user.address.get() == 'default value'

    def test_default_value_from_db(self):
        class User(Model):
            name = StringField(index=True)
            surname = StringField()
            age = NumberField()
            address = StringField(default='default value')

        user = User()
        user.name = 'Peter9'
        user.surname = 'Pan'
        user.age = 15
        user.save()
        assert user.address.get() == 'default value'
        found_user = User.find('Peter9')
        assert found_user.address.get() == 'default value' == user.address.get()

    def test_default_value_in_index(self):
        with pytest.raises(FieldException):
            class User(Model):
                name = StringField(index=True, default='a default value')
            user = User()
            user.name = 'Peter'
