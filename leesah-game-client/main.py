from client_lib import quiz_rapid
from client_lib.config import HOSTED_KAFKA
import base64
import requests
import json

# LEESAH QUIZ GAME CLIENT

# 1. Change TEAM_NAME variable to your team name
# 2. make sure you have downloaded and unpacked the credential files in the certs/ dir

# Config ##########################################################################################################

TEAM_NAME = "TeamImsdal"
QUIZ_TOPIC = "quiz-rapid"
CONSUMER_GROUP_ID = f"cg-leesah-team-${TEAM_NAME}-1"
assert TEAM_NAME is not None and TEAM_NAME != "CHANGE ME", "Husk å gi teamet ditt et navn"
assert QUIZ_TOPIC is not None and QUIZ_TOPIC != "CHANGE ME", "Husk å sett riktig topic navn"

# ##################################################################################################################


class MyParticipant(quiz_rapid.QuizParticipant):
    def __init__(self):
        super().__init__(TEAM_NAME)
        self.dedup = []
        with open("dedup.txt", "r") as f:
            for line in f:
                self.dedup.append(line)
        with open("saldo.txt", "w") as f:
            f.write("0")

    def handle_question(self, question: quiz_rapid.Question):
        if question.category == "team-registration":
            self.handle_register_team(question)
        if question.category == "arithmetic":
            self.handle_arithmetic(question)
        if question.category == "ping-pong":
            self.handle_ping(question)
        if question.category == "NAV":
            self.handle_nav(question)
        if question.category == "base64":
            self.handle_base64(question)
        if question.category == "is-a-prime":
            self.handle_prime(question)
        if question.category == "deduplication":
            self.handle_deduplication(question)
        if question.category == "transactions":
            self.handle_transaction(question)
        if question.category == "grunnbelop":
            self.handle_grunn(question)

    def handle_assessment(self, assessment: quiz_rapid.Assessment):
        pass

# Question handlers ################################################################################################

    def handle_register_team(self, question: quiz_rapid.Question):
        if question.question == "Register a new team":
            self.publish_answer(
                question_id=question.messageId,
                category=question.category,
                answer=TEAM_NAME
            )

        

    def handle_arithmetic(self, question: quiz_rapid.Question):
        a, operator, b = question.question.split(" ")
        a=int(a)
        b=int(b)
        if operator == "+":
            self.publish_answer(
                question_id=question.messageId,
                category=question.category,
                answer=a + b
            )
        if operator == "-":
            self.publish_answer(
                question_id=question.messageId,
                category=question.category,
                answer=a - b
            )
        if operator == "*":
            self.publish_answer(
                question_id=question.messageId,
                category=question.category,
                answer=a * b
            )
        if operator == "/":
            self.publish_answer(
                question_id=question.messageId,
                category=question.category,
                answer=int(a / b)
            )
    
    def handle_ping(self, question: quiz_rapid.Question):
        if question.question == "ping":
            self.publish_answer(
                question_id=question.messageId,
                category=question.category,
                answer="pong"
            )
        if question.question == "pong":
            self.publish_answer(
                question_id=question.messageId,
                category=question.category,
                answer="ping"
            )

    def handle_nav(self, question: quiz_rapid.Question):
        if question.question == "P\u00e5 hvilken nettside finner man informasjon om rekruttering til NAV IT?":
            self.publish_answer(
                question_id=question.messageId,
                category=question.category,
                answer="detsombetyrnoe.no"
            )
        if question.question == "Hva heter applikasjonsplattformen til NAV?":
            self.publish_answer(
                question_id=question.messageId,
                category=question.category,
                answer="NAIS"
            )

    def handle_base64(self, question: quiz_rapid.Question):
        value = question.question[5:]
        self.publish_answer(
                question_id=question.messageId,
                category=question.category,
                answer=base64.b64decode(value).decode('ascii')
            )
    
    def handle_prime(self, question: quiz_rapid.Question):
        ans = True
        n = int(question.question.split(" ")[-1])

        for i in range(2, n):
            if (n % i) == 0:
                ans = False
                break
        self.publish_answer(
            question_id=question.messageId,
            category=question.category,
            answer=ans
        )

    def handle_deduplication(self, question: quiz_rapid.Question):
        if question.question not in self.dedup:
            self.dedup.append(question.question)
            with open("dedup.txt", "a") as f:
                f.write(question.question + "\n")
            self.publish_answer(
            question_id=question.messageId,
            category=question.category,
            answer="you wont dupe me!"
            )
        """self.publish_answer(
            question_id=question.messageId,
            category=question.category,
            answer="you duped me!"
            )"""

    def handle_transaction(self, question: quiz_rapid.Question):
        action, value = question.question.split(" ")
        value = int(value)
        saldo = 0
        with open("saldo.txt", "r") as f:
            saldo = int(f.read())
        if (action == "UTTREKK"):
            saldo -= value
        else:
            saldo += value
        with open("saldo.txt", "w") as f:
            f.write(str(saldo))
        self.publish_answer(
            question_id=question.messageId,
            category=question.category,
            answer=saldo
            )

    def handle_grunn(self, question: quiz_rapid.Question):
        dato = question.question.split(" ")[-1]
        req = requests.get("http://g.nav.no/api/v1/grunnbeløp?name={}".format(dato))
        data = req.json()
        self.publish_answer(
            question_id=question.messageId,
            category=question.category,
            answer=str(data["grunnbeløp"])
            )
         

        
#####################################################################################################################


def main():
    rapid = quiz_rapid.QuizRapid(
        team_name=TEAM_NAME,
        topic=QUIZ_TOPIC,
        bootstrap_servers=HOSTED_KAFKA,
        consumer_group_id=CONSUMER_GROUP_ID,
        auto_commit=False,     # Bare sku på denne om du vet hva du driver med :)
        logg_questions=True,   # Logg spørsmålene appen mottar
        logg_answers=True,     # Logg svarene appen sender
        short_log_line=False,  # Logg bare en forkortet versjon av meldingene
        log_ignore_list=["arithmetic", "team-registration", "ping-pong", "base64", "is-a-prime", "deduplication"]     # Liste med spørsmålskategorier loggingen skal ignorere
    )
    return MyParticipant(), rapid