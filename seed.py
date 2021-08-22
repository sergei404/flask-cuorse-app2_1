import json
from app import db
from app import Tutor


def seed():
    with open('teachers.json') as f:
        teachers = json.load(f)
    tutors = []
    for teacher in teachers:
        teacher_model = Tutor(
            name=teacher['name'],
            about=teacher['about'],
            rating=teacher['rating'],
            picture=teacher['picture'],
            price=teacher['price'],
            goals=json.dumps(teacher['goals']),
            free=json.dumps(teacher['free']),
        )
        tutors.append(teacher_model)

    db.session.bulk_save_objects(tutors)
    db.session.commit()


if __name__ == '__main__':
    seed()