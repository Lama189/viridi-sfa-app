
class UserNotFoundError(Exception):
    pass

class UserAlreadyExistsError(Exception):
    pass

class InvalidPasswordError(Exception):
    pass

class UserNotActiveError(Exception):
    pass

class InvalidInviteCodeError(Exception):
    pass

class MembershipNotFoundError(Exception):
    pass

class MembershipAlreadyExistsError(Exception):
    pass