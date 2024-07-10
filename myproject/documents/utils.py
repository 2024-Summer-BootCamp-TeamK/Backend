import secrets
import string

PASSWORD_LENGTH = 6

def generate_password():
    # 각 종류의 문자를 최소 하나씩 포함
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]

    # 나머지 길이만큼 무작위로 추가
    all_characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
    password += [secrets.choice(all_characters) for _ in range(PASSWORD_LENGTH - 3)]

    # 리스트를 셔플하여 비밀번호 생성
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)