from peewee import *
import os.path

# define database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.db")
conn = SqliteDatabase(db_path)
cursor = conn.cursor()
conn.close()

# define parent class
class BaseModel(Model):
    class Meta:
        database = conn 

# class for last user's info
class CustomPath(BaseModel):
    id = AutoField(column_name='id')
    user_id = IntegerField(column_name='user_id')
    price = IntegerField(column_name='price')
    answer = TextField(column_name='answer')

    class Meta:
        table_name = 'custom_path'

# class with user's questions
class Questions(BaseModel):
    id = AutoField(column_name='id')
    q_id = IntegerField(column_name='q_id')
    user_id = IntegerField(column_name='user_id')
    price = IntegerField(column_name='price')
    question = TextField(column_name='question')
    answer = TextField(column_name='answer')
    category = TextField(column_name='category')

    class Meta:
        table_name = 'questions'

# class with user's score
class UserScore(BaseModel):
    id = AutoField(column_name='id')
    user_id = IntegerField(column_name='user_id')
    score = IntegerField(column_name='score')

    class Meta:
        table_name = 'user_score'

# function for getting last user's info
def get_last_info(CustomPath, user_id):
    return CustomPath.get(CustomPath.user_id==user_id)

# function for updateting last user's info
def update_last_info(CustomPath, user_id, answer, price):
    if CustomPath.get_or_none(CustomPath.user_id == user_id) is None:
        CustomPath.create(user_id=user_id, price=price, answer=answer)
    else:
        id = CustomPath.get(CustomPath.user_id==user_id).id
        CustomPath.set_by_id(id, {'price': price, 'answer': answer})

# uinction for updating user score
def update_user_score(UserScore, user_id, price):
    if UserScore.get_or_none(UserScore.user_id == user_id) is None:
        UserScore.create(user_id=user_id, score=price)
    else:
        id = UserScore.get(UserScore.user_id==user_id).id
        score = UserScore.get(UserScore.user_id==user_id).score + price
        UserScore.set_by_id(id, {'score': score})

# function for deleting user's questions
def delete_old_questions(Questions, user_id):
    if Questions.get_or_none(Questions.user_id == user_id) is not None:
        query = Questions.delete().where(Questions.user_id == user_id)
        query.execute()
