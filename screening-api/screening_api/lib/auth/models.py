from collections import namedtuple


User = namedtuple(
    'User',
    [
        'user_id', 'first_name', 'last_name', 'email', 'account_id',
        'account_name', 'account_descendants', 'role', 'exp', 'iss',
    ],
)
