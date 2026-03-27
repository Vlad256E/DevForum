class ReputationStrategy:
    def apply(self, user, points):
        user.reputation += points
        user.save()

class RewardAction(ReputationStrategy): # Поощрение (Лайк/Полезный ответ)
    def execute(self, user, action_type):
        points = 5 if action_type == 'like' else 15
        self.apply(user, points)

class PenaltyAction(ReputationStrategy): # Наказание (Удаление спама)
    def execute(self, user):
        self.apply(user, -10)